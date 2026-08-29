use std::collections::BTreeMap;
use std::fs;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use base64::Engine as _;
use base64::engine::general_purpose::STANDARD as BASE64;
use ureq::tls::{Certificate, PemItem, RootCerts, TlsConfig, parse_pem};
use ureq::{Agent, Proxy, ProxyProtocol};

use crate::config::TlsMode;
use crate::error::{Error, Result};
use crate::logging::Logger;

pub const USER_AGENT: &str = concat!(
    "DDNS-Rust/",
    env!("CARGO_PKG_VERSION"),
    " (ddns@newfuture.cc)"
);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Method {
    Get,
    Post,
    Put,
    Delete,
}

impl Method {
    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::Get => "GET",
            Self::Post => "POST",
            Self::Put => "PUT",
            Self::Delete => "DELETE",
        }
    }
}

#[derive(Clone, Debug)]
pub struct HttpRequest {
    pub method: Method,
    pub url: String,
    pub headers: BTreeMap<String, String>,
    pub body: Option<String>,
    pub proxies: Vec<String>,
    pub timeout: Duration,
    pub retries: u32,
}

impl HttpRequest {
    pub fn get(url: impl Into<String>, proxies: Vec<String>) -> Self {
        Self {
            method: Method::Get,
            url: url.into(),
            headers: BTreeMap::new(),
            body: None,
            proxies,
            timeout: Duration::from_secs(60),
            retries: 2,
        }
    }
}

#[derive(Debug)]
pub struct HttpResponse {
    pub status: u16,
    pub reason: String,
    pub body: String,
}

pub trait HttpClient {
    fn execute(&self, request: &HttpRequest) -> Result<HttpResponse>;
}

pub struct UreqClient {
    logger: Logger,
    tls: TlsMode,
    sleeper: fn(Duration),
}

impl UreqClient {
    pub const fn new(logger: Logger, tls: TlsMode) -> Self {
        Self {
            logger,
            tls,
            sleeper: thread::sleep,
        }
    }

    #[cfg(test)]
    fn with_sleeper(logger: Logger, tls: TlsMode, sleeper: fn(Duration)) -> Self {
        Self {
            logger,
            tls,
            sleeper,
        }
    }

    fn execute_with_proxy(
        &self,
        request: &HttpRequest,
        proxy: Option<Proxy>,
        insecure: bool,
    ) -> std::result::Result<HttpResponse, ureq::Error> {
        let agent = build_agent(request, &self.tls, proxy, insecure).map_err(|error| {
            ureq::Error::Other(Box::new(std::io::Error::other(error.to_string())))
        })?;
        let (url, basic_auth) = embedded_basic_auth(&request.url);
        let mut builder = ureq::http::Request::builder()
            .method(request.method.as_str())
            .uri(url);
        for (name, value) in &request.headers {
            builder = builder.header(name, value);
        }
        if let Some(authorization) = basic_auth
            && !request
                .headers
                .keys()
                .any(|name| name.eq_ignore_ascii_case("authorization"))
        {
            builder = builder.header("authorization", authorization);
        }
        if !request
            .headers
            .keys()
            .any(|name| name.eq_ignore_ascii_case("user-agent"))
        {
            builder = builder.header("user-agent", USER_AGENT);
        }
        let request = builder
            .body(request.body.as_deref().unwrap_or_default())
            .map_err(ureq::Error::Http)?;
        let mut response = agent.run(request)?;
        let status = response.status().as_u16();
        let reason = response
            .status()
            .canonical_reason()
            .unwrap_or_default()
            .to_owned();
        let body = response.body_mut().read_to_string()?;
        Ok(HttpResponse {
            status,
            reason,
            body,
        })
    }

    fn run_policy(
        &self,
        request: &HttpRequest,
        proxy: Option<Proxy>,
        insecure: bool,
    ) -> std::result::Result<HttpResponse, ureq::Error> {
        let mut retries = 0;
        loop {
            match self.execute_with_proxy(request, proxy.clone(), insecure) {
                Ok(response)
                    if is_retryable_status(response.status)
                        && matches!(request.method, Method::Get | Method::Delete)
                        && retries < request.retries =>
                {
                    retries += 1;
                    let delay = Duration::from_secs(2_u64.saturating_pow(retries));
                    self.logger.warning(
                        "http",
                        format!(
                            "HTTP {} from {}, retrying in {} seconds",
                            response.status,
                            self.logger.mask(&redact_url(&request.url)),
                            delay.as_secs()
                        ),
                    );
                    (self.sleeper)(delay);
                }
                Ok(response) => return Ok(response),
                Err(error)
                    if is_retryable_for_method(&error, request.method)
                        && retries < request.retries =>
                {
                    retries += 1;
                    let delay = Duration::from_secs(2_u64.saturating_pow(retries));
                    self.logger.warning(
                        "http",
                        format!(
                            "request to {} failed: {}; retrying in {} seconds",
                            self.logger.mask(&redact_url(&request.url)),
                            safe_transport_error(&error),
                            delay.as_secs()
                        ),
                    );
                    (self.sleeper)(delay);
                }
                Err(error) => return Err(error),
            }
        }
    }
}

impl HttpClient for UreqClient {
    fn execute(&self, request: &HttpRequest) -> Result<HttpResponse> {
        let proxy_values = if request.proxies.is_empty() {
            vec![None]
        } else {
            request.proxies.iter().map(Some).collect()
        };
        let mut last_error = None;
        let mut last_config_error = None;
        let mut attempted_route = false;
        for proxy_value in proxy_values {
            let proxy = match proxy_value {
                None => system_proxy_setting(),
                Some(value) => proxy_setting(value),
            };
            let proxy = match proxy {
                Ok(proxy) => proxy,
                Err(error) => {
                    let message = error.to_string();
                    self.logger.warning("http", &message);
                    last_config_error = Some(error);
                    continue;
                }
            };
            attempted_route = true;
            self.logger.info(
                "http",
                format!(
                    "{} {}",
                    request.method.as_str(),
                    self.logger.mask(&redact_url(&request.url))
                ),
            );
            match self.run_policy(
                request,
                proxy.clone(),
                matches!(self.tls, TlsMode::Insecure),
            ) {
                Ok(response) => return Ok(response),
                Err(error) if matches!(self.tls, TlsMode::Auto) && is_certificate_error(&error) => {
                    self.logger.warning(
                        "http",
                        "TLS certificate validation failed in ssl=auto mode; retrying once without certificate verification. This connection is vulnerable to interception.",
                    );
                    match self.run_policy(request, proxy, true) {
                        Ok(response) => return Ok(response),
                        Err(error) => last_error = Some(safe_transport_error(&error)),
                    }
                }
                Err(error) => last_error = Some(safe_transport_error(&error)),
            }
        }
        if !attempted_route {
            return Err(last_config_error.unwrap_or_else(|| {
                Error::Config("no valid proxy route was configured".to_owned())
            }));
        }
        Err(Error::Http(format!(
            "request to {} failed: {}",
            self.logger.mask(&redact_url(&request.url)),
            last_error.unwrap_or_else(|| "no proxy route was attempted".to_owned())
        )))
    }
}

fn build_agent(
    request: &HttpRequest,
    tls: &TlsMode,
    proxy: Option<Proxy>,
    insecure: bool,
) -> Result<Agent> {
    let root_certs = match tls {
        TlsMode::CustomCa(path) => {
            let pem = fs::read(path).map_err(|error| {
                Error::Http(format!(
                    "failed to read custom CA `{}`: {error}",
                    path.display()
                ))
            })?;
            let mut certificates = Vec::new();
            for item in parse_pem(&pem) {
                if let PemItem::Certificate(certificate) =
                    item.map_err(|error| Error::Http(format!("invalid CA PEM: {error}")))?
                {
                    certificates.push(certificate);
                }
            }
            if certificates.is_empty() {
                certificates.push(Certificate::from_der(&pem).to_owned());
            }
            RootCerts::Specific(Arc::new(certificates))
        }
        TlsMode::Auto | TlsMode::Verify | TlsMode::Insecure => RootCerts::PlatformVerifier,
    };
    let tls_config = TlsConfig::builder()
        .root_certs(root_certs)
        .disable_verification(insecure)
        .build();
    let config = Agent::config_builder()
        .http_status_as_error(false)
        .timeout_global(Some(request.timeout))
        .tls_config(tls_config)
        .proxy(proxy)
        .user_agent(USER_AGENT)
        .build();
    Ok(Agent::new_with_config(config))
}

fn proxy_setting(value: &str) -> Result<Option<Proxy>> {
    match value.to_ascii_uppercase().as_str() {
        "DIRECT" => Ok(None),
        "SYSTEM" | "DEFAULT" => system_proxy_setting(),
        _ => {
            let normalized = if value.contains("://") {
                value.to_owned()
            } else {
                format!("http://{value}")
            };
            let scheme = normalized
                .split_once("://")
                .map(|(scheme, _)| scheme.to_ascii_lowercase())
                .unwrap_or_default();
            if !matches!(scheme.as_str(), "http" | "https") {
                return Err(Error::Config(format!(
                    "unsupported proxy scheme `{scheme}`; only HTTP and HTTPS proxies are supported"
                )));
            }
            Proxy::new(&normalized)
                .map_err(|_| Error::Config("invalid proxy configuration".to_owned()))
                .and_then(|proxy| validate_proxy(proxy).map(Some))
        }
    }
}

fn system_proxy_setting() -> Result<Option<Proxy>> {
    Proxy::try_from_env().map(validate_proxy).transpose()
}

fn validate_proxy(proxy: Proxy) -> Result<Proxy> {
    match proxy.protocol() {
        ProxyProtocol::Http | ProxyProtocol::Https => Ok(proxy),
        _ => Err(Error::Config(
            "unsupported proxy protocol; only HTTP and HTTPS proxies are supported".to_owned(),
        )),
    }
}

fn is_retryable_status(status: u16) -> bool {
    matches!(status, 408 | 429 | 500 | 502 | 503 | 504)
}

fn safe_transport_error(error: &ureq::Error) -> String {
    match error {
        ureq::Error::ConnectProxyFailed(_) => "proxy connection failed".to_owned(),
        ureq::Error::InvalidProxyUrl => "invalid proxy URL".to_owned(),
        _ => error.to_string(),
    }
}

fn is_retryable_for_method(error: &ureq::Error, method: Method) -> bool {
    matches!(
        error,
        ureq::Error::HostNotFound
            | ureq::Error::ConnectionFailed
            | ureq::Error::ConnectProxyFailed(_)
    ) || (matches!(method, Method::Get | Method::Delete)
        && matches!(error, ureq::Error::Io(_) | ureq::Error::Timeout(_)))
}

fn is_certificate_error(error: &ureq::Error) -> bool {
    if !matches!(
        error,
        ureq::Error::Tls(_) | ureq::Error::Rustls(_) | ureq::Error::Pem(_)
    ) {
        return false;
    }
    let message = error.to_string().to_ascii_lowercase();
    [
        "unknownissuer",
        "unknown issuer",
        "local issuer",
        "unknown ca",
        "basic constraints",
        "causedasendentity",
    ]
    .iter()
    .any(|fragment| message.contains(fragment))
}

pub fn percent_encode(value: &str) -> String {
    let mut output = String::new();
    for byte in value.bytes() {
        if byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'.' | b'_' | b'~') {
            output.push(char::from(byte));
        } else {
            output.push('%');
            output.push(hex_digit(byte >> 4));
            output.push(hex_digit(byte & 0x0f));
        }
    }
    output
}

pub fn redact_url(url: &str) -> String {
    let (prefix, remainder) = if let Some((scheme, remainder)) = url.split_once("://") {
        (format!("{scheme}://"), remainder)
    } else {
        (String::new(), url)
    };
    let authority_end = remainder.find(['/', '?', '#']).unwrap_or(remainder.len());
    let authority = &remainder[..authority_end];
    let authority = authority
        .rsplit_once('@')
        .map_or_else(|| authority.to_owned(), |(_, host)| format!("***@{host}"));
    let suffix = &remainder[authority_end..];
    let (suffix, fragment) = suffix
        .split_once('#')
        .map_or((suffix, false), |(value, _)| (value, true));
    let (path, query) = suffix
        .split_once('?')
        .map_or((suffix, None), |(path, query)| (path, Some(query)));
    let query = query.map(|query| {
        query
            .split('&')
            .map(|parameter| {
                parameter
                    .split_once('=')
                    .map_or_else(|| "***".to_owned(), |(name, _)| format!("{name}=***"))
            })
            .collect::<Vec<_>>()
            .join("&")
    });
    format!(
        "{prefix}{authority}{path}{}{}",
        query.map_or_else(String::new, |query| format!("?{query}")),
        if fragment { "#***" } else { "" }
    )
}

fn embedded_basic_auth(url: &str) -> (String, Option<String>) {
    let Some((scheme, remainder)) = url.split_once("://") else {
        return (url.to_owned(), None);
    };
    let authority_end = remainder.find(['/', '?', '#']).unwrap_or(remainder.len());
    let authority = &remainder[..authority_end];
    let Some((userinfo, host)) = authority.rsplit_once('@') else {
        return (url.to_owned(), None);
    };
    let Some((username, password)) = userinfo.split_once(':') else {
        return (url.to_owned(), None);
    };
    let mut credentials = percent_decode_bytes(username);
    credentials.push(b':');
    credentials.extend(percent_decode_bytes(password));
    (
        format!("{scheme}://{host}{}", &remainder[authority_end..]),
        Some(format!("Basic {}", BASE64.encode(credentials))),
    )
}

fn percent_decode_bytes(value: &str) -> Vec<u8> {
    let bytes = value.as_bytes();
    let mut decoded = Vec::with_capacity(bytes.len());
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'%'
            && index + 2 < bytes.len()
            && let (Some(high), Some(low)) =
                (hex_value(bytes[index + 1]), hex_value(bytes[index + 2]))
        {
            decoded.push((high << 4) | low);
            index += 3;
            continue;
        }
        decoded.push(bytes[index]);
        index += 1;
    }
    decoded
}

pub fn form_encode(parameters: &BTreeMap<String, String>) -> String {
    parameters
        .iter()
        .map(|(key, value)| format!("{}={}", form_component(key), form_component(value)))
        .collect::<Vec<_>>()
        .join("&")
}

pub fn append_query(url: &str, parameters: &BTreeMap<String, String>) -> String {
    if parameters.is_empty() {
        return url.to_owned();
    }
    let separator = if url.contains('?') { '&' } else { '?' };
    format!("{url}{separator}{}", form_encode(parameters))
}

fn form_component(value: &str) -> String {
    percent_encode(value).replace("%20", "+")
}

const fn hex_digit(value: u8) -> char {
    match value {
        0..=9 => (b'0' + value) as char,
        _ => (b'A' + value - 10) as char,
    }
}

const fn hex_value(value: u8) -> Option<u8> {
    match value {
        b'0'..=b'9' => Some(value - b'0'),
        b'a'..=b'f' => Some(value - b'a' + 10),
        b'A'..=b'F' => Some(value - b'A' + 10),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::path::Path;
    use std::thread;
    use std::time::Duration;

    use crate::config::TlsMode;
    use crate::logging::{Level, Logger};

    use super::{
        HttpClient, HttpRequest, Method, UreqClient, embedded_basic_auth, form_encode,
        is_certificate_error, is_retryable_for_method, is_retryable_status, percent_encode,
        proxy_setting, redact_url, safe_transport_error,
    };

    #[test]
    fn percent_encodes_rfc3986_values() {
        assert_eq!(percent_encode("a b/中文"), "a%20b%2F%E4%B8%AD%E6%96%87");
        assert_eq!(
            form_encode(&BTreeMap::from([("name".to_owned(), "a b".to_owned())])),
            "name=a+b"
        );
        assert_eq!(
            redact_url("https://user:password@example.com/config?api_key=secret&flag#private"),
            "https://***@example.com/config?api_key=***&***#***"
        );
        assert_eq!(
            embedded_basic_auth("https://us%65r:p%40ss@example.com/config?key=value"),
            (
                "https://example.com/config?key=value".to_owned(),
                Some("Basic dXNlcjpwQHNz".to_owned())
            )
        );
    }

    #[test]
    fn classifies_retryable_statuses() {
        assert!(is_retryable_status(429));
        assert!(is_retryable_status(503));
        assert!(!is_retryable_status(400));
        assert!(is_retryable_for_method(
            &ureq::Error::ConnectionFailed,
            Method::Post
        ));
        assert!(!is_retryable_for_method(
            &ureq::Error::Io(std::io::Error::other("after send")),
            Method::Post
        ));
    }

    #[test]
    fn constructs_client_with_test_sleeper() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let _client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
    }

    #[test]
    fn performs_real_local_request_and_retries_get_status() {
        let (url, server) = local_server(&[(503, "retry"), (200, "ok")]);
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let mut request = HttpRequest::get(url, vec!["DIRECT".to_owned()]);
        request.retries = 1;
        let response = client.execute(&request).unwrap();
        assert_eq!(response.status, 200);
        assert_eq!(response.body, "ok");
        server.join().unwrap();
    }

    #[test]
    fn sends_embedded_url_credentials_as_basic_auth() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let server = thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            stream
                .set_read_timeout(Some(Duration::from_secs(2)))
                .unwrap();
            let mut buffer = [0_u8; 4096];
            let count = stream.read(&mut buffer).unwrap();
            let request = String::from_utf8_lossy(&buffer[..count]);
            assert!(request.starts_with("GET /secure HTTP/1.1\r\n"));
            assert!(
                request
                    .to_ascii_lowercase()
                    .contains("\r\nauthorization: basic dxnlcjpwqhnz\r\n")
            );
            stream
                .write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")
                .unwrap();
        });
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let request = HttpRequest::get(
            format!("http://us%65r:p%40ss@{address}/secure"),
            vec!["DIRECT".to_owned()],
        );
        let response = client.execute(&request).unwrap();
        assert_eq!(response.body, "ok");
        server.join().unwrap();
    }

    #[test]
    fn does_not_retry_post_after_http_response() {
        let (url, server) = local_server(&[(503, "not retried")]);
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let request = HttpRequest {
            method: Method::Post,
            url,
            headers: BTreeMap::new(),
            body: Some("value".to_owned()),
            proxies: vec!["DIRECT".to_owned()],
            timeout: Duration::from_secs(5),
            retries: 3,
        };
        let response = client.execute(&request).unwrap();
        assert_eq!(response.status, 503);
        server.join().unwrap();
    }

    #[test]
    fn classifies_only_certificate_tls_errors_for_auto_mode() {
        assert!(is_certificate_error(&ureq::Error::Tls(
            "invalid peer certificate: UnknownIssuer"
        )));
        assert!(!is_certificate_error(&ureq::Error::Tls(
            "invalid peer certificate: expired"
        )));
        assert!(!is_certificate_error(&ureq::Error::ConnectionFailed));
    }

    #[test]
    fn falls_back_to_direct_after_proxy_failure() {
        let unavailable = TcpListener::bind("127.0.0.1:0").unwrap();
        let unavailable_address = unavailable.local_addr().unwrap();
        drop(unavailable);
        let (url, server) = local_server(&[(200, "direct")]);
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let mut request = HttpRequest::get(
            url,
            vec![format!("http://{unavailable_address}"), "DIRECT".to_owned()],
        );
        request.retries = 0;
        let response = client.execute(&request).unwrap();
        assert_eq!(response.body, "direct");
        server.join().unwrap();
    }

    #[test]
    fn valid_route_is_not_blocked_by_malformed_backup_proxy() {
        let (url, server) = local_server(&[(200, "direct")]);
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let mut request = HttpRequest::get(
            url,
            vec![
                "DIRECT".to_owned(),
                "http://user:backup-password@[".to_owned(),
            ],
        );
        request.retries = 0;
        let response = client.execute(&request).unwrap();
        assert_eq!(response.body, "direct");
        server.join().unwrap();
    }

    #[test]
    fn rejects_unsupported_or_malformed_proxies_without_leaking_credentials() {
        for proxy in [
            "socks5://user:socks-password@127.0.0.1:1080",
            "http://user:http-password@[",
            "http://user:delimiter-password bad/path@proxy.example",
        ] {
            let error = proxy_setting(proxy).unwrap_err().to_string();
            assert!(!error.contains("socks-password"));
            assert!(!error.contains("http-password"));
            assert!(!error.contains("delimiter-password"));
            assert!(error.contains("proxy"));
        }
        assert_eq!(
            safe_transport_error(&ureq::Error::ConnectProxyFailed(
                "http://user:transport-password@proxy.example".to_owned()
            )),
            "proxy connection failed"
        );

        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let client = UreqClient::with_sleeper(logger, TlsMode::Verify, |_| {});
        let request = HttpRequest::get(
            "http://127.0.0.1/",
            vec!["socks5://user:password@127.0.0.1:1080".to_owned()],
        );
        assert!(matches!(
            client.execute(&request),
            Err(crate::error::Error::Config(_))
        ));
    }

    fn local_server(responses: &[(u16, &str)]) -> (String, thread::JoinHandle<()>) {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let address = listener.local_addr().unwrap();
        let responses = responses
            .iter()
            .map(|(status, body)| (*status, (*body).to_owned()))
            .collect::<Vec<_>>();
        let server = thread::spawn(move || {
            for (status, body) in responses {
                let (mut stream, _) = listener.accept().unwrap();
                stream
                    .set_read_timeout(Some(Duration::from_secs(2)))
                    .unwrap();
                let mut request = Vec::new();
                let mut buffer = [0_u8; 4096];
                loop {
                    let count = stream.read(&mut buffer).unwrap_or_default();
                    if count == 0 {
                        break;
                    }
                    request.extend_from_slice(&buffer[..count]);
                    let Some(header_end) =
                        request.windows(4).position(|window| window == b"\r\n\r\n")
                    else {
                        continue;
                    };
                    let headers = String::from_utf8_lossy(&request[..header_end]);
                    let content_length = headers
                        .lines()
                        .find_map(|line| {
                            let (name, value) = line.split_once(':')?;
                            name.eq_ignore_ascii_case("content-length")
                                .then(|| value.trim().parse::<usize>().ok())
                                .flatten()
                        })
                        .unwrap_or_default();
                    if request.len() >= header_end + 4 + content_length {
                        break;
                    }
                }
                let reason = if status == 200 {
                    "OK"
                } else {
                    "Service Unavailable"
                };
                let response = format!(
                    "HTTP/1.1 {status} {reason}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
                    body.len()
                );
                stream.write_all(response.as_bytes()).unwrap();
            }
        });
        (format!("http://{address}/test"), server)
    }
}

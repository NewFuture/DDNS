use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr, UdpSocket};
use std::process::Command;
use std::str::FromStr;

use regex::Regex;

use crate::config::{AddressRules, TlsMode};
use crate::error::{Error, Result};
use crate::http::{HttpClient, HttpRequest, redact_url};
use crate::logging::Logger;

const PUBLIC_IPV4_APIS: &[&str] = &[
    "https://api.ipify.org",
    "https://ipv4.ddnsip.cn",
    "https://ipinfo.io/ip",
    "https://api-ipv4.ip.sb/ip",
    "http://checkip.amazonaws.com",
];
const PUBLIC_IPV6_APIS: &[&str] = &[
    "https://api6.ipify.org/",
    "https://ipv6.ddnsip.cn",
    "https://api-ipv6.ip.sb/ip",
    "http://ipv6.icanhazip.com",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AddressFamily {
    V4,
    V6,
}

impl AddressFamily {
    pub const fn record_type(self) -> &'static str {
        match self {
            Self::V4 => "A",
            Self::V6 => "AAAA",
        }
    }

    const fn label(self) -> &'static str {
        match self {
            Self::V4 => "IPv4",
            Self::V6 => "IPv6",
        }
    }

    const fn matches(self, address: IpAddr) -> bool {
        matches!(
            (self, address),
            (Self::V4, IpAddr::V4(_)) | (Self::V6, IpAddr::V6(_))
        )
    }
}

pub fn resolve(
    family: AddressFamily,
    rules: &AddressRules,
    tls: &TlsMode,
    client: &dyn HttpClient,
    logger: &Logger,
) -> Result<Option<IpAddr>> {
    let AddressRules::Rules(rules) = rules else {
        return Ok(None);
    };
    let mut failures = Vec::new();
    for rule in rules {
        let displayed_rule = display_rule(rule);
        logger.debug(
            "ip",
            format!("trying {} rule `{displayed_rule}`", family.label()),
        );
        match resolve_rule(family, rule, tls, client) {
            Ok(address) => {
                logger.info("ip", format!("resolved {} as {address}", family.label()));
                return Ok(Some(address));
            }
            Err(error) => {
                logger.warning("ip", format!("rule `{displayed_rule}` failed: {error}"));
                failures.push(format!("{displayed_rule}: {error}"));
            }
        }
    }
    Err(Error::Ip(format!(
        "all {} rules failed: {}",
        family.label(),
        failures.join("; ")
    )))
}

fn display_rule(rule: &str) -> String {
    if let Some(url) = rule.strip_prefix("url:") {
        format!("url:{}", redact_url(url))
    } else if rule.starts_with("cmd:") {
        "cmd:<redacted>".to_owned()
    } else if rule.starts_with("shell:") {
        "shell:<redacted>".to_owned()
    } else {
        rule.to_owned()
    }
}

fn resolve_rule(
    family: AddressFamily,
    rule: &str,
    tls: &TlsMode,
    client: &dyn HttpClient,
) -> Result<IpAddr> {
    if let Ok(index) = rule.parse::<usize>() {
        return local_address(family, index);
    }
    if let Some(url) = rule.strip_prefix("url:") {
        return fetch_address(family, url, tls, client);
    }
    if let Some(pattern) = rule.strip_prefix("regex:") {
        return regex_address(family, pattern);
    }
    if let Some(command) = rule.strip_prefix("cmd:") {
        return command_address(family, command, false);
    }
    if let Some(command) = rule.strip_prefix("shell:") {
        return command_address(family, command, true);
    }
    match rule {
        "default" => default_address(family),
        "public" => public_address(family, tls, client),
        "local" => local_address(family, 0),
        _ => Err(Error::Ip("unknown address rule".to_owned())),
    }
}

fn default_address(family: AddressFamily) -> Result<IpAddr> {
    let (bind, remote) = match family {
        AddressFamily::V4 => (
            SocketAddr::new(IpAddr::V4(Ipv4Addr::UNSPECIFIED), 0),
            SocketAddr::new(IpAddr::V4(Ipv4Addr::new(1, 1, 1, 1)), 53),
        ),
        AddressFamily::V6 => (
            SocketAddr::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), 0),
            SocketAddr::new(
                IpAddr::V6(Ipv6Addr::from_str("2606:4700:4700::1111").expect("valid constant")),
                53,
            ),
        ),
    };
    let socket = UdpSocket::bind(bind)?;
    socket.connect(remote)?;
    let address = socket.local_addr()?.ip();
    validate_family(family, address)
}

fn local_address(family: AddressFamily, index: usize) -> Result<IpAddr> {
    let addresses = if_addrs::get_if_addrs()?
        .into_iter()
        .map(|interface| interface.ip())
        .filter(|address| family.matches(*address))
        .collect::<Vec<_>>();
    addresses.get(index).copied().ok_or_else(|| {
        Error::Ip(format!(
            "{} interface index {index} is unavailable ({} matching addresses)",
            family.label(),
            addresses.len()
        ))
    })
}

fn public_address(family: AddressFamily, tls: &TlsMode, client: &dyn HttpClient) -> Result<IpAddr> {
    let mut failures = Vec::new();
    let endpoints = match family {
        AddressFamily::V4 => PUBLIC_IPV4_APIS,
        AddressFamily::V6 => PUBLIC_IPV6_APIS,
    };
    for endpoint in endpoints {
        match fetch_address(family, endpoint, tls, client) {
            Ok(address) => return Ok(address),
            Err(error) => failures.push(format!("{endpoint}: {error}")),
        }
    }
    Err(Error::Ip(failures.join("; ")))
}

fn fetch_address(
    family: AddressFamily,
    url: &str,
    tls: &TlsMode,
    client: &dyn HttpClient,
) -> Result<IpAddr> {
    let mut request = HttpRequest::get(url, tls.clone(), Vec::new());
    request.retries = 2;
    let response = client.execute(&request)?;
    if !(200..300).contains(&response.status) {
        return Err(Error::Ip(format!(
            "HTTP {} {}",
            response.status, response.reason
        )));
    }
    extract_address(family, &response.body)
}

fn regex_address(family: AddressFamily, pattern: &str) -> Result<IpAddr> {
    let output = network_configuration()?;
    regex_address_in_text(family, pattern, &output)
}

fn regex_address_in_text(family: AddressFamily, pattern: &str, output: &str) -> Result<IpAddr> {
    let matcher =
        Regex::new(pattern).map_err(|error| Error::Ip(format!("invalid regex: {error}")))?;
    for address in addresses_in_text(family, output) {
        if matcher.is_match(&address.to_string()) {
            return Ok(address);
        }
    }
    Err(Error::Ip("no local address matched the regex".to_owned()))
}

fn command_address(family: AddressFamily, command: &str, shell: bool) -> Result<IpAddr> {
    let output = if shell {
        shell_command(command)?
    } else {
        direct_command(command)?
    };
    extract_address(family, &output)
}

fn direct_command(command: &str) -> Result<String> {
    let arguments = split_command(command)?;
    let (program, arguments) = arguments
        .split_first()
        .ok_or_else(|| Error::Ip("cmd rule is empty".to_owned()))?;
    let output = Command::new(program).args(arguments).output()?;
    command_output(output, command)
}

#[cfg(windows)]
fn shell_command(command: &str) -> Result<String> {
    command_output(Command::new("cmd").args(["/C", command]).output()?, command)
}

#[cfg(not(windows))]
fn shell_command(command: &str) -> Result<String> {
    command_output(
        Command::new("/bin/sh").args(["-c", command]).output()?,
        command,
    )
}

fn command_output(output: std::process::Output, _command: &str) -> Result<String> {
    if !output.status.success() {
        return Err(Error::Ip(format!(
            "command exited with {}: {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    String::from_utf8(output.stdout)
        .map_err(|error| Error::Ip(format!("command output is not UTF-8: {error}")))
}

fn network_configuration() -> Result<String> {
    #[cfg(windows)]
    let candidates: &[(&str, &[&str])] = &[("ipconfig", &[])];
    #[cfg(not(windows))]
    let candidates: &[(&str, &[&str])] = &[("ip", &["address"]), ("ifconfig", &[])];

    let mut errors = Vec::new();
    for (program, arguments) in candidates {
        match Command::new(program).args(*arguments).output() {
            Ok(output) if output.status.success() => {
                return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
            }
            Ok(output) => errors.push(format!("{program}: {}", output.status)),
            Err(error) => errors.push(format!("{program}: {error}")),
        }
    }
    Err(Error::Ip(format!(
        "unable to read network configuration: {}",
        errors.join("; ")
    )))
}

fn extract_address(family: AddressFamily, content: &str) -> Result<IpAddr> {
    addresses_in_text(family, content)
        .into_iter()
        .next()
        .ok_or_else(|| Error::Ip(format!("response contains no valid {}", family.label())))
}

fn addresses_in_text(family: AddressFamily, content: &str) -> Vec<IpAddr> {
    content
        .split(|character: char| {
            character.is_whitespace()
                || matches!(
                    character,
                    ',' | ';' | '=' | '[' | ']' | '(' | ')' | '<' | '>' | '"' | '\''
                )
        })
        .filter_map(|token| {
            let token = token
                .trim_matches(|character: char| matches!(character, '/' | '%' | '.'))
                .split('/')
                .next()
                .unwrap_or_default()
                .split('%')
                .next()
                .unwrap_or_default();
            token
                .parse::<IpAddr>()
                .ok()
                .filter(|address| family.matches(*address))
        })
        .collect()
}

fn validate_family(family: AddressFamily, address: IpAddr) -> Result<IpAddr> {
    if family.matches(address) {
        Ok(address)
    } else {
        Err(Error::Ip(format!(
            "{address} is not a valid {} address",
            family.label()
        )))
    }
}

fn split_command(command: &str) -> Result<Vec<String>> {
    let mut arguments = Vec::new();
    let mut current = String::new();
    let mut quote = None;
    let mut escaped = false;
    for character in command.chars() {
        if escaped {
            current.push(character);
            escaped = false;
            continue;
        }
        if character == '\\' && !cfg!(windows) {
            escaped = true;
            continue;
        }
        if let Some(active_quote) = quote {
            if character == active_quote {
                quote = None;
            } else {
                current.push(character);
            }
            continue;
        }
        if matches!(character, '"' | '\'') {
            quote = Some(character);
        } else if character.is_whitespace() {
            if !current.is_empty() {
                arguments.push(std::mem::take(&mut current));
            }
        } else if matches!(character, '|' | ';' | '&' | '>' | '<') {
            return Err(Error::Ip(
                "cmd rules cannot contain shell operators; use shell: explicitly".to_owned(),
            ));
        } else {
            current.push(character);
        }
    }
    if escaped || quote.is_some() {
        return Err(Error::Ip("unterminated cmd quoting".to_owned()));
    }
    if !current.is_empty() {
        arguments.push(current);
    }
    Ok(arguments)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::path::Path;

    use crate::config::{AddressRules, TlsMode};
    use crate::error::Result;
    use crate::http::{HttpClient, HttpRequest, HttpResponse};
    use crate::logging::{Level, Logger};

    use super::{
        AddressFamily, command_address, default_address, extract_address, local_address,
        regex_address_in_text, resolve, split_command,
    };

    struct FakeClient;

    impl HttpClient for FakeClient {
        fn execute(&self, request: &HttpRequest) -> Result<HttpResponse> {
            let body = if request.url.contains("invalid") {
                "address unavailable"
            } else {
                "current address: 192.0.2.44"
            };
            Ok(HttpResponse {
                status: 200,
                reason: "OK".to_owned(),
                headers: BTreeMap::new(),
                body: body.to_owned(),
            })
        }
    }

    #[test]
    fn extracts_only_requested_address_family() {
        let content = "IPv6 2001:db8::1 and IPv4 192.0.2.1";
        assert_eq!(
            extract_address(AddressFamily::V4, content)
                .unwrap()
                .to_string(),
            "192.0.2.1"
        );
        assert_eq!(
            extract_address(AddressFamily::V6, content)
                .unwrap()
                .to_string(),
            "2001:db8::1"
        );
    }

    #[test]
    fn parses_direct_commands_without_shell_operators() {
        assert_eq!(
            split_command(r#"program --name "two words""#).unwrap(),
            vec!["program", "--name", "two words"]
        );
        assert!(split_command("program | other").is_err());

        #[cfg(windows)]
        assert_eq!(
            split_command(r#""C:\Program Files\Tool\tool.exe" --flag"#).unwrap(),
            vec![r"C:\Program Files\Tool\tool.exe", "--flag"]
        );
    }

    #[test]
    fn resolves_url_fallback_and_public_rules() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let address = resolve(
            AddressFamily::V4,
            &AddressRules::Rules(vec![
                "url:http://test/invalid".to_owned(),
                "url:http://test/valid".to_owned(),
            ]),
            &TlsMode::Verify,
            &FakeClient,
            &logger,
        )
        .unwrap();
        assert_eq!(address.unwrap().to_string(), "192.0.2.44");

        let public = resolve(
            AddressFamily::V4,
            &AddressRules::Rules(vec!["public".to_owned()]),
            &TlsMode::Verify,
            &FakeClient,
            &logger,
        )
        .unwrap();
        assert_eq!(public.unwrap().to_string(), "192.0.2.44");
    }

    #[test]
    fn resolves_default_local_regex_and_command_rules() {
        assert!(matches!(
            default_address(AddressFamily::V4).unwrap(),
            std::net::IpAddr::V4(_)
        ));
        assert!(matches!(
            local_address(AddressFamily::V4, 0).unwrap(),
            std::net::IpAddr::V4(_)
        ));
        assert_eq!(
            regex_address_in_text(
                AddressFamily::V4,
                r"192\.168\..*",
                "inet 10.0.0.1/8\ninet 192.168.1.2/24"
            )
            .unwrap()
            .to_string(),
            "192.168.1.2"
        );

        #[cfg(windows)]
        let command = "cmd.exe /C echo 192.0.2.55";
        #[cfg(not(windows))]
        let command = "printf 192.0.2.55";
        assert_eq!(
            command_address(AddressFamily::V4, command, false)
                .unwrap()
                .to_string(),
            "192.0.2.55"
        );
    }
}

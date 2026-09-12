use std::cell::Cell;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use serde_json::{Value, json};

use crate::dashboard::{DashboardError, DashboardService};
use crate::error::{Error, Result};
use crate::http_settings::{
    HttpSettings, host_header_is_loopback, normalize_origin, token_matches,
};

pub(crate) const MAX_BODY_SIZE: usize = 2 * 1024 * 1024;
const MAX_HEADER_SIZE: usize = 64 * 1024;
const CONNECTION_TIMEOUT: Duration = Duration::from_secs(15);
const MAX_CONNECTIONS: usize = 64;

pub(crate) struct Request {
    pub method: String,
    pub path: String,
    headers: Vec<(String, String)>,
    body_read: Cell<bool>,
}

impl Request {
    pub fn header(&self, name: &str) -> Option<&str> {
        self.headers
            .iter()
            .find(|(key, _)| key.eq_ignore_ascii_case(name))
            .map(|(_, value)| value.as_str())
    }

    pub fn header_count(&self, name: &str) -> usize {
        self.headers
            .iter()
            .filter(|(key, _)| key.eq_ignore_ascii_case(name))
            .count()
    }

    pub fn token(&self, allow_dashboard_header: bool) -> Option<&str> {
        let bearer = self.header("authorization").and_then(|value| {
            let (scheme, token) = value.split_once(char::is_whitespace)?;
            scheme.eq_ignore_ascii_case("bearer").then(|| token.trim())
        });
        bearer.or_else(|| {
            allow_dashboard_header
                .then(|| self.header("x-ddns-token"))
                .flatten()
        })
    }

    pub fn origin(&self) -> Option<String> {
        self.header("origin")
            .and_then(|origin| normalize_origin(origin).ok())
    }

    pub fn origin_allowed(&self, settings: &HttpSettings, cors: bool) -> bool {
        if self.header("origin").is_none() {
            return true;
        }
        let Some(origin) = self.origin() else {
            return false;
        };
        let direct = self
            .header("host")
            .and_then(|host| normalize_origin(&format!("http://{host}")).ok());
        direct.as_ref() == Some(&origin) || (cors && settings.origins.contains(&origin))
    }

    fn read(reader: &mut impl BufRead) -> std::result::Result<Self, Response> {
        let mut remaining = MAX_HEADER_SIZE;
        let line = read_header_line(reader, &mut remaining)?;
        let mut parts = line.split(' ');
        let method = parts.next().unwrap_or_default();
        let target = parts.next().unwrap_or_default();
        let version = parts.next().unwrap_or_default();
        if parts.next().is_some()
            || !["HTTP/1.0", "HTTP/1.1"].contains(&version)
            || method.is_empty()
            || !method.bytes().all(|byte| byte.is_ascii_uppercase())
            || !target.starts_with('/')
            || target.starts_with("//")
            || target.contains('#')
            || target
                .bytes()
                .any(|byte| byte.is_ascii_control() || byte.is_ascii_whitespace())
        {
            return Err(Response::error(
                400,
                "invalid_request",
                "Invalid HTTP request line.",
            ));
        }
        let method = method.to_owned();
        let path = target.split('?').next().unwrap_or(target).to_owned();
        let mut headers = Vec::new();
        loop {
            let line = read_header_line(reader, &mut remaining)?;
            if line.is_empty() {
                break;
            }
            let Some((name, value)) = line.split_once(':') else {
                return Err(Response::error(
                    400,
                    "invalid_request",
                    "Invalid HTTP header.",
                ));
            };
            if name.is_empty()
                || !name
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || b"!#$%&'*+-.^_`|~".contains(&byte))
                || value
                    .bytes()
                    .any(|byte| (byte < 0x20 && byte != b'\t') || byte == 0x7f)
            {
                return Err(Response::error(
                    400,
                    "invalid_request",
                    "Invalid HTTP header.",
                ));
            }
            headers.push((
                name.to_ascii_lowercase(),
                value.trim_matches([' ', '\t']).to_owned(),
            ));
            if headers.len() > 100 {
                return Err(Response::error(
                    431,
                    "headers_too_large",
                    "Too many HTTP headers.",
                ));
            }
        }
        let request = Self {
            method,
            path,
            headers,
            body_read: Cell::new(false),
        };
        for name in [
            "host",
            "content-length",
            "authorization",
            "x-ddns-token",
            "origin",
            "content-type",
            "accept",
        ] {
            if request.header_count(name) > 1 {
                return Err(Response::error(
                    400,
                    "invalid_request",
                    "Repeated HTTP header.",
                ));
            }
        }
        if request.header("transfer-encoding").is_some() {
            return Err(Response::error(
                400,
                "invalid_request",
                "Transfer-Encoding is not supported.",
            ));
        }
        if request.header("expect").is_some() {
            return Err(Response::error(
                417,
                "expectation_failed",
                "Expect is not supported.",
            ));
        }
        Ok(request)
    }

    pub fn read_json(
        &self,
        reader: &mut impl Read,
        mcp: bool,
    ) -> std::result::Result<Value, Response> {
        if !self
            .header("content-type")
            .unwrap_or_default()
            .split(';')
            .next()
            .unwrap_or_default()
            .trim()
            .eq_ignore_ascii_case("application/json")
        {
            return Err(Response::error(
                415,
                "unsupported_media_type",
                "Content-Type must be application/json.",
            ));
        }
        let length = self.header("content-length").ok_or_else(|| {
            Response::error(411, "length_required", "Content-Length is required.")
        })?;
        if length.is_empty() || !length.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err(Response::error(
                400,
                "invalid_length",
                "Content-Length is invalid.",
            ));
        }
        let length = length
            .parse::<usize>()
            .ok()
            .filter(|length| *length <= MAX_BODY_SIZE)
            .ok_or_else(|| {
                Response::error(413, "payload_too_large", "Request body is too large.")
            })?;
        let mut content = vec![0; length];
        self.body_read.set(true);
        reader
            .read_exact(&mut content)
            .map_err(|_| Response::error(400, "invalid_body", "Request body is incomplete."))?;
        let value: Value = serde_json::from_slice(&content).map_err(|_| {
            if mcp {
                Response::json(
                    400,
                    crate::mcp::error_response(Value::Null, -32700, "Parse error"),
                )
            } else {
                Response::error(
                    400,
                    "invalid_json",
                    "Request body must contain valid UTF-8 JSON.",
                )
            }
        })?;
        if !value.is_object() {
            return Err(if mcp {
                Response::json(
                    400,
                    crate::mcp::error_response(Value::Null, -32600, "Invalid Request"),
                )
            } else {
                Response::error(400, "invalid_json", "Request body must be a JSON object.")
            });
        }
        Ok(value)
    }
}

fn read_header_line(
    reader: &mut impl BufRead,
    remaining: &mut usize,
) -> std::result::Result<String, Response> {
    let mut line = Vec::new();
    reader
        .take((*remaining + 1) as u64)
        .read_until(b'\n', &mut line)
        .map_err(|_| Response::error(408, "request_timeout", "HTTP header read failed."))?;
    if line.len() > *remaining {
        return Err(Response::error(
            431,
            "headers_too_large",
            "HTTP headers are too large.",
        ));
    }
    *remaining -= line.len();
    if !line.ends_with(b"\r\n") {
        return Err(Response::error(
            400,
            "invalid_request",
            "HTTP headers require CRLF framing.",
        ));
    }
    line.truncate(line.len() - 2);
    String::from_utf8(line)
        .map_err(|_| Response::error(400, "invalid_request", "Invalid HTTP header encoding."))
}

pub(crate) struct Response {
    pub status: u16,
    pub headers: Vec<(String, String)>,
    pub body: Vec<u8>,
}

impl Response {
    pub fn empty(status: u16) -> Self {
        Self {
            status,
            headers: Vec::new(),
            body: Vec::new(),
        }
    }
    pub fn bytes(status: u16, body: Vec<u8>, content_type: &str) -> Self {
        Self {
            status,
            headers: vec![("Content-Type".to_owned(), content_type.to_owned())],
            body,
        }
    }
    pub fn json(status: u16, value: Value) -> Self {
        Self::bytes(
            status,
            serde_json::to_vec(&value).expect("JSON Value serialization"),
            "application/json; charset=utf-8",
        )
    }
    pub fn error(status: u16, code: &str, message: &str) -> Self {
        Self::json(status, json!({"error":{"code":code,"message":message}}))
    }
    pub fn header(mut self, name: &str, value: &str) -> Self {
        self.headers.push((name.to_owned(), value.to_owned()));
        self
    }
    fn write(&self, stream: &mut impl Write, head: bool) -> std::io::Result<()> {
        let reason = ureq::http::StatusCode::from_u16(self.status)
            .ok()
            .and_then(|status| status.canonical_reason())
            .unwrap_or("Response");
        write!(
            stream,
            "HTTP/1.1 {} {}\r\nContent-Length: {}\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nX-Frame-Options: DENY\r\nCross-Origin-Opener-Policy: same-origin\r\nCross-Origin-Resource-Policy: same-origin\r\nPermissions-Policy: camera=(), geolocation=(), microphone=()\r\nContent-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; object-src 'none'\r\n",
            self.status,
            reason,
            self.body.len()
        )?;
        for (name, value) in &self.headers {
            write!(stream, "{name}: {value}\r\n")?;
        }
        stream.write_all(b"\r\n")?;
        if !head {
            stream.write_all(&self.body)?;
        }
        stream.flush()
    }
}

impl From<DashboardError> for Response {
    fn from(error: DashboardError) -> Self {
        Self::error(error.status, error.code, &error.message)
    }
}

struct ServerState {
    service: Arc<DashboardService>,
    settings: HttpSettings,
    web: bool,
    launch: Mutex<Option<(String, Instant)>>,
}

pub struct HttpServer {
    listener: TcpListener,
    state: Arc<ServerState>,
}

impl HttpServer {
    pub fn bind(service: Arc<DashboardService>, settings: HttpSettings, web: bool) -> Result<Self> {
        // Revalidate public settings so direct callers cannot bypass bind authentication.
        let settings = HttpSettings::from_value(
            &json!({"host":settings.host,"port":settings.port,"token":settings.token,"origins":settings.origins}),
            true,
        )?;
        let listener = TcpListener::bind((settings.host.as_str(), settings.port))?;
        listener.set_nonblocking(true)?;
        Ok(Self {
            listener,
            state: Arc::new(ServerState {
                service,
                settings,
                web,
                launch: Mutex::new(None),
            }),
        })
    }

    pub fn local_addr(&self) -> Result<SocketAddr> {
        Ok(self.listener.local_addr()?)
    }

    pub fn launch_url(&self) -> Result<String> {
        let address = self.local_addr()?;
        let host = match address.ip() {
            std::net::IpAddr::V4(ip) if ip.is_unspecified() => "127.0.0.1".to_owned(),
            std::net::IpAddr::V6(ip) if ip.is_unspecified() => "[::1]".to_owned(),
            std::net::IpAddr::V6(ip) => format!("[{ip}]"),
            ip => ip.to_string(),
        };
        let origin = format!("http://{host}:{}", address.port());
        if !self.state.web {
            return Ok(format!("{origin}/mcp"));
        }
        if self.state.settings.token.is_none() {
            return Ok(format!("{origin}/#view=overview"));
        }
        let mut bytes = [0; 24];
        getrandom::fill(&mut bytes)
            .map_err(|_| Error::Http("Unable to create browser launch token".to_owned()))?;
        let token = bytes
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect::<String>();
        *self
            .state
            .launch
            .lock()
            .map_err(|_| Error::Http("Browser launch state unavailable".to_owned()))? =
            Some((token.clone(), Instant::now()));
        Ok(format!("{origin}/launch/{token}"))
    }

    pub fn serve(&self, stop: &AtomicBool) -> Result<()> {
        let active = Arc::new(AtomicUsize::new(0));
        let mut workers: Vec<thread::JoinHandle<()>> = Vec::new();
        while !stop.load(Ordering::Acquire) {
            match self.listener.accept() {
                Ok((mut stream, _)) => {
                    stream.set_nonblocking(false)?;
                    stream.set_read_timeout(Some(CONNECTION_TIMEOUT))?;
                    stream.set_write_timeout(Some(CONNECTION_TIMEOUT))?;
                    if active.load(Ordering::Acquire) >= MAX_CONNECTIONS {
                        let _ = Response::error(503, "busy", "Too many active connections.")
                            .write(&mut stream, false);
                        continue;
                    }
                    active.fetch_add(1, Ordering::AcqRel);
                    let state = Arc::clone(&self.state);
                    let active = Arc::clone(&active);
                    workers.push(thread::spawn(move || {
                        struct ActiveConnection(Arc<AtomicUsize>);
                        impl Drop for ActiveConnection {
                            fn drop(&mut self) {
                                self.0.fetch_sub(1, Ordering::AcqRel);
                            }
                        }
                        let _active = ActiveConnection(active);
                        handle_connection(stream, &state);
                    }));
                }
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(10))
                }
                Err(error) => return Err(error.into()),
            }
            let mut index = 0;
            while index < workers.len() {
                if workers[index].is_finished() {
                    let _ = workers.swap_remove(index).join();
                } else {
                    index += 1;
                }
            }
        }
        for worker in workers {
            let _ = worker.join();
        }
        Ok(())
    }
}

fn handle_connection(stream: TcpStream, state: &ServerState) {
    let mut reader = BufReader::new(stream);
    let (response, head) = match Request::read(&mut reader) {
        Ok(request) => {
            let head = request.method == "HEAD";
            let response = route(&request, &mut reader, state);
            discard_unread_body(&request, &mut reader);
            (response, head)
        }
        Err(response) => (response, false),
    };
    let _ = response.write(reader.get_mut(), head);
}

fn discard_unread_body(request: &Request, reader: &mut BufReader<TcpStream>) {
    if request.body_read.get() {
        return;
    }
    let Some(mut remaining) = request
        .header("content-length")
        .and_then(|length| length.parse::<usize>().ok())
        .filter(|length| *length <= MAX_BODY_SIZE)
    else {
        return;
    };
    // Unread request bytes can reset early rejection responses on Windows.
    // Bound the entire drain, not each read, so authentication never waits for an unsent body.
    let deadline = Instant::now() + Duration::from_millis(50);
    let mut buffer = [0; 4096];
    while remaining > 0 {
        let timeout = deadline.saturating_duration_since(Instant::now());
        if timeout.is_zero() || reader.get_mut().set_read_timeout(Some(timeout)).is_err() {
            break;
        }
        let count = remaining.min(buffer.len());
        match reader.read(&mut buffer[..count]) {
            Ok(0) | Err(_) => break,
            Ok(count) => remaining -= count,
        }
    }
}

fn route(request: &Request, reader: &mut impl Read, state: &ServerState) -> Response {
    if request.path == "/mcp" {
        return crate::mcp_http::handle(
            request,
            reader,
            &state.settings,
            Arc::clone(&state.service),
        );
    }
    if !state.web {
        return Response::error(404, "not_found", "Resource not found.");
    }
    if state.settings.token.is_none()
        && !host_header_is_loopback(request.header("host").unwrap_or_default())
    {
        return Response::error(
            421,
            "invalid_host",
            "Unauthenticated dashboard only accepts local hosts.",
        );
    }
    if request.method == "GET" || request.method == "HEAD" {
        if let Some(token) = request.path.strip_prefix("/launch/") {
            let consumed = if request.method == "HEAD" {
                false
            } else {
                state
                    .launch
                    .lock()
                    .map(|mut launch| {
                        let valid = launch.as_ref().is_some_and(|(expected, issued)| {
                            issued.elapsed() <= Duration::from_secs(60)
                                && token_matches(Some(token), Some(expected))
                        });
                        if valid {
                            *launch = None;
                        }
                        valid
                    })
                    .unwrap_or(false)
            };
            if !consumed {
                return Response::error(
                    403,
                    "invalid_launch_token",
                    "Dashboard launch token is invalid.",
                );
            }
            let token = state.settings.token.as_deref().unwrap_or_default();
            return Response::empty(302).header(
                "Location",
                &format!(
                    "/#token={}&view=overview",
                    crate::http::percent_encode(token)
                ),
            );
        }
        if let Some((content, content_type)) = asset(&request.path) {
            return Response::bytes(200, content.to_vec(), content_type);
        }
    }
    if !request.path.starts_with("/api/") {
        return Response::error(404, "not_found", "Resource not found.");
    }
    if !token_matches(request.token(true), state.settings.token.as_deref()) {
        return Response::error(403, "invalid_token", "Dashboard request token is invalid.");
    }
    if !request.origin_allowed(&state.settings, false) {
        return Response::error(
            403,
            "invalid_origin",
            "Dashboard request origin is not allowed.",
        );
    }
    let result = match (request.method.as_str(), request.path.as_str()) {
        ("GET" | "HEAD", "/api/dashboard") => state.service.dashboard(),
        ("GET" | "HEAD", "/api/config") => state.service.config_state(),
        ("POST" | "PUT", _) => {
            let payload = match request.read_json(reader, false) {
                Ok(payload) => payload,
                Err(response) => return response,
            };
            match (request.method.as_str(), request.path.as_str()) {
                ("PUT", "/api/config") => state
                    .service
                    .save(payload.get("config").cloned().unwrap_or(Value::Null)),
                ("POST", "/api/config/validate") => state
                    .service
                    .validate(payload.get("config").cloned().unwrap_or(Value::Null))
                    .map(|config| json!({"config":config})),
                ("POST", "/api/config/restore") => state.service.restore_backup(),
                ("POST", "/api/sync") => state.service.sync("Web", &|| false),
                ("POST", "/api/scheduler") => {
                    let interval = match payload.get("interval") {
                        None => 5,
                        Some(value) => match value
                            .as_u64()
                            .and_then(|value| u16::try_from(value).ok())
                            .filter(|value| (1..=1440).contains(value))
                        {
                            Some(value) => value,
                            None => {
                                return Response::error(
                                    400,
                                    "invalid_config",
                                    "Scheduler interval must be between 1 and 1440 minutes.",
                                );
                            }
                        },
                    };
                    state
                        .service
                        .configure_scheduler(
                            payload
                                .get("action")
                                .and_then(Value::as_str)
                                .unwrap_or_default(),
                            payload
                                .get("scheduler")
                                .and_then(Value::as_str)
                                .unwrap_or("auto"),
                            interval,
                        )
                        .map(|scheduler| json!({"scheduler":scheduler}))
                }
                _ => return Response::error(404, "not_found", "Resource not found."),
            }
        }
        _ => return Response::error(405, "method_not_allowed", "Method not allowed."),
    };
    match result {
        Ok(value) => Response::json(200, value),
        Err(error) => error.into(),
    }
}

fn asset(path: &str) -> Option<(&'static [u8], &'static str)> {
    match path {
        "/" | "/index.html" | "/dashboard" | "/dashboard/" => Some((
            include_bytes!("../../web/index.html"),
            "text/html; charset=utf-8",
        )),
        "/assets/dashboard.js" => Some((
            include_bytes!("../../web/dashboard.js"),
            "application/javascript; charset=utf-8",
        )),
        "/assets/dashboard.css" => Some((
            include_bytes!("../../web/dashboard.css"),
            "text/css; charset=utf-8",
        )),
        "/assets/ddns.svg" => Some((include_bytes!("../../web/ddns.svg"), "image/svg+xml")),
        _ => None,
    }
}

use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use ddns_rs::dashboard::DashboardService;
use ddns_rs::http_server::HttpServer;
use ddns_rs::http_settings::HttpSettings;
use ddns_rs::mcp::{CLIENT_CAPABILITIES_KEY, PROTOCOL_VERSION, PROTOCOL_VERSION_KEY};
use serde_json::{Value, json};

struct TestServer {
    address: SocketAddr,
    stop: Arc<AtomicBool>,
    thread: Option<JoinHandle<()>>,
    directory: PathBuf,
    launch: String,
}

impl TestServer {
    fn new(web: bool, token: Option<&str>) -> Self {
        let mut random = [0; 8];
        getrandom::fill(&mut random).unwrap();
        let directory = std::env::temp_dir().join(format!(
            "ddns-http-test-{}-{}",
            std::process::id(),
            u64::from_ne_bytes(random)
        ));
        fs::create_dir(&directory).unwrap();
        let path = directory.join("config.json");
        fs::write(
            &path,
            serde_json::to_vec(&config("home.example.com")).unwrap(),
        )
        .unwrap();
        let service = Arc::new(DashboardService::new(Some(path), 5).unwrap());
        let settings = HttpSettings::from_value(&json!({"host":"127.0.0.1","port":0,"token":token,"origins":["https://client.example"]}), true).unwrap();
        let server = HttpServer::bind(service, settings, web).unwrap();
        let address = server.local_addr().unwrap();
        let launch = server.launch_url().unwrap();
        let stop = Arc::new(AtomicBool::new(false));
        let stopping = Arc::clone(&stop);
        let thread = thread::spawn(move || server.serve(&stopping).unwrap());
        Self {
            address,
            stop,
            thread: Some(thread),
            directory,
            launch,
        }
    }

    fn request(&self, method: &str, path: &str, headers: &[(&str, &str)], body: &str) -> Response {
        let host = if headers
            .iter()
            .any(|(name, _)| name.eq_ignore_ascii_case("host"))
        {
            String::new()
        } else {
            format!("Host: {}\r\n", self.address)
        };
        let mut request = format!(
            "{method} {path} HTTP/1.1\r\n{host}Content-Length: {}\r\n",
            body.len()
        );
        for (name, value) in headers {
            request.push_str(&format!("{name}: {value}\r\n"));
        }
        request.push_str("\r\n");
        request.push_str(body);
        self.raw(&request)
    }

    fn raw(&self, request: &str) -> Response {
        let mut stream = TcpStream::connect(self.address).unwrap();
        stream
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        stream.write_all(request.as_bytes()).unwrap();
        let mut output = Vec::new();
        if let Err(error) = stream.read_to_end(&mut output) {
            assert!(!output.is_empty(), "read response: {error}");
        }
        Response::parse(output)
    }

    fn rpc(&self, message: &Value, overrides: &[(&str, &str)]) -> Response {
        let mut headers = BTreeMap::from([
            ("Content-Type", "application/json"),
            ("Accept", "application/json, text/event-stream"),
            (
                "MCP-Protocol-Version",
                message["params"]["_meta"][PROTOCOL_VERSION_KEY]
                    .as_str()
                    .unwrap_or(PROTOCOL_VERSION),
            ),
            (
                "Mcp-Method",
                message["method"].as_str().unwrap_or("tools/list"),
            ),
        ]);
        if message["method"] == "tools/call" {
            headers.insert("Mcp-Name", message["params"]["name"].as_str().unwrap());
        }
        headers.extend(overrides.iter().copied());
        self.request(
            "POST",
            "/mcp",
            &headers.into_iter().collect::<Vec<_>>(),
            &message.to_string(),
        )
    }
}

impl Drop for TestServer {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Release);
        if let Some(thread) = self.thread.take() {
            thread.join().unwrap();
        }
        fs::remove_dir_all(&self.directory).unwrap();
    }
}

struct Response {
    status: u16,
    headers: BTreeMap<String, String>,
    body: Vec<u8>,
}
impl Response {
    fn parse(output: Vec<u8>) -> Self {
        let end = output
            .windows(4)
            .position(|window| window == b"\r\n\r\n")
            .expect("response framing");
        let headers = String::from_utf8(output[..end].to_vec()).unwrap();
        let mut lines = headers.split("\r\n");
        let status = lines
            .next()
            .unwrap()
            .split(' ')
            .nth(1)
            .unwrap()
            .parse()
            .unwrap();
        let headers = lines
            .map(|line| {
                let (name, value) = line.split_once(':').unwrap();
                (name.to_ascii_lowercase(), value.trim().to_owned())
            })
            .collect();
        Self {
            status,
            headers,
            body: output[end + 4..].to_vec(),
        }
    }
    fn json(&self) -> Value {
        serde_json::from_slice(&self.body).unwrap()
    }
}

fn config(domain: &str) -> Value {
    json!({"cache":false,"providers":[{"provider":"debug","id":"provider-id-secret","token":"provider-token-secret","ipv4":[domain],"index4":"shell:echo 192.0.2.44","index6":false}]})
}

fn message(method: &str, mut params: Value) -> Value {
    params["_meta"] = json!({PROTOCOL_VERSION_KEY:PROTOCOL_VERSION,CLIENT_CAPABILITIES_KEY:{}});
    json!({"jsonrpc":"2.0","id":1,"method":method,"params":params})
}

#[test]
fn serves_only_embedded_assets_with_security_headers_and_head() {
    let server = TestServer::new(true, None);
    for path in [
        "/",
        "/index.html",
        "/dashboard",
        "/dashboard/",
        "/assets/dashboard.js",
        "/assets/dashboard.css",
        "/assets/ddns.svg",
    ] {
        let response = server.request("GET", path, &[], "");
        assert_eq!(response.status, 200, "{path}");
        assert!(!response.body.is_empty());
        assert_eq!(response.headers["x-content-type-options"], "nosniff");
        assert!(response.headers["content-security-policy"].contains("frame-ancestors 'none'"));
        let head = server.request("HEAD", path, &[], "");
        assert_eq!(head.status, 200);
        assert!(head.body.is_empty());
        assert_eq!(
            head.headers["content-length"],
            response.body.len().to_string()
        );
    }
    for path in [
        "/config.json",
        "/../config.json",
        "/assets/../../config.json",
        "/assets/%2e%2e/config.json",
    ] {
        assert_eq!(server.request("GET", path, &[], "").status, 404);
    }
}

#[test]
fn protects_api_and_bootstraps_browser_exactly_once() {
    let server = TestServer::new(true, Some("http-test-token"));
    assert!(!server.launch.contains("http-test-token"));
    assert_eq!(server.request("GET", "/api/config", &[], "").status, 403);
    assert_eq!(
        server
            .request("GET", "/api/config?token=http-test-token", &[], "")
            .status,
        403
    );
    let path = server.launch.split_once("/launch/").unwrap().1;
    let path = format!("/launch/{path}");
    assert_eq!(server.request("HEAD", &path, &[], "").status, 403);
    let launch = server.request("GET", &path, &[], "");
    assert_eq!(launch.status, 302);
    assert_eq!(
        launch.headers["location"],
        "/#token=http-test-token&view=overview"
    );
    assert_eq!(server.request("GET", &path, &[], "").status, 403);
    for headers in [
        vec![("X-DDNS-Token", "http-test-token")],
        vec![
            ("Authorization", "Bearer http-test-token"),
            ("Host", "reverse-proxy.example"),
        ],
    ] {
        assert_eq!(
            server.request("GET", "/api/config", &headers, "").status,
            200
        );
    }
    let status = server.request(
        "GET",
        "/api/dashboard",
        &[("Authorization", "Bearer http-test-token")],
        "",
    );
    assert_eq!(status.status, 200);
    assert!(!String::from_utf8(status.body).unwrap().contains("secret"));
}

#[test]
fn rejects_dns_rebinding_and_cross_origin_web_writes() {
    let server = TestServer::new(true, None);
    for host in [
        "attacker.example",
        "127.0.0.1.attacker.example",
        "127.0.0.1:bad",
        "127.0.0.1/path",
        "user@127.0.0.1",
    ] {
        assert_eq!(
            server
                .request("GET", "/api/config", &[("Host", host)], "")
                .status,
            421,
            "{host}"
        );
    }
    for origin in ["https://evil.example", "null", "https://client.example"] {
        assert_eq!(
            server
                .request(
                    "POST",
                    "/api/sync",
                    &[("Content-Type", "application/json"), ("Origin", origin)],
                    "{}"
                )
                .status,
            403
        );
    }
    assert_eq!(server.request("GET", "/api/config", &[], "").status, 200);
}

#[test]
fn configuration_validation_persistence_restore_and_sync_use_real_service() {
    let server = TestServer::new(true, None);
    let headers = [("Content-Type", "application/json")];
    let original = server.request("GET", "/api/config", &[], "").json();
    assert!(original["model"]["providers"].is_array());
    let replacement = config("new.example.com");
    let body = json!({"config":replacement}).to_string();
    let validation = server.request("POST", "/api/config/validate", &headers, &body);
    assert_eq!(validation.status, 200);
    assert_eq!(
        server.request("GET", "/api/config", &[], "").json()["config"],
        original["config"]
    );
    let saved = server.request("PUT", "/api/config", &headers, &body);
    assert_eq!(saved.status, 200);
    assert_eq!(saved.json()["backup_available"], true);
    assert_eq!(
        saved.json()["config"]["providers"][0]["ipv4"][0],
        "new.example.com"
    );
    let sync = server.request("POST", "/api/sync", &headers, "{}");
    assert_eq!(sync.status, 200, "{}", String::from_utf8_lossy(&sync.body));
    assert_eq!(sync.json()["state"], "synced");
    assert_eq!(sync.json()["records"][0]["value"], "192.0.2.44");
    let restored = server.request("POST", "/api/config/restore", &headers, "{}");
    assert_eq!(restored.status, 200);
    assert_eq!(
        restored.json()["config"]["providers"][0]["ipv4"][0],
        "home.example.com"
    );
    let invalid = server.request(
        "PUT",
        "/api/config",
        &headers,
        r#"{"config":{"providers":{}}}"#,
    );
    assert_eq!(invalid.status, 400);
    assert_eq!(
        server.request("GET", "/api/config", &[], "").json()["config"],
        restored.json()["config"]
    );
}

#[test]
fn scheduler_controls_validate_interval_without_installing_system_tasks() {
    let server = TestServer::new(true, None);
    let headers = [("Content-Type", "application/json")];
    let disabled = server.request(
        "POST",
        "/api/scheduler",
        &headers,
        r#"{"action":"disable","scheduler":"web","interval":7}"#,
    );
    assert_eq!(disabled.status, 200);
    assert_eq!(disabled.json()["scheduler"]["enabled"], false);
    for interval in [json!(true), json!(1.5), json!(0), json!(1441), json!("5")] {
        let response = server.request(
            "POST",
            "/api/scheduler",
            &headers,
            &json!({"action":"enable","interval":interval}).to_string(),
        );
        assert_eq!(response.status, 400);
    }
    assert_eq!(
        server
            .request(
                "POST",
                "/api/scheduler",
                &headers,
                r#"{"action":"takeover"}"#
            )
            .status,
        501
    );
}

#[test]
fn modern_mcp_discovery_tools_notifications_and_shared_state() {
    let server = TestServer::new(true, None);
    let discover = server.rpc(&message("server/discover", json!({})), &[]);
    assert_eq!(discover.status, 200);
    assert_eq!(
        discover.json()["result"]["supportedVersions"],
        json!([PROTOCOL_VERSION])
    );
    let tools = server.rpc(&message("tools/list", json!({})), &[]);
    assert_eq!(tools.json()["result"]["tools"].as_array().unwrap().len(), 2);
    let updated = server.rpc(
        &message(
            "tools/call",
            json!({"name":"update_dns_records","arguments":{}}),
        ),
        &[],
    );
    assert_eq!(updated.status, 200);
    assert_eq!(updated.json()["result"]["isError"], false);
    let status = server.rpc(
        &message("tools/call", json!({"name":"get_ddns_status"})),
        &[],
    );
    assert_eq!(
        status.json()["result"]["structuredContent"]["state"],
        "synced"
    );
    assert!(
        status.json()["result"]["structuredContent"]
            .get("config_path")
            .is_none()
    );
    assert!(!String::from_utf8(status.body).unwrap().contains("secret"));
    assert_eq!(
        server.request("GET", "/api/dashboard", &[], "").json()["state"],
        "synced"
    );
    let mut notification = message("notifications/cancelled", json!({"requestId":1}));
    notification.as_object_mut().unwrap().remove("id");
    let response = server.rpc(&notification, &[]);
    assert_eq!(response.status, 202);
    assert!(response.body.is_empty());
}

#[test]
fn standalone_mcp_has_no_dashboard_and_requires_bearer_auth() {
    let server = TestServer::new(false, Some("http-test-token"));
    assert_eq!(server.request("GET", "/", &[], "").status, 404);
    assert_eq!(server.request("GET", "/api/config", &[], "").status, 404);
    let request = message("tools/list", json!({}));
    let rejected = server.rpc(&request, &[]);
    assert_eq!(rejected.status, 401);
    assert!(rejected.headers.contains_key("www-authenticate"));
    assert_eq!(
        server
            .rpc(&request, &[("X-DDNS-Token", "http-test-token")])
            .status,
        401
    );
    assert_eq!(
        server
            .rpc(&request, &[("Authorization", "Bearer http-test-token")])
            .status,
        200
    );
}

#[test]
fn mcp_validates_media_routing_headers_and_jsonrpc_before_dispatch() {
    let server = TestServer::new(false, None);
    let request = message("tools/call", json!({"name":"get_ddns_status"}));
    for (headers, status, code) in [
        (
            vec![("MCP-Protocol-Version", "2025-11-25")],
            400,
            Some(-32020),
        ),
        (vec![("Mcp-Method", "tools/list")], 400, Some(-32020)),
        (vec![("Mcp-Name", "update_dns_records")], 400, Some(-32020)),
        (vec![("Accept", "application/json")], 406, None),
        (
            vec![("Accept", "application/json;q=0, text/event-stream")],
            406,
            None,
        ),
        (vec![("Content-Type", "text/plain")], 415, None),
    ] {
        let response = server.rpc(&request, &headers);
        assert_eq!(response.status, status);
        if let Some(code) = code {
            assert_eq!(response.json()["error"]["code"], code);
        }
    }
    let mut legacy = request.clone();
    legacy["params"]["_meta"][PROTOCOL_VERSION_KEY] = json!("2025-11-25");
    assert_eq!(server.rpc(&legacy, &[]).json()["error"]["code"], -32022);
    let mut invalid = request.clone();
    invalid["id"] = json!([]);
    let response = server.rpc(&invalid, &[("Mcp-Method", "mismatch")]);
    assert_eq!(response.status, 400);
    assert_eq!(response.json()["error"]["code"], -32600);
    assert!(response.json()["id"].is_null());
    assert_eq!(
        server
            .rpc(&message("resources/list", json!({})), &[])
            .status,
        404
    );
    assert_eq!(
        server
            .rpc(
                &message("resources/read", json!({"uri":"file:///status"})),
                &[]
            )
            .json()["error"]["code"],
        -32020
    );
    assert_eq!(
        server
            .rpc(
                &message("resources/read", json!({"uri":"file:///status"})),
                &[("Mcp-Name", "file:///status")]
            )
            .status,
        404
    );
    assert_eq!(
        server
            .rpc(&request, &[("Mcp-Name", "=?base64?Z2V0X2RkbnNfc3RhdHVz?=")])
            .status,
        200
    );
}

#[test]
fn rejects_duplicate_mcp_routing_headers_and_batch_requests() {
    let server = TestServer::new(false, None);
    let body = message("tools/list", json!({})).to_string();
    let response = server.raw(&format!("POST /mcp HTTP/1.1\r\nHost: {}\r\nContent-Type: application/json\r\nAccept: application/json, text/event-stream\r\nContent-Length: {}\r\nMCP-Protocol-Version: {PROTOCOL_VERSION}\r\nMCP-Protocol-Version: {PROTOCOL_VERSION}\r\nMcp-Method: tools/list\r\n\r\n{body}",server.address,body.len()));
    assert_eq!(response.status, 400);
    assert_eq!(response.json()["error"]["code"], -32020);
    let response = server.request(
        "POST",
        "/mcp",
        &[
            ("Content-Type", "application/json"),
            ("Accept", "application/json, text/event-stream"),
        ],
        "[]",
    );
    assert_eq!(response.json()["error"]["code"], -32600);
}

#[test]
fn cors_is_exact_and_applies_to_transport_errors_only_on_mcp() {
    let server = TestServer::new(false, None);
    let request = message("tools/list", json!({}));
    for origin in ["https://evil.example", "null"] {
        assert_eq!(server.rpc(&request, &[("Origin", origin)]).status, 403);
        assert_eq!(
            server
                .request("GET", "/mcp", &[("Origin", origin)], "")
                .status,
            403
        );
    }
    let preflight = server.request(
        "OPTIONS",
        "/mcp",
        &[("Origin", "https://client.example")],
        "",
    );
    assert_eq!(preflight.status, 204);
    assert_eq!(
        preflight.headers["access-control-allow-origin"],
        "https://client.example"
    );
    assert_eq!(
        server
            .request("OPTIONS", "/mcp", &[("Origin", "https://evil.example")], "")
            .status,
        403
    );
    let response = server.rpc(
        &request,
        &[
            ("Origin", "https://client.example"),
            ("Mcp-Method", "wrong"),
        ],
    );
    assert_eq!(response.status, 400);
    assert_eq!(
        response.headers["access-control-allow-origin"],
        "https://client.example"
    );
    let direct = format!("http://{}", server.address);
    assert_eq!(server.rpc(&request, &[("Origin", &direct)]).status, 200);
    let method = server.request("GET", "/mcp", &[], "");
    assert_eq!(method.status, 405);
    assert_eq!(method.headers["allow"], "POST, OPTIONS");
}

#[test]
fn bounds_request_framing_and_rejects_auth_before_reading_body() {
    let server = TestServer::new(true, Some("http-test-token"));
    let started = Instant::now();
    let response = server.raw(&format!("POST /mcp HTTP/1.1\r\nHost: {}\r\nContent-Length: 100\r\nContent-Type: application/json\r\n\r\n",server.address));
    assert_eq!(response.status, 401);
    assert!(started.elapsed() < Duration::from_secs(2));
    for extra in [
        "Content-Length: 0\r\nContent-Length: 0\r\n",
        "Transfer-Encoding: chunked\r\n",
        "Host: duplicate\r\n",
    ] {
        let response = server.raw(&format!(
            "POST /api/sync HTTP/1.1\r\nHost: {}\r\n{extra}\r\n",
            server.address
        ));
        assert_eq!(response.status, 400);
    }
    let too_large = server.raw(&format!("POST /api/sync HTTP/1.1\r\nHost: {}\r\nAuthorization: Bearer http-test-token\r\nContent-Type: application/json\r\nContent-Length: 2097153\r\n\r\n",server.address));
    assert_eq!(too_large.status, 413);
    assert_eq!(server.raw("bad request\r\n\r\n").status, 400);
}

#[test]
fn authentication_rejection_delivers_complete_response_for_buffered_body() {
    let server = TestServer::new(false, Some("http-test-token"));
    let body = "x".repeat(128 * 1024);
    let response = server.request(
        "POST",
        "/mcp",
        &[("Content-Type", "application/json")],
        &body,
    );
    assert_eq!(response.status, 401);
    assert_eq!(
        response.headers["content-length"],
        response.body.len().to_string()
    );
    assert_eq!(response.json()["error"]["code"], "invalid_token");
}

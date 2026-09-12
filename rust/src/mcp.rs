use std::collections::HashMap;
use std::io::{self, BufRead, BufReader, Write};
use std::panic::{AssertUnwindSafe, catch_unwind};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, mpsc};
use std::thread;

use serde_json::{Value, json};

use crate::dashboard::DashboardService;
use crate::error::Result;

pub const PROTOCOL_VERSION: &str = "2026-07-28";
pub const LEGACY_PROTOCOL_VERSION: &str = "2025-11-25";
pub const PROTOCOL_VERSION_KEY: &str = "io.modelcontextprotocol/protocolVersion";
pub const CLIENT_CAPABILITIES_KEY: &str = "io.modelcontextprotocol/clientCapabilities";
const CLIENT_INFO_KEY: &str = "io.modelcontextprotocol/clientInfo";
const SERVER_INFO_KEY: &str = "io.modelcontextprotocol/serverInfo";
const INSTRUCTIONS: &str = "Use get_ddns_status to inspect local cached state. Use update_dns_records only with user approval to update configured DNS records.";
const STATUS_FIELDS: [&str; 6] = [
    "state",
    "message",
    "last_sync",
    "addresses",
    "providers",
    "records",
];
const MAX_LINE_BYTES: usize = 1024 * 1024;

pub fn error_response(id: Value, code: i64, message: &str) -> Value {
    json!({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})
}

fn request_id(message: &Value) -> Option<&Value> {
    message
        .get("id")
        .filter(|id| id.is_string() || id.as_i64().is_some() || id.as_u64().is_some())
}

fn server_info() -> Value {
    json!({"name": "ddns", "version": env!("CARGO_PKG_VERSION")})
}

fn complete(mut result: Value, modern: bool) -> Value {
    if modern {
        result["resultType"] = json!("complete");
        result["_meta"] = json!({SERVER_INFO_KEY: server_info()});
    }
    result
}

fn valid_client_info(info: &Value) -> bool {
    info.is_object() && info["name"].is_string() && info["version"].is_string()
}

fn validate_meta(params: &Value) -> std::result::Result<&Value, String> {
    let meta = &params["_meta"];
    if !meta.is_object() {
        return Err("params._meta must be an object.".into());
    }
    if !meta[PROTOCOL_VERSION_KEY].is_string() {
        return Err(format!("{PROTOCOL_VERSION_KEY} is required."));
    }
    if !meta[CLIENT_CAPABILITIES_KEY].is_object() {
        return Err(format!("{CLIENT_CAPABILITIES_KEY} is required."));
    }
    if !meta[CLIENT_INFO_KEY].is_null() && !valid_client_info(&meta[CLIENT_INFO_KEY]) {
        return Err(format!(
            "{CLIENT_INFO_KEY} must contain string name and version fields."
        ));
    }
    Ok(meta)
}

fn tools() -> Value {
    json!([
        {
            "name": "get_ddns_status",
            "title": "Get DDNS status",
            "description": "Read configured providers, cached DNS records, addresses, and the latest local sync status.",
            "inputSchema": {"type": "object", "additionalProperties": false},
            "annotations": {"title": "Get DDNS status", "readOnlyHint": true, "destructiveHint": false, "idempotentHint": true, "openWorldHint": true}
        },
        {
            "name": "update_dns_records",
            "title": "Update DNS records",
            "description": "Run one complete DDNS synchronization for every record in the configured local file.",
            "inputSchema": {"type": "object", "additionalProperties": false},
            "annotations": {"title": "Update DNS records", "readOnlyHint": false, "destructiveHint": true, "idempotentHint": true, "openWorldHint": true}
        }
    ])
}

fn tool_success(status: Value, modern: bool) -> Value {
    let status: Value = STATUS_FIELDS
        .into_iter()
        .map(|field| (field.to_owned(), status[field].clone()))
        .collect();
    complete(
        json!({"content": [{"type": "text", "text": status.to_string()}], "structuredContent": status, "isError": false}),
        modern,
    )
}

pub struct McpServer {
    service: Arc<DashboardService>,
    modern_only: bool,
    legacy_initialized: bool,
    legacy_ready: bool,
}

impl McpServer {
    pub fn new(service: Arc<DashboardService>, modern_only: bool) -> Self {
        Self {
            service,
            modern_only,
            legacy_initialized: false,
            legacy_ready: false,
        }
    }

    fn supported_versions(&self) -> Value {
        if self.modern_only {
            json!([PROTOCOL_VERSION])
        } else {
            json!([PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])
        }
    }

    pub fn handle_message(
        &mut self,
        message: Value,
        cancelled: &(dyn Fn() -> bool + Sync),
    ) -> Option<Value> {
        let id = request_id(&message).cloned().unwrap_or(Value::Null);
        if !message.is_object() || message["jsonrpc"] != "2.0" || !message["method"].is_string() {
            return Some(error_response(id, -32600, "Invalid Request"));
        }
        let method = message["method"].as_str().unwrap();
        if message.get("id").is_none() {
            if !self.modern_only && method == "notifications/initialized" && self.legacy_initialized
            {
                self.legacy_ready = true;
            }
            return None;
        }
        if id.is_null() {
            return Some(error_response(id, -32600, "Invalid Request"));
        }
        let empty = json!({});
        let params = message.get("params").unwrap_or(&empty);
        if !params.is_object() {
            return Some(error_response(id, -32602, "Invalid params"));
        }
        let modern = self.modern_only || (method != "initialize" && !self.legacy_initialized);
        if !modern {
            if method == "initialize" {
                return Some(self.initialize(id, params));
            }
            if !self.legacy_ready && method != "ping" {
                return Some(error_response(id, -32600, "Server is not initialized"));
            }
        } else {
            if method == "server/discover" && !params["_meta"].is_object() {
                return Some(error_response(id, -32601, "Method not found"));
            }
            let meta = match validate_meta(params) {
                Ok(meta) => meta,
                Err(message) => return Some(error_response(id, -32602, &message)),
            };
            if meta[PROTOCOL_VERSION_KEY] != PROTOCOL_VERSION {
                let mut response = error_response(id, -32022, "Unsupported protocol version");
                response["error"]["data"] = json!({"supported": self.supported_versions(), "requested": meta[PROTOCOL_VERSION_KEY]});
                return Some(response);
            }
        }
        Some(
            match catch_unwind(AssertUnwindSafe(|| {
                self.dispatch(method, params, modern, cancelled)
            })) {
                Ok(Ok(Some(result))) => json!({"jsonrpc": "2.0", "id": id, "result": result}),
                Ok(Ok(None)) => error_response(id, -32601, "Method not found"),
                Ok(Err(message)) => error_response(id, -32602, &message),
                Err(_) => error_response(id, -32603, "Internal error"),
            },
        )
    }

    fn initialize(&mut self, id: Value, params: &Value) -> Value {
        let error = if !params["protocolVersion"].is_string() {
            Some("protocolVersion is required.")
        } else if !params["capabilities"].is_object() {
            Some("capabilities must be an object.")
        } else if !valid_client_info(&params["clientInfo"]) {
            Some("clientInfo must contain string name and version fields.")
        } else {
            None
        };
        if let Some(message) = error {
            return error_response(id, -32602, message);
        }
        self.legacy_initialized = true;
        self.legacy_ready = false;
        json!({"jsonrpc": "2.0", "id": id, "result": {
            "protocolVersion": LEGACY_PROTOCOL_VERSION, "capabilities": {"tools": {}},
            "serverInfo": server_info(), "instructions": INSTRUCTIONS
        }})
    }

    fn dispatch(
        &self,
        method: &str,
        params: &Value,
        modern: bool,
        cancelled: &(dyn Fn() -> bool + Sync),
    ) -> std::result::Result<Option<Value>, String> {
        let result = match method {
            "server/discover" if modern => complete(
                json!({
                    "supportedVersions": self.supported_versions(), "capabilities": {"tools": {}},
                    "instructions": INSTRUCTIONS, "ttlMs": 3600000, "cacheScope": "public"
                }),
                true,
            ),
            "tools/list" => {
                if !params["cursor"].is_null() {
                    return Err("Pagination cursor is not supported.".into());
                }
                let mut result = json!({"tools": tools()});
                if modern {
                    result["ttlMs"] = json!(3600000);
                    result["cacheScope"] = json!("public");
                }
                complete(result, modern)
            }
            "tools/call" => self.call_tool(params, modern, cancelled)?,
            "ping" if !modern => json!({}),
            _ => return Ok(None),
        };
        Ok(Some(result))
    }

    fn call_tool(
        &self,
        params: &Value,
        modern: bool,
        cancelled: &(dyn Fn() -> bool + Sync),
    ) -> std::result::Result<Value, String> {
        let name = params["name"]
            .as_str()
            .ok_or("Tool name must be a string.")?;
        let empty = json!({});
        let arguments = params
            .get("arguments")
            .unwrap_or(&empty)
            .as_object()
            .ok_or("Tool arguments must be an object.")?;
        if !arguments.is_empty() {
            return Err("This tool does not accept arguments.".into());
        }
        let status = match name {
            "get_ddns_status" => self.service.dashboard(),
            "update_dns_records" => self.service.sync("MCP", cancelled),
            _ => return Err(format!("Unknown tool: {name}")),
        };
        Ok(match status {
            Ok(status) => tool_success(status, modern),
            Err(error) => complete(
                json!({"content": [{"type": "text", "text": error.to_string()}], "isError": true}),
                modern,
            ),
        })
    }
}

#[derive(Default)]
struct Pending {
    requests: HashMap<String, Vec<Arc<AtomicBool>>>,
}

impl Pending {
    fn register(&mut self, id: &Value) -> Arc<AtomicBool> {
        let flag = Arc::new(AtomicBool::new(false));
        self.requests
            .entry(id.to_string())
            .or_default()
            .push(flag.clone());
        flag
    }

    fn cancel(&self, message: &Value) -> bool {
        if message.get("method").and_then(Value::as_str) != Some("notifications/cancelled") {
            return false;
        }
        // Like Python stdio, consume malformed cancellation messages without a response.
        if message["jsonrpc"] == "2.0" && message.get("id").is_none() {
            let id = &message["params"]["requestId"];
            if (id.is_string() || id.as_i64().is_some() || id.as_u64().is_some())
                && let Some(flags) = self.requests.get(&id.to_string())
            {
                for flag in flags {
                    flag.store(true, Ordering::Release);
                }
            }
        }
        true
    }

    fn remove(&mut self, id: &Value, flag: &Arc<AtomicBool>) {
        let key = id.to_string();
        if let Some(flags) = self.requests.get_mut(&key) {
            flags.retain(|pending| !Arc::ptr_eq(pending, flag));
            if flags.is_empty() {
                self.requests.remove(&key);
            }
        }
    }
}

struct Incoming {
    message: Value,
    parse_error: bool,
    flag: Option<Arc<AtomicBool>>,
}

// Drain overlong lines without allocating their full length, then resume at the next frame.
fn read_frame(reader: &mut impl BufRead) -> io::Result<Option<Vec<u8>>> {
    let mut line = Vec::new();
    let mut oversized = false;
    loop {
        let buffer = reader.fill_buf()?;
        if buffer.is_empty() {
            return Ok(if oversized {
                Some(Vec::new())
            } else if line.is_empty() {
                None
            } else {
                Some(line)
            });
        }
        let end = buffer.iter().position(|byte| *byte == b'\n');
        let count = end.map_or(buffer.len(), |index| index + 1);
        if !oversized && line.len() + count <= MAX_LINE_BYTES {
            line.extend_from_slice(&buffer[..count]);
        } else {
            oversized = true;
            line.clear();
        }
        reader.consume(count);
        if end.is_some() {
            return Ok(Some(line));
        }
    }
}

pub fn serve_streams<R: BufRead + Send + 'static, W: Write>(
    service: Arc<DashboardService>,
    mut input: R,
    mut output: W,
) -> Result<()> {
    let pending = Arc::new(Mutex::new(Pending::default()));
    let reader_pending = pending.clone();
    let (sender, receiver) = mpsc::channel();
    // The reader must remain independent of sync so it can observe cancellation in flight.
    // It is detached on output failure: stdin may be blocked indefinitely.
    thread::Builder::new()
        .name("ddns-mcp-reader".into())
        .spawn(move || {
            loop {
                let line = match read_frame(&mut input) {
                    Ok(Some(line)) => line,
                    Ok(None) => break,
                    Err(error) => {
                        let _ = sender.send(Err(error));
                        break;
                    }
                };
                let incoming = match serde_json::from_slice::<Value>(&line) {
                    Ok(message) => {
                        let mut pending = reader_pending
                            .lock()
                            .unwrap_or_else(|error| error.into_inner());
                        if pending.cancel(&message) {
                            continue;
                        }
                        let flag = request_id(&message).map(|id| pending.register(id));
                        Incoming {
                            message,
                            parse_error: false,
                            flag,
                        }
                    }
                    Err(_) => Incoming {
                        message: error_response(Value::Null, -32700, "Parse error"),
                        parse_error: true,
                        flag: None,
                    },
                };
                if sender.send(Ok(incoming)).is_err() {
                    break;
                }
            }
        })?;
    let mut server = McpServer::new(service, false);
    for incoming in receiver {
        let incoming = incoming?;
        let cancelled = || {
            incoming
                .flag
                .as_ref()
                .is_some_and(|flag| flag.load(Ordering::Acquire))
        };
        let id = request_id(&incoming.message).cloned();
        let response = if cancelled() {
            None
        } else if incoming.parse_error {
            Some(incoming.message.clone())
        } else {
            server.handle_message(incoming.message.clone(), &cancelled)
        };
        // Serialize response publication with cancellation, including the final suppression check.
        let mut pending = pending.lock().unwrap_or_else(|error| error.into_inner());
        if let (Some(id), Some(flag)) = (id, &incoming.flag) {
            pending.remove(&id, flag);
        }
        if !cancelled()
            && let Some(response) = response
        {
            serde_json::to_writer(&mut output, &response)?;
            output.write_all(b"\n")?;
            output.flush()?;
        }
    }
    Ok(())
}

pub fn serve_stdio(service: Arc<DashboardService>) -> Result<()> {
    serve_streams(service, BufReader::new(io::stdin()), io::stdout().lock())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::io::Cursor;
    use std::path::PathBuf;
    use std::sync::atomic::AtomicUsize;

    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            static NEXT: AtomicUsize = AtomicUsize::new(0);
            let path = std::env::temp_dir().join(format!(
                "ddns-mcp-unit-{}-{}",
                std::process::id(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            fs::create_dir(&path).unwrap();
            fs::write(path.join("config.json"), json!({"cache": false, "providers": [{"provider": "debug", "ipv4": ["test.example.com"], "index4": "shell:echo 192.0.2.10", "index6": false}]}).to_string()).unwrap();
            Self(path)
        }
        fn service(&self) -> Arc<DashboardService> {
            Arc::new(DashboardService::new(Some(self.0.join("config.json")), 5).unwrap())
        }
        fn server(&self) -> McpServer {
            McpServer::new(self.service(), false)
        }
    }
    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    fn request(method: &str, mut params: Value) -> Value {
        params["_meta"] =
            json!({PROTOCOL_VERSION_KEY: PROTOCOL_VERSION, CLIENT_CAPABILITIES_KEY: {}});
        json!({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    }
    fn call(server: &mut McpServer, request: Value) -> Value {
        server.handle_message(request, &|| false).unwrap()
    }
    fn initialize() -> Value {
        json!({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": LEGACY_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}})
    }

    #[test]
    fn discovery_tools_and_safety_annotations() {
        let fixture = Fixture::new();
        let mut server = fixture.server();
        let result = call(&mut server, request("server/discover", json!({})))["result"].clone();
        assert_eq!(
            result["supportedVersions"],
            json!([PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])
        );
        assert_eq!(result["capabilities"], json!({"tools": {}}));
        assert_eq!(result["resultType"], "complete");
        assert_eq!(result["_meta"][SERVER_INFO_KEY], server_info());
        assert_eq!(result["instructions"], INSTRUCTIONS);
        assert_eq!(result["ttlMs"], 3600000);
        assert_eq!(result["cacheScope"], "public");
        let result = call(&mut server, request("tools/list", json!({})))["result"].clone();
        assert_eq!(result["tools"], tools());
        for (index, name, read_only) in [
            (0, "get_ddns_status", true),
            (1, "update_dns_records", false),
        ] {
            let tool = &result["tools"][index];
            assert_eq!(tool["name"], name);
            assert_eq!(
                tool["inputSchema"],
                json!({"type": "object", "additionalProperties": false})
            );
            assert_eq!(tool["annotations"]["readOnlyHint"], read_only);
            assert_eq!(tool["annotations"]["destructiveHint"], !read_only);
            assert_eq!(tool["annotations"]["idempotentHint"], true);
            assert_eq!(tool["annotations"]["openWorldHint"], true);
        }
        assert_eq!(result["ttlMs"], 3600000);
        assert_eq!(
            call(&mut server, request("tools/list", json!({"cursor": ""})))["error"]["code"],
            -32602
        );
        assert!(
            call(&mut server, request("tools/list", json!({"cursor": null})))["result"].is_object()
        );
    }

    #[test]
    fn validates_envelopes_ids_notifications_and_batches() {
        let fixture = Fixture::new();
        let mut server = fixture.server();
        for value in [
            json!([]),
            json!([request("tools/list", json!({}))]),
            json!(null),
            json!(3),
            json!({}),
            json!({"jsonrpc":"2.0", "method":3}),
        ] {
            assert_eq!(
                call(&mut server, value),
                error_response(Value::Null, -32600, "Invalid Request")
            );
        }
        for id in [
            json!(true),
            json!(false),
            json!(null),
            json!(1.0),
            json!([]),
            json!({}),
        ] {
            let mut message = request("tools/list", json!({}));
            message["id"] = id;
            assert_eq!(
                call(&mut server, message),
                error_response(Value::Null, -32600, "Invalid Request")
            );
        }
        for id in [
            json!(0),
            json!(-1),
            json!(u64::MAX),
            json!(""),
            json!("测试"),
        ] {
            let mut message = request("tools/list", json!({}));
            message["id"] = id.clone();
            assert_eq!(call(&mut server, message)["id"], id);
        }
        for method in [
            "notifications/initialized",
            "notifications/cancelled",
            "tools/call",
            "unknown",
        ] {
            assert!(
                server
                    .handle_message(
                        json!({"jsonrpc":"2.0", "method":method, "params":true}),
                        &|| false
                    )
                    .is_none()
            );
        }
        let mut message = request("tools/list", json!({}));
        message["jsonrpc"] = json!("1.0");
        assert_eq!(
            call(&mut server, message),
            error_response(json!(1), -32600, "Invalid Request")
        );
        for params in [json!(null), json!([]), json!(true)] {
            assert_eq!(
                call(
                    &mut server,
                    json!({"jsonrpc":"2.0", "id":1,"method":"tools/list","params":params})
                ),
                error_response(json!(1), -32602, "Invalid params")
            );
        }
    }

    #[test]
    fn metadata_validation_and_unknown_methods() {
        let fixture = Fixture::new();
        let mut server = fixture.server();
        assert_eq!(
            call(
                &mut server,
                json!({"jsonrpc":"2.0", "id":1,"method":"server/discover"})
            )["error"]["code"],
            -32601
        );
        for meta in [
            json!(null),
            json!({}),
            json!({PROTOCOL_VERSION_KEY: 3}),
            json!({PROTOCOL_VERSION_KEY:PROTOCOL_VERSION, CLIENT_CAPABILITIES_KEY:[]}),
            json!({PROTOCOL_VERSION_KEY:PROTOCOL_VERSION, CLIENT_CAPABILITIES_KEY:{}, CLIENT_INFO_KEY:{"name":3,"version":"1"}}),
        ] {
            let mut message = request("tools/list", json!({}));
            message["params"]["_meta"] = meta;
            assert_eq!(call(&mut server, message)["error"]["code"], -32602);
        }
        for info in [json!(null), json!({"name":"测试", "version":"1"})] {
            let mut message = request("tools/list", json!({}));
            message["params"]["_meta"][CLIENT_INFO_KEY] = info;
            assert!(call(&mut server, message)["result"].is_object());
        }
        for method in ["ping", "resources/list", "tasks/get", "unknown"] {
            assert_eq!(
                call(&mut server, request(method, json!({})))["error"]["code"],
                -32601
            );
        }
        let mut message = request("server/discover", json!({}));
        message["params"]["_meta"][PROTOCOL_VERSION_KEY] = json!(LEGACY_PROTOCOL_VERSION);
        assert_eq!(
            call(&mut server, message)["error"],
            json!({"code":-32022,"message":"Unsupported protocol version","data":{"supported":[PROTOCOL_VERSION,LEGACY_PROTOCOL_VERSION],"requested":LEGACY_PROTOCOL_VERSION}})
        );
    }

    #[test]
    fn legacy_lifecycle_reinitialization_and_modern_only_isolation() {
        let fixture = Fixture::new();
        let mut server = fixture.server();
        for (key, invalid) in [
            ("protocolVersion", json!(null)),
            ("capabilities", json!([])),
            ("clientInfo", json!({"name":"client"})),
        ] {
            let mut message = initialize();
            message["params"][key] = invalid;
            assert_eq!(call(&mut server, message)["error"]["code"], -32602);
        }
        let result = call(&mut server, initialize())["result"].clone();
        assert_eq!(result["protocolVersion"], LEGACY_PROTOCOL_VERSION);
        assert!(result.get("resultType").is_none());
        assert_eq!(
            call(&mut server, json!({"jsonrpc":"2.0","id":1,"method":"ping"}))["result"],
            json!({})
        );
        assert_eq!(
            call(&mut server, request("tools/list", json!({})))["error"]["code"],
            -32600
        );
        assert!(
            server
                .handle_message(
                    json!({"jsonrpc":"2.0","method":"notifications/initialized"}),
                    &|| false
                )
                .is_none()
        );
        let result = call(
            &mut server,
            json!({"jsonrpc":"2.0","id":1,"method":"tools/list"}),
        )["result"]
            .clone();
        for key in ["resultType", "ttlMs", "cacheScope", "_meta"] {
            assert!(result.get(key).is_none());
        }
        assert_eq!(
            call(&mut server, request("server/discover", json!({})))["error"]["code"],
            -32601
        );
        assert_eq!(
            call(
                &mut server,
                json!({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_ddns_status"}})
            )["result"]["isError"],
            false
        );
        call(&mut server, initialize());
        assert_eq!(
            call(&mut server, request("tools/list", json!({})))["error"]["code"],
            -32600
        );
        let mut server = McpServer::new(fixture.service(), true);
        assert_eq!(call(&mut server, initialize())["error"]["code"], -32602);
        assert_eq!(
            call(&mut server, request("initialize", json!({})))["error"]["code"],
            -32601
        );
        server.handle_message(
            json!({"jsonrpc":"2.0","method":"notifications/initialized"}),
            &|| false,
        );
        assert_eq!(
            call(&mut server, request("server/discover", json!({})))["result"]["supportedVersions"],
            json!([PROTOCOL_VERSION])
        );
        let mut message = request("tools/list", json!({}));
        message["params"]["_meta"][PROTOCOL_VERSION_KEY] = json!(LEGACY_PROTOCOL_VERSION);
        assert_eq!(
            call(&mut server, message)["error"]["data"]["supported"],
            json!([PROTOCOL_VERSION])
        );
    }

    #[test]
    fn status_whitelist_and_real_debug_sync() {
        let result = tool_success(
            json!({"state":"synced", "message":"测试", "token":"secret", "config_path":"secret", "scheduler":{"token":"secret"}, "activities":[], "providers":[], "records":[]}),
            true,
        );
        assert_eq!(
            result["structuredContent"].as_object().unwrap().len(),
            STATUS_FIELDS.len()
        );
        assert_eq!(result["structuredContent"]["last_sync"], Value::Null);
        assert!(!result.to_string().contains("secret"));
        assert_eq!(
            serde_json::from_str::<Value>(result["content"][0]["text"].as_str().unwrap()).unwrap(),
            result["structuredContent"]
        );
        let fixture = Fixture::new();
        let mut server = fixture.server();
        let result = call(
            &mut server,
            request("tools/call", json!({"name":"update_dns_records"})),
        )["result"]
            .clone();
        assert_eq!(result["isError"], false, "{result}");
        assert_eq!(result["structuredContent"]["state"], "synced");
        assert_eq!(
            result["structuredContent"]["records"][0]["value"],
            "192.0.2.10"
        );
        let result = call(
            &mut server,
            request("tools/call", json!({"name":"get_ddns_status"})),
        )["result"]
            .clone();
        assert_eq!(result["isError"], false);
        assert_eq!(result["structuredContent"].as_object().unwrap().len(), 6);
    }

    #[test]
    fn tool_arguments_errors_repair_and_cooperative_cancellation() {
        let fixture = Fixture::new();
        let mut server = fixture.server();
        for params in [
            json!({}),
            json!({"name":3}),
            json!({"name":"missing"}),
            json!({"name":"update_dns_records","arguments":null}),
            json!({"name":"update_dns_records","arguments":[]}),
            json!({"name":"update_dns_records","arguments":{"domain":"injected"}}),
        ] {
            assert_eq!(
                call(&mut server, request("tools/call", params))["error"]["code"],
                -32602
            );
        }
        let result = server
            .handle_message(
                request("tools/call", json!({"name":"update_dns_records"})),
                &|| true,
            )
            .unwrap();
        assert_eq!(result["result"]["isError"], true);
        assert!(
            result["result"]["content"][0]["text"]
                .as_str()
                .unwrap()
                .to_lowercase()
                .contains("cancel")
        );
        let original = fs::read(fixture.0.join("config.json")).unwrap();
        fs::write(fixture.0.join("config.json"), "not JSON").unwrap();
        let mut server = fixture.server();
        assert!(call(&mut server, request("server/discover", json!({})))["result"].is_object());
        assert_eq!(
            call(
                &mut server,
                request("tools/call", json!({"name":"update_dns_records"}))
            )["result"]["isError"],
            true
        );
        fs::write(fixture.0.join("config.json"), original).unwrap();
        assert_eq!(
            call(
                &mut server,
                request("tools/call", json!({"name":"update_dns_records"}))
            )["result"]["isError"],
            false
        );
    }

    #[test]
    fn cancellation_tracks_only_pending_ids_and_cleans_up_reused_ids() {
        let mut pending = Pending::default();
        let cancel = |id| json!({"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":id}});
        for id in 0..10000 {
            assert!(pending.cancel(&cancel(json!(id))));
        }
        assert!(pending.requests.is_empty());
        let first = pending.register(&json!(1));
        let second = pending.register(&json!(1));
        let string_id = pending.register(&json!("1"));
        for message in [
            cancel(json!(true)),
            cancel(json!(1.0)),
            json!({"jsonrpc":"1.0","method":"notifications/cancelled","params":{"requestId":1}}),
            json!({"jsonrpc":"2.0","id":0,"method":"notifications/cancelled","params":{"requestId":1}}),
        ] {
            assert!(pending.cancel(&message));
        }
        assert!(!first.load(Ordering::Acquire));
        pending.cancel(&cancel(json!(1)));
        assert!(first.load(Ordering::Acquire));
        assert!(second.load(Ordering::Acquire));
        assert!(!string_id.load(Ordering::Acquire));
        pending.remove(&json!(1), &first);
        pending.remove(&json!(1), &second);
        pending.remove(&json!("1"), &string_id);
        assert!(pending.requests.is_empty());
        pending.cancel(&cancel(json!(1)));
        assert!(!pending.register(&json!(1)).load(Ordering::Acquire));
    }

    #[test]
    fn stdio_recovers_from_parse_utf8_and_frame_errors() {
        let fixture = Fixture::new();
        let mut bytes = b"{\n\xff\n[]\n".to_vec();
        bytes.extend(vec![b'x'; MAX_LINE_BYTES + 20]);
        bytes.push(b'\n');
        bytes.extend_from_slice(
            b"{\"jsonrpc\":\"1.0\",\"method\":\"notifications/cancelled\",\"id\":9}\n",
        );
        bytes.extend_from_slice(request("server/discover", json!({})).to_string().as_bytes());
        let mut output = Vec::new();
        serve_streams(fixture.service(), Cursor::new(bytes), &mut output).unwrap();
        let lines: Vec<Value> = String::from_utf8(output)
            .unwrap()
            .lines()
            .map(|line| serde_json::from_str(line).unwrap())
            .collect();
        assert_eq!(lines.len(), 5);
        for (line, code) in lines.iter().zip([-32700, -32700, -32600, -32700]) {
            assert_eq!(line["error"]["code"], code);
            assert!(line["id"].is_null());
        }
        assert_eq!(lines[4]["result"]["resultType"], "complete");
    }

    #[test]
    fn unexpected_sync_panic_is_a_sanitized_internal_error() {
        let fixture = Fixture::new();
        let response = fixture
            .server()
            .handle_message(
                request("tools/call", json!({"name":"update_dns_records"})),
                &|| panic!("private-provider-secret"),
            )
            .unwrap();
        assert_eq!(response, error_response(json!(1), -32603, "Internal error"));
    }

    #[cfg(unix)]
    #[test]
    fn reader_cancels_running_and_queued_syncs_before_publishing() {
        use std::io::Read;
        use std::time::{Duration, Instant};

        struct GatedInput {
            current: Cursor<Vec<u8>>,
            phase: u8,
            started: PathBuf,
            release: PathBuf,
        }
        impl Read for GatedInput {
            fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
                let available = self.fill_buf()?;
                let count = buffer.len().min(available.len());
                buffer[..count].copy_from_slice(&available[..count]);
                self.consume(count);
                Ok(count)
            }
        }
        impl BufRead for GatedInput {
            fn fill_buf(&mut self) -> io::Result<&[u8]> {
                if self.current.position() as usize == self.current.get_ref().len() {
                    let bytes = match self.phase {
                        0 => {
                            let deadline = Instant::now() + Duration::from_secs(5);
                            while !self.started.exists() {
                                if Instant::now() >= deadline {
                                    return Err(io::Error::new(
                                        io::ErrorKind::TimedOut,
                                        "sync did not start",
                                    ));
                                }
                                thread::sleep(Duration::from_millis(5));
                            }
                            let mut queued =
                                request("tools/call", json!({"name":"update_dns_records"}));
                            queued["id"] = json!(2);
                            format!("{}\n{}\n{}\n", queued,
                                json!({"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":1}}),
                                json!({"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":2}})).into_bytes()
                        }
                        1 => {
                            // Reaching this read proves both cancellation frames were consumed.
                            fs::write(&self.release, "release")?;
                            let mut status =
                                request("tools/call", json!({"name":"get_ddns_status"}));
                            status["id"] = json!(3);
                            format!("{}\n{}\n", status, request("server/discover", json!({})))
                                .into_bytes()
                        }
                        _ => Vec::new(),
                    };
                    self.phase = self.phase.saturating_add(1);
                    self.current = Cursor::new(bytes);
                }
                self.current.fill_buf()
            }
            fn consume(&mut self, amount: usize) {
                self.current.consume(amount);
            }
        }
        let fixture = Fixture::new();
        let started = fixture.0.join("started");
        let release = fixture.0.join("release");
        let quote =
            |path: &std::path::Path| format!("'{}'", path.to_string_lossy().replace('\'', "'\\''"));
        let rule = format!(
            "shell:touch {}; i=0; while [ ! -f {} ] && [ $i -lt 500 ]; do sleep 0.01; i=$((i+1)); done; echo 192.0.2.10",
            quote(&started),
            quote(&release)
        );
        fs::write(fixture.0.join("config.json"), json!({"cache":false, "providers":[{"provider":"debug","ipv4":["one.example.com","two.example.com"],"index4":rule,"index6":false}]}).to_string()).unwrap();
        let input = GatedInput {
            current: Cursor::new(
                format!(
                    "{}\n",
                    request("tools/call", json!({"name":"update_dns_records"}))
                )
                .into_bytes(),
            ),
            phase: 0,
            started,
            release,
        };
        let mut output = Vec::new();
        serve_streams(fixture.service(), input, &mut output).unwrap();
        let responses: Vec<Value> = String::from_utf8(output)
            .unwrap()
            .lines()
            .map(|line| serde_json::from_str(line).unwrap())
            .collect();
        assert_eq!(responses.len(), 2, "{responses:?}");
        assert_eq!(responses[0]["id"], 3);
        assert_eq!(
            responses[0]["result"]["structuredContent"]["records"],
            json!([])
        );
        assert_eq!(responses[1]["id"], 1);
        assert_eq!(responses[1]["result"]["resultType"], "complete");
    }
}

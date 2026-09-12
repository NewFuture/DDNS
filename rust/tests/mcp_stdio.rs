use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::{Duration, Instant};

use ddns_rs::mcp::{
    CLIENT_CAPABILITIES_KEY, LEGACY_PROTOCOL_VERSION, PROTOCOL_VERSION, PROTOCOL_VERSION_KEY,
};
use serde_json::{Value, json};

struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        static NEXT: AtomicUsize = AtomicUsize::new(0);
        let path = std::env::temp_dir().join(format!(
            "ddns-mcp-stdio-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        let fixture = Self(path);
        fixture.write_config();
        fixture
    }
    fn write_config(&self) {
        fs::write(self.0.join("config.json"), json!({
            "cache":false, "providers":[{"provider":"debug", "token":"test-private-provider-token", "ipv4":["one.example.com", "two.example.com"], "index4":"shell:echo 192.0.2.44", "index6":false}]
        }).to_string()).unwrap();
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

struct Process {
    child: Child,
    lines: Receiver<String>,
    stderr: Option<thread::JoinHandle<String>>,
}
impl Process {
    fn start(fixture: &Fixture) -> Self {
        let mut command = Command::new(env!("CARGO_BIN_EXE_ddns-rs"));
        for (key, _) in std::env::vars_os() {
            if key
                .to_string_lossy()
                .to_ascii_uppercase()
                .starts_with("DDNS_")
            {
                command.env_remove(key);
            }
        }
        let mut child = command
            .current_dir(&fixture.0)
            .args(["mcp", "--config", "config.json"])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        let stdout = child.stdout.take().unwrap();
        let (sender, lines) = mpsc::channel();
        thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                if sender.send(line.unwrap()).is_err() {
                    break;
                }
            }
        });
        let mut stderr = child.stderr.take().unwrap();
        let stderr = thread::spawn(move || {
            let mut text = String::new();
            stderr.read_to_string(&mut text).unwrap();
            text
        });
        Self {
            child,
            lines,
            stderr: Some(stderr),
        }
    }
    fn send(&mut self, message: Value) {
        self.raw(format!("{message}\n").as_bytes());
    }
    fn raw(&mut self, bytes: &[u8]) {
        let input = self.child.stdin.as_mut().unwrap();
        input.write_all(bytes).unwrap();
        input.flush().unwrap();
    }
    fn receive(&self) -> Value {
        let line = self
            .lines
            .recv_timeout(Duration::from_secs(10))
            .expect("MCP response timeout or unexpected stdout EOF");
        serde_json::from_str(&line)
            .unwrap_or_else(|error| panic!("non-JSON stdout: {line:?}: {error}"))
    }
    fn finish(mut self) -> String {
        self.child.stdin.take();
        let deadline = Instant::now() + Duration::from_secs(10);
        let status = loop {
            if let Some(status) = self.child.try_wait().unwrap() {
                break status;
            }
            assert!(Instant::now() < deadline, "MCP failed to exit on EOF");
            thread::sleep(Duration::from_millis(10));
        };
        let stderr = self.stderr.take().unwrap().join().unwrap();
        assert!(status.success(), "MCP exit {status}: {stderr}");
        assert!(
            self.lines.recv_timeout(Duration::from_secs(1)).is_err(),
            "unexpected extra stdout response"
        );
        stderr
    }
}
impl Drop for Process {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

fn request(id: Value, method: &str, mut params: Value) -> Value {
    params["_meta"] = json!({PROTOCOL_VERSION_KEY:PROTOCOL_VERSION, CLIENT_CAPABILITIES_KEY:{}, "io.modelcontextprotocol/clientInfo":{"name":"测试客户端", "version":"1"}});
    json!({"jsonrpc":"2.0", "id":id, "method":method, "params":params})
}
fn tool(id: i64, name: &str) -> Value {
    request(
        json!(id),
        "tools/call",
        json!({"name":name, "arguments":{}}),
    )
}
fn assert_status(response: &Value) {
    assert_eq!(response["result"]["isError"], false, "{response}");
    let status = &response["result"]["structuredContent"];
    let mut keys = status
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect::<Vec<_>>();
    keys.sort();
    assert_eq!(
        keys,
        [
            "addresses",
            "last_sync",
            "message",
            "providers",
            "records",
            "state"
        ]
    );
    assert_eq!(
        serde_json::from_str::<Value>(response["result"]["content"][0]["text"].as_str().unwrap())
            .unwrap(),
        *status
    );
    assert!(!response.to_string().contains("test-private-provider-token"));
}

#[test]
fn modern_stdio_discovery_full_sync_status_and_stdout_purity() {
    let fixture = Fixture::new();
    let mut process = Process::start(&fixture);
    process.send(request(json!("discover"), "server/discover", json!({})));
    let response = process.receive();
    assert_eq!(response["id"], "discover");
    assert_eq!(
        response["result"]["supportedVersions"],
        json!([PROTOCOL_VERSION, LEGACY_PROTOCOL_VERSION])
    );
    process.send(request(json!(2), "tools/list", json!({})));
    assert_eq!(
        process.receive()["result"]["tools"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    process.send(tool(3, "get_ddns_status"));
    assert_status(&process.receive());
    process.send(tool(4, "update_dns_records"));
    let response = process.receive();
    assert_status(&response);
    assert_eq!(response["result"]["structuredContent"]["state"], "synced");
    let records = response["result"]["structuredContent"]["records"]
        .as_array()
        .unwrap();
    assert_eq!(records.len(), 2);
    assert!(records.iter().all(|record| record["value"] == "192.0.2.44"));
    process.send(tool(5, "get_ddns_status"));
    assert_status(&process.receive());
    process.finish();
}

#[test]
fn legacy_stdio_initialization_gate_ping_and_sync() {
    let fixture = Fixture::new();
    let mut process = Process::start(&fixture);
    process.send(json!({"jsonrpc":"2.0","id":0,"method":"server/discover"}));
    assert_eq!(process.receive()["error"]["code"], -32601);
    process.send(json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":LEGACY_PROTOCOL_VERSION,"capabilities":{},"clientInfo":{"name":"copilot","version":"1"}}}));
    let response = process.receive();
    assert_eq!(
        response["result"]["protocolVersion"],
        LEGACY_PROTOCOL_VERSION
    );
    assert!(response["result"].get("resultType").is_none());
    process.send(json!({"jsonrpc":"2.0","id":2,"method":"tools/list"}));
    assert_eq!(process.receive()["error"]["code"], -32600);
    process.send(json!({"jsonrpc":"2.0","id":3,"method":"ping"}));
    assert_eq!(process.receive()["result"], json!({}));
    process.send(json!({"jsonrpc":"2.0","method":"notifications/initialized"}));
    process.send(json!({"jsonrpc":"2.0","id":4,"method":"tools/list"}));
    let response = process.receive();
    assert_eq!(response["id"], 4);
    assert!(response["result"].get("ttlMs").is_none());
    process.send(json!({"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"update_dns_records"}}));
    let response = process.receive();
    assert_status(&response);
    assert!(response["result"].get("resultType").is_none());
    process.finish();
}

#[test]
fn stdio_parse_errors_batches_invalid_ids_and_unknown_cancellation() {
    let fixture = Fixture::new();
    let mut process = Process::start(&fixture);
    process.raw(b"{\n\xff\n[]\n");
    for code in [-32700, -32700, -32600] {
        let response = process.receive();
        assert_eq!(response["error"]["code"], code);
        assert!(response["id"].is_null());
    }
    for id in [json!(null), json!(true), json!(1.5), json!({})] {
        process.send(request(id, "tools/list", json!({})));
        assert_eq!(process.receive()["error"]["code"], -32600);
    }
    process.send(
        json!({"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":42}}),
    );
    process.send(json!({"jsonrpc":"1.0","id":7,"method":"notifications/cancelled"}));
    process.send(
        json!({"jsonrpc":"2.0","method":"tools/call","params":{"name":"update_dns_records"}}),
    );
    process.send(request(json!(42), "server/discover", json!({})));
    assert_eq!(process.receive()["id"], 42);
    process.send(tool(43, "get_ddns_status"));
    let response = process.receive();
    assert_status(&response);
    assert!(
        response["result"]["structuredContent"]["records"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    process.finish();
}

#[test]
fn invalid_configuration_keeps_stdio_alive_and_is_repairable() {
    let fixture = Fixture::new();
    fs::write(fixture.0.join("config.json"), "not json").unwrap();
    let mut process = Process::start(&fixture);
    process.send(request(json!(1), "server/discover", json!({})));
    assert_eq!(process.receive()["result"]["resultType"], "complete");
    process.send(tool(2, "update_dns_records"));
    let response = process.receive();
    assert_eq!(response["result"]["isError"], true);
    assert!(response.get("error").is_none());
    fixture.write_config();
    process.send(tool(3, "update_dns_records"));
    assert_status(&process.receive());
    process.finish();
}

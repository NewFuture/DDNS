use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

use serde_json::{Value, json};

struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let mut random = [0; 8];
        getrandom::fill(&mut random).unwrap();
        let directory = std::env::temp_dir().join(format!(
            "ddns-server-cli-{}-{}",
            std::process::id(),
            u64::from_ne_bytes(random)
        ));
        fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn command(&self) -> Command {
        let mut command = Command::new(env!("CARGO_BIN_EXE_ddns-rs"));
        command.current_dir(&self.0);
        for (key, _) in std::env::vars_os() {
            let name = key.to_string_lossy().to_ascii_uppercase();
            if name.starts_with("DDNS_") || name == "PYTHONHTTPSVERIFY" {
                command.env_remove(key);
            }
        }
        command
    }
    fn write(&self, document: Value) {
        fs::write(self.0.join("config.json"), document.to_string()).unwrap();
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

struct Running(Child);
impl Running {
    fn start(mut command: Command) -> (Self, String) {
        let mut process = Self(
            command
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap(),
        );
        let stdout = process.0.stdout.take().unwrap();
        let (sender, receiver) = mpsc::channel();
        thread::spawn(move || {
            let mut line = String::new();
            let result = BufReader::new(stdout).read_line(&mut line);
            sender.send((result, line)).unwrap();
        });
        let (result, line) = receiver
            .recv_timeout(Duration::from_secs(5))
            .expect("server startup timeout");
        result.unwrap();
        assert!(!line.is_empty(), "server exited before announcing listener");
        (process, line)
    }
}
impl Drop for Running {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

fn get(address: &str, path: &str) -> (u16, Value) {
    let mut stream = TcpStream::connect(address).unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(3)))
        .unwrap();
    stream
        .write_all(format!("GET {path} HTTP/1.1\r\nHost: {address}\r\n\r\n").as_bytes())
        .unwrap();
    let mut response = String::new();
    stream.read_to_string(&mut response).unwrap();
    let status = response.split(' ').nth(1).unwrap().parse().unwrap();
    let body = response.split_once("\r\n\r\n").unwrap().1;
    (status, serde_json::from_str(body).unwrap())
}

#[test]
fn web_help_and_mcp_help_do_not_start_services() {
    let fixture = Fixture::new();
    for mode in ["web", "mcp"] {
        let output = fixture.command().args([mode, "--help"]).output().unwrap();
        assert!(output.status.success());
        assert!(
            String::from_utf8(output.stdout)
                .unwrap()
                .contains(&format!("Usage: ddns-rs {mode}"))
        );
    }
}

#[test]
fn starts_explicit_and_inferred_web_with_cli_interval_priority() {
    let fixture = Fixture::new();
    fixture.write(json!({"interval":7,"http":{"port":0},"providers":[]}));
    for args in [
        vec!["web", "-c", "config.json", "--interval", "9"],
        vec!["-c", "config.json", "--interval", "9"],
        vec!["-c", "config.json", "--port", "0"],
    ] {
        let mut command = fixture.command();
        command.args(&args);
        let (_process, line) = Running::start(command);
        assert!(line.starts_with("DDNS dashboard: http://"), "{line}");
        let address = line
            .split("http://")
            .nth(1)
            .unwrap()
            .split('/')
            .next()
            .unwrap();
        let (status, dashboard) = get(address, "/api/dashboard");
        assert_eq!(status, 200);
        assert_eq!(dashboard["scheduler"]["active"], true);
        assert_eq!(
            dashboard["scheduler"]["interval"],
            if args.contains(&"9") { 9 } else { 7 }
        );
    }
}

#[test]
fn starts_standalone_http_mcp_without_dashboard() {
    let fixture = Fixture::new();
    fixture.write(json!({"providers":[]}));
    let mut command = fixture.command();
    command.args([
        "mcp",
        "--transport",
        "http",
        "--port",
        "0",
        "-c",
        "config.json",
    ]);
    let (_process, line) = Running::start(command);
    assert!(line.starts_with("DDNS MCP HTTP: http://"));
    let address = line
        .split("http://")
        .nth(1)
        .unwrap()
        .split('/')
        .next()
        .unwrap();
    assert_eq!(get(address, "/api/config").0, 404);
    assert_eq!(get(address, "/mcp").0, 405);
}

#[test]
fn rejects_ambiguous_local_configs_and_insecure_bindings() {
    let fixture = Fixture::new();
    for args in [
        vec!["web", "--host", "0.0.0.0"],
        vec!["mcp", "--host", "127.0.0.1"],
        vec!["mcp", "-c", "https://example.com/config"],
        vec!["web", "-c", "first", "-c", "second"],
        vec!["--interval", "5", "--dns", "debug"],
        vec!["web", "--interval", "1441"],
        vec!["web", "--port", "65536"],
    ] {
        let output = fixture.command().args(&args).output().unwrap();
        assert_eq!(output.status.code(), Some(2), "{args:?}");
    }
    let output = fixture
        .command()
        .args(["mcp"])
        .env("DDNS_CONFIG", "['one.json','two.json']")
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
}

#[test]
fn malformed_file_remains_repairable_on_explicit_web_command() {
    let fixture = Fixture::new();
    fs::write(fixture.0.join("config.json"), "{ invalid JSON").unwrap();
    let mut command = fixture.command();
    command.args(["web", "-c", "config.json", "--port", "0"]);
    let (_process, line) = Running::start(command);
    let address = line
        .split("http://")
        .nth(1)
        .unwrap()
        .split('/')
        .next()
        .unwrap();
    let (status, config) = get(address, "/api/config");
    assert_eq!(status, 200);
    assert!(config["validation_error"].is_string());
    assert_eq!(config["raw"], "{ invalid JSON");
}

#[cfg(target_os = "linux")]
#[test]
fn browser_launcher_does_not_block_http_serving() {
    use std::os::unix::fs::PermissionsExt;
    use std::time::Instant;

    let fixture = Fixture::new();
    fixture.write(json!({"providers":[]}));
    // A local executable fixture avoids launching a user's real browser during tests.
    let launcher = fixture.0.join("xdg-open");
    fs::write(&launcher, "#!/bin/sh\nsleep 2\n").unwrap();
    fs::set_permissions(&launcher, fs::Permissions::from_mode(0o700)).unwrap();
    let mut command = fixture.command();
    let path = format!(
        "{}:{}",
        fixture.0.display(),
        std::env::var("PATH").unwrap_or_default()
    );
    command
        .env("PATH", path)
        .args(["web", "--port", "0", "--open"]);
    let (_process, line) = Running::start(command);
    let address = line
        .split("http://")
        .nth(1)
        .unwrap()
        .split('/')
        .next()
        .unwrap();
    let started = Instant::now();
    assert_eq!(get(address, "/api/dashboard").0, 200);
    assert!(started.elapsed() < Duration::from_secs(1));
}

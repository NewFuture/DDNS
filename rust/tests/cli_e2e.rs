use std::io::{Read, Write};
use std::net::TcpListener;
use std::process::Command;
use std::thread;
use std::time::Duration;

fn binary() -> &'static str {
    env!("CARGO_BIN_EXE_ddns-rs")
}

#[test]
fn runs_debug_provider_with_shell_address_rule() {
    let output = Command::new(binary())
        .args([
            "--dns",
            "debug",
            "--no-cache",
            "--index4",
            "shell:echo 192.0.2.44",
            "--ipv4",
            "test.example.com",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("[IPv4] 192.0.2.44"));
}

#[test]
fn reports_unsupported_modes_with_usage_exit_code() {
    let output = Command::new(binary()).arg("web").output().unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("not supported"));
}

#[test]
fn prints_help_and_version() {
    let help = Command::new(binary()).arg("--help").output().unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("Usage: ddns-rs"));

    let version = Command::new(binary()).arg("--version").output().unwrap();
    assert!(version.status.success());
    assert!(String::from_utf8_lossy(&version.stdout).contains("ddns-rs v"));
}

#[test]
fn generates_and_reuses_configuration() {
    let directory = std::env::temp_dir().join(format!(
        "ddns-rs-e2e-{}-config with spaces",
        std::process::id()
    ));
    std::fs::create_dir_all(&directory).unwrap();
    let path = directory.join("generated config.json");
    let generated = Command::new(binary())
        .args([
            "--dns",
            "debug",
            "--index4",
            "shell:echo 192.0.2.66",
            "--ipv4",
            "generated.example.com",
            "--new-config",
            path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        generated.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&generated.stderr)
    );
    let document: serde_json::Value =
        serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    assert_eq!(document["dns"], "debug");
    assert_eq!(
        document["ipv4"],
        serde_json::json!(["generated.example.com"])
    );

    let run = Command::new(binary())
        .args(["-c", path.to_str().unwrap(), "--no-cache"])
        .output()
        .unwrap();
    assert!(
        run.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&run.stderr)
    );
    assert!(String::from_utf8_lossy(&run.stdout).contains("[IPv4] 192.0.2.66"));
    let _ = std::fs::remove_dir_all(directory);
}

#[test]
fn applies_cli_over_environment_precedence() {
    let output = Command::new(binary())
        .env("DDNS_DNS", "debug")
        .env("DDNS_CACHE", "false")
        .env("DDNS_INDEX4", "shell:echo 192.0.2.77")
        .env("DDNS_IPV4", "env.example.com")
        .args(["--ipv4", "cli.example.com"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("cli.example.com"));
    assert!(!stderr.contains("env.example.com"));
}

#[test]
fn cache_skips_unchanged_provider_update() {
    let path = std::env::temp_dir().join(format!(
        "ddns-rs-e2e-cache-{}-{}.json",
        std::process::id(),
        "unchanged"
    ));
    let arguments = [
        "--dns",
        "debug",
        "--cache",
        path.to_str().unwrap(),
        "--index4",
        "shell:echo 192.0.2.88",
        "--ipv4",
        "cache.example.com",
    ];
    let first = Command::new(binary()).args(arguments).output().unwrap();
    assert!(first.status.success());
    assert!(String::from_utf8_lossy(&first.stdout).contains("[IPv4] 192.0.2.88"));

    let second = Command::new(binary()).args(arguments).output().unwrap();
    assert!(second.status.success());
    assert!(!String::from_utf8_lossy(&second.stdout).contains("[IPv4]"));
    assert!(String::from_utf8_lossy(&second.stderr).contains("is unchanged"));
    let _ = std::fs::remove_file(path);
}

#[test]
fn loads_remote_configuration_and_address_from_local_http() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let server = thread::spawn(move || {
        for _ in 0..2 {
            let (mut stream, _) = listener.accept().unwrap();
            stream
                .set_read_timeout(Some(Duration::from_secs(2)))
                .unwrap();
            let mut buffer = [0_u8; 4096];
            let count = stream.read(&mut buffer).unwrap();
            let request = String::from_utf8_lossy(&buffer[..count]);
            let path = request
                .lines()
                .next()
                .and_then(|line| line.split_whitespace().nth(1))
                .unwrap();
            let body = if path == "/config" {
                format!(
                    r#"{{
                        "dns": "debug",
                        "cache": false,
                        "proxy": ["DIRECT"],
                        "ssl": false,
                        "index4": ["url:http://{address}/ip"],
                        "ipv4": ["remote.example.com"]
                    }}"#
                )
            } else {
                "192.0.2.111".to_owned()
            };
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
                body.len()
            );
            stream.write_all(response.as_bytes()).unwrap();
        }
    });
    let output = Command::new(binary())
        .args([
            "-c",
            &format!("http://{address}/config"),
            "--proxy",
            "DIRECT",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("[IPv4] 192.0.2.111"));
    server.join().unwrap();
}

#[test]
fn rejects_empty_configuration_documents() {
    let path =
        std::env::temp_dir().join(format!("ddns-rs-empty-config-{}.json", std::process::id()));
    std::fs::write(&path, r#"{"providers":[]}"#).unwrap();
    let output = Command::new(binary())
        .args(["-c", path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("does not contain any provider entries")
    );
    let _ = std::fs::remove_file(path);
}

#[test]
fn empty_cli_config_list_suppresses_environment_config() {
    let output = Command::new(binary())
        .env("DDNS_CONFIG", "http://127.0.0.1:1/should-not-be-requested")
        .args([
            "--config",
            "--dns",
            "debug",
            "--no-cache",
            "--index4",
            "shell:echo 192.0.2.144",
            "--ipv4",
            "override.example.com",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("[IPv4] 192.0.2.144"));
}

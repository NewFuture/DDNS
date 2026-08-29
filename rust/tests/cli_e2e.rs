use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

fn binary() -> &'static str {
    env!("CARGO_BIN_EXE_ddns-rs")
}

fn command() -> Command {
    let mut command = Command::new(binary());
    for (key, _) in std::env::vars_os() {
        let key_text = key.to_string_lossy();
        if key_text.to_ascii_uppercase().starts_with("DDNS_")
            || key_text.eq_ignore_ascii_case("PYTHONHTTPSVERIFY")
        {
            command.env_remove(key);
        }
    }
    command
}

fn accept_with_timeout(listener: &TcpListener) -> TcpStream {
    listener.set_nonblocking(true).unwrap();
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        match listener.accept() {
            Ok((stream, _)) => return stream,
            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                assert!(
                    Instant::now() < deadline,
                    "timed out waiting for HTTP request"
                );
                thread::sleep(Duration::from_millis(10));
            }
            Err(error) => panic!("failed to accept HTTP request: {error}"),
        }
    }
}

fn read_http_request(stream: &mut impl Read) -> String {
    let mut request = Vec::new();
    let mut buffer = [0_u8; 4096];
    loop {
        let count = stream.read(&mut buffer).unwrap();
        if count == 0 {
            break;
        }
        request.extend_from_slice(&buffer[..count]);
        let Some(header_end) = request.windows(4).position(|window| window == b"\r\n\r\n") else {
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
    String::from_utf8_lossy(&request).into_owned()
}

#[test]
fn runs_debug_provider_with_shell_address_rule() {
    let output = command()
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
fn runs_dual_stack_update() {
    let output = command()
        .args([
            "--dns",
            "debug",
            "--no-cache",
            "--index4",
            "shell:echo 192.0.2.45",
            "--index6",
            "shell:echo 2001:db8::45",
            "--ipv4",
            "v4.example.com",
            "--ipv6",
            "v6.example.com",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("[IPv4] 192.0.2.45"));
    assert!(stdout.contains("[IPv6] 2001:db8::45"));
}

#[test]
fn reports_unsupported_modes_with_usage_exit_code() {
    let output = command().arg("web").output().unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("not supported"));
}

#[test]
fn prints_help_and_version() {
    let help = command().arg("--help").output().unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("Usage: ddns-rs"));

    let version = command().arg("--version").output().unwrap();
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
    let generated = command()
        .args([
            "--dns",
            "debug",
            "--endpoint",
            "http://127.0.0.1:9",
            "--extra.proxied",
            "--extra.comment",
            "generated config",
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
    assert_eq!(document["endpoint"], "http://127.0.0.1:9");
    assert_eq!(document["extra"]["proxied"], true);
    assert_eq!(document["extra"]["comment"], "generated config");
    assert_eq!(document["ttl"], 600);
    assert_eq!(
        document["ipv4"],
        serde_json::json!(["generated.example.com"])
    );

    let run = command()
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
    let output = command()
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
    let directory = std::env::temp_dir().join(format!("ddns-rs-e2e-cache-{}", std::process::id()));
    std::fs::create_dir_all(&directory).unwrap();
    let path = directory.join("cache.json");
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
    let first = command().args(arguments).output().unwrap();
    assert!(first.status.success());
    assert!(String::from_utf8_lossy(&first.stdout).contains("[IPv4] 192.0.2.88"));

    let second = command().args(arguments).output().unwrap();
    assert!(second.status.success());
    assert!(!String::from_utf8_lossy(&second.stdout).contains("[IPv4]"));
    assert!(String::from_utf8_lossy(&second.stderr).contains("is unchanged"));
    let _ = std::fs::remove_dir_all(directory);
}

#[test]
fn no_cache_does_not_deduplicate_updates() {
    let output = command()
        .args([
            "--dns",
            "debug",
            "--no-cache",
            "--index4",
            "shell:echo 192.0.2.89",
            "--ipv4",
            "duplicate.example.com",
            "duplicate.example.com",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8_lossy(&output.stdout)
            .matches("[IPv4]")
            .count(),
        2
    );
}

#[test]
fn loads_remote_configuration_and_address_from_local_http() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let server = thread::spawn(move || {
        for _ in 0..2 {
            let mut stream = accept_with_timeout(&listener);
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
    let output = command()
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
    let output = command()
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
    let output = command()
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

#[test]
fn log_file_failure_does_not_skip_later_configurations() {
    let directory =
        std::env::temp_dir().join(format!("ddns-rs-log-failure-{}", std::process::id()));
    std::fs::create_dir_all(&directory).unwrap();
    let config_path = directory.join("multi.json");
    let document = serde_json::json!({
        "cache": false,
        "providers": [
            {
                "provider": "debug",
                "index4": ["shell:echo 192.0.2.151"],
                "ipv4": ["first.example.com"],
                "log": {"file": directory}
            },
            {
                "provider": "debug",
                "index4": ["shell:echo 192.0.2.152"],
                "ipv4": ["second.example.com"]
            }
        ]
    });
    std::fs::write(&config_path, serde_json::to_vec(&document).unwrap()).unwrap();

    let output = command()
        .args(["-c", config_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert_eq!(
        String::from_utf8_lossy(&output.stdout)
            .matches("[IPv4]")
            .count(),
        2
    );
    assert!(String::from_utf8_lossy(&output.stderr).contains("log setup"));
    let _ = std::fs::remove_dir_all(directory);
}

#[test]
fn provider_failure_continues_across_jsonc_and_python_configs() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let server = thread::spawn(move || {
        let mut stream = accept_with_timeout(&listener);
        stream
            .set_read_timeout(Some(Duration::from_secs(2)))
            .unwrap();
        let request = read_http_request(&mut stream);
        let body = "provider rejected e2e-secret";
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        );
        stream.write_all(response.as_bytes()).unwrap();
        request
    });

    let directory =
        std::env::temp_dir().join(format!("ddns-rs-e2e-formats-{}", std::process::id()));
    std::fs::create_dir_all(&directory).unwrap();
    let jsonc_path = directory.join("providers.jsonc");
    let python_path = directory.join("legacy.conf");
    std::fs::write(
        &jsonc_path,
        format!(
            r#"{{
                // A failed provider must not stop later configurations.
                "cache": false,
                "proxy": ["DIRECT"],
                "ssl": false,
                "providers": [
                    {{
                        "provider": "he",
                        "token": "e2e-secret",
                        "endpoint": "http://{address}",
                        "index4": ["shell:echo 192.0.2.201"],
                        "ipv4": ["failed.example.com"]
                    }},
                    {{
                        "provider": "debug",
                        "index4": ["shell:echo 192.0.2.202"],
                        "ipv4": ["jsonc.example.com"]
                    }}
                ]
            }}"#
        ),
    )
    .unwrap();
    std::fs::write(
        &python_path,
        "{'dns': 'debug', 'cache': False, 'index4': ['shell:echo 192.0.2.203'], 'ipv4': ['python.example.com']}",
    )
    .unwrap();

    let output = command()
        .args([
            "-c",
            jsonc_path.to_str().unwrap(),
            python_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    let request = server.join().unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert_eq!(output.status.code(), Some(1));
    assert!(request.contains("password=e2e-secret"));
    assert!(stdout.contains("[IPv4] 192.0.2.202"));
    assert!(stdout.contains("[IPv4] 192.0.2.203"));
    assert!(stderr.contains("update operation(s) failed"));
    assert!(!stderr.contains("e2e-secret"));
    let _ = std::fs::remove_dir_all(directory);
}

use std::fs;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, mpsc};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use ddns_rs::dashboard::DashboardService;
use serde_json::{Value, json};

struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        static NEXT: AtomicUsize = AtomicUsize::new(0);
        let path = std::env::temp_dir().join(format!(
            "ddns-dashboard-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn service(&self) -> DashboardService {
        DashboardService::new(Some(self.0.join("config.json")), 5).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn document() -> Value {
    json!({"cache": false, "log": {"level": "CRITICAL"}, "providers": [{"provider": "debug", "ipv4": ["test.example.com"], "index4": ["shell:echo 192.0.2.10"], "index6": false}]})
}

#[test]
fn repairs_missing_and_invalid_config_and_swaps_backup() {
    let fixture = Fixture::new();
    let service = fixture.service();
    assert_eq!(service.config_state().unwrap()["exists"], false);
    fs::write(service.config_path(), "not json secret-token").unwrap();
    let state = service.config_state().unwrap();
    assert!(state.get("validation_error").is_some());
    assert_eq!(state["raw"], "not json secret-token");
    assert!(
        !service
            .dashboard()
            .unwrap()
            .to_string()
            .contains("secret-token")
    );
    service.save(document()).unwrap();
    assert!(service.restore_backup().is_err());
    let mut second = document();
    second["interval"] = json!(12);
    service.save(second).unwrap();
    assert_eq!(
        service.restore_backup().unwrap()["config"].get("interval"),
        None
    );
    assert_eq!(service.restore_backup().unwrap()["config"]["interval"], 12);
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        for path in [
            service.config_path().to_path_buf(),
            fixture.0.join("config.json.bak"),
        ] {
            assert_eq!(
                fs::metadata(path).unwrap().permissions().mode() & 0o777,
                0o600
            );
        }
    }
}

#[test]
fn normalizes_legacy_preserves_sparse_fields_and_scopes_metadata() {
    let fixture = Fixture::new();
    let service = fixture.service();
    let value = service.validate(json!({"dns":"DEBUG", "id":"account", "token":"secret", "http":{"token":"http-secret"}, "interval":10, "log_level":"INFO", "extra_region":"west", "custom":42})).unwrap();
    assert_eq!(value["providers"][0]["provider"], "debug");
    assert_eq!(
        value["providers"][0]["extra"],
        json!({"region":"west", "custom":42})
    );
    assert!(value["providers"][0].get("http").is_none());
    assert!(value["providers"][0].get("interval").is_none());
    assert!(value["providers"][0].get("index4").is_none());
    assert_eq!(value["log"], json!({"level":"INFO"}));
    let sparse = json!({"providers":[{"provider":"debug"}]});
    let validated = service.validate(sparse).unwrap();
    let configs = ddns_rs::config::from_document(
        validated,
        &std::collections::BTreeMap::from([
            ("token".into(), json!("environment-secret")),
            ("ipv4".into(), json!(["env.example.com"])),
        ]),
    )
    .unwrap();
    assert_eq!(configs[0].token, "environment-secret");
    assert_eq!(configs[0].ipv4, ["env.example.com"]);
    for invalid in [
        json!({"providers":[{"provider":"debug","http":{}}]}),
        json!({"providers":[], "interval":0}),
        json!({"providers":[{"provider":"debug","extra":{"domain":"override"}}]}),
        json!({"providers":[{"provider":"debug","ipv4":["not a domain"]}]}),
    ] {
        assert!(service.validate(invalid).is_err());
    }
}

#[test]
fn debug_sync_retains_cache_disabled_records_and_redacts_status() {
    fn send_sync<T: Send + Sync>() {}
    send_sync::<DashboardService>();
    let fixture = Fixture::new();
    let service = fixture.service();
    let mut value = document();
    value["providers"][0]["token"] = json!("private-token");
    value["http"] = json!({"token":"private-http-token"});
    service.save(value).unwrap();
    let state = service.sync("private-token", &|| false).unwrap();
    assert_eq!(state["state"], "synced");
    assert_eq!(state["providers"][0]["status"], "synced");
    assert_eq!(state["records"][0]["value"], "192.0.2.10");
    assert!(!state.to_string().contains("private-token"));
    assert!(!state.to_string().contains("private-http-token"));
}

#[test]
fn cancellation_stops_before_and_between_domains() {
    let fixture = Fixture::new();
    let service = fixture.service();
    let mut value = document();
    value["providers"][0]["ipv4"] = json!(["one.example.com", "two.example.com"]);
    service.save(value).unwrap();
    assert_eq!(
        service.sync("test", &|| true).unwrap_err().code,
        "cancelled"
    );
    let count = AtomicUsize::new(0);
    let result = service.sync("test", &|| count.fetch_add(1, Ordering::SeqCst) >= 3);
    assert!(result.is_err());
    assert!(
        service.dashboard().unwrap()["records"]
            .as_array()
            .unwrap()
            .len()
            <= 1
    );
}

#[test]
fn duplicate_provider_failure_is_indexed_and_loopback_ip_is_real() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut buf = [0; 4096];
        let _ = stream.read(&mut buf).unwrap();
        stream
            .write_all(
                b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\nConnection: close\r\n\r\n192.0.2.20",
            )
            .unwrap();
    });
    let fixture = Fixture::new();
    let service = fixture.service();
    let mut value = document();
    value["providers"][0]["index4"] = json!([format!("url:http://{address}/ip")]);
    let mut second = value["providers"][0].clone();
    second["index4"] = json!(["shell:echo no-address"]);
    value["providers"].as_array_mut().unwrap().push(second);
    service.save(value).unwrap();
    assert!(service.sync("test", &|| false).is_err());
    server.join().unwrap();
    let state = service.dashboard().unwrap();
    assert_eq!(state["providers"][0]["status"], "synced");
    assert_eq!(state["providers"][1]["status"], "error");
    assert_eq!(state["records"][0]["value"], "192.0.2.20");
}

#[test]
fn reads_actual_cache_scoped_to_configured_domains() {
    let fixture = Fixture::new();
    let service = fixture.service();
    let mut value = document();
    value["cache"] = json!(fixture.0.join("cache"));
    service.save(value).unwrap();
    service.sync("test", &|| false).unwrap();
    let reopened = fixture.service();
    let dashboard = reopened.dashboard().unwrap();
    assert_eq!(dashboard["records"][0]["value"], "192.0.2.10");
    assert!(dashboard["records"][0]["updated"].as_f64().is_some());
    assert_eq!(dashboard["last_sync"], dashboard["records"][0]["updated"]);
}

#[test]
fn scheduler_is_opt_in_configurable_and_stops_on_drop() {
    let fixture = Fixture::new();
    let service = Arc::new(fixture.service());
    assert_eq!(service.dashboard().unwrap()["scheduler"]["active"], false);
    assert!(service.configure_scheduler("takeover", "web", 5).is_err());
    assert!(service.configure_scheduler("enable", "cron", 5).is_err());
    assert!(service.configure_scheduler("configure", "web", 0).is_err());
    let handle = service.start_scheduler();
    assert_eq!(
        service.configure_scheduler("disable", "web", 1).unwrap()["enabled"],
        false
    );
    assert_eq!(
        service.configure_scheduler("enable", "web", 2).unwrap()["interval"],
        2
    );
    assert_eq!(service.dashboard().unwrap()["last_sync"], Value::Null);
    drop(handle);
    assert_eq!(service.dashboard().unwrap()["scheduler"]["active"], false);
}

#[cfg(unix)]
#[test]
fn save_and_restore_preserve_symlink_target() {
    use std::os::unix::fs::symlink;
    let fixture = Fixture::new();
    let target = fixture.0.join("real.json");
    fs::write(&target, "{'dns':'debug'}").unwrap();
    symlink("real.json", fixture.0.join("config.json")).unwrap();
    let service = fixture.service();
    service.save(document()).unwrap();
    assert!(
        fs::symlink_metadata(service.config_path())
            .unwrap()
            .file_type()
            .is_symlink()
    );
    assert!(fixture.0.join("real.json.bak").exists());
    service.restore_backup().unwrap();
    assert_eq!(fs::read_to_string(target).unwrap(), "{'dns':'debug'}");
}

#[test]
fn mutation_waits_for_real_callback_sync_without_deadlocking() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let address = listener.local_addr().unwrap();
    let (started, received) = mpsc::channel();
    let (release, released) = mpsc::channel();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut request = Vec::new();
        let mut buffer = [0; 4096];
        while !request.windows(4).any(|window| window == b"\r\n\r\n") {
            let count = stream.read(&mut buffer).unwrap();
            assert!(count > 0, "callback request ended before its headers");
            request.extend_from_slice(&buffer[..count]);
            assert!(
                request.len() <= 64 * 1024,
                "callback request headers are too large"
            );
        }
        started.send(()).unwrap();
        released.recv_timeout(Duration::from_secs(5)).unwrap();
        stream
            .write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK")
            .unwrap();
    });
    let fixture = Fixture::new();
    let service = Arc::new(fixture.service());
    let mut value = document();
    value["providers"][0]["provider"] = json!("callback");
    value["providers"][0]["id"] = json!(format!("http://{address}/update?secret=hidden"));
    service.save(value).unwrap();
    let updater = service.clone();
    let sync = thread::spawn(move || updater.sync("mcp", &|| false));
    received.recv_timeout(Duration::from_secs(5)).unwrap();
    let writer = service.clone();
    let (saved, done) = mpsc::channel();
    let write = thread::spawn(move || {
        let result = writer.save(document());
        saved.send(()).unwrap();
        result
    });
    assert!(done.recv_timeout(Duration::from_millis(30)).is_err());
    release.send(()).unwrap();
    let status = sync.join().unwrap().unwrap();
    assert_eq!(status["records"].as_array().unwrap().len(), 1);
    assert!(!status.to_string().contains("hidden"));
    write.join().unwrap().unwrap();
    server.join().unwrap();
    assert_eq!(service.dashboard().unwrap()["providers"][0]["id"], "debug");
}

#[test]
fn canonical_validation_rejects_duplicates_and_invalid_metadata() {
    let fixture = Fixture::new();
    let service = fixture.service();
    for invalid in [
        json!({"providers":[{"provider":"debug","ipv4":["UPPER.example.com","upper.example.com"]}]}),
        json!({"providers":[{"provider":"debug","extra_domain":"override"}]}),
        json!({"providers":[{"provider":"debug","index4":["url:http://"]}]}),
        json!({"providers":[],"http":{"host":"127.0.0.1@evil"}}),
        json!({"providers":[],"http":{"origins":["http://example.com/path"]}}),
    ] {
        assert!(service.validate(invalid).is_err());
    }
    let value = service.validate(json!({"providers":[{"provider":"debug","ipv4":["UPPER.example.com"],"index6":[],"ttl":"60"}]})).unwrap();
    assert_eq!(value["providers"][0]["ipv4"], json!(["upper.example.com"]));
    assert_eq!(value["providers"][0]["index6"], false);
    assert_eq!(value["providers"][0]["ttl"], 60);
}

#[test]
fn constructor_interval_wins_and_sparse_http_is_normalized() {
    let fixture = Fixture::new();
    fs::write(
        fixture.0.join("config.json"),
        r#"{"interval":12,"providers":[]}"#,
    )
    .unwrap();
    let service = DashboardService::new(Some(fixture.0.join("config.json")), 3).unwrap();
    assert_eq!(service.dashboard().unwrap()["scheduler"]["interval"], 3);
    let value = service
        .validate(json!({"providers":[],"http":{"origins":["HTTPS://CLIENT.example:443/"]}}))
        .unwrap();
    assert_eq!(value["http"], json!({"origins":["https://client.example"]}));
    assert_eq!(
        service
            .validate(json!({"providers":{},"token":"hidden"}))
            .unwrap_err()
            .code,
        "invalid_config"
    );
    service.save(json!({"interval":8,"providers":[]})).unwrap();
    assert_eq!(service.dashboard().unwrap()["scheduler"]["interval"], 8);
    service.restore_backup().unwrap();
    assert_eq!(service.dashboard().unwrap()["scheduler"]["interval"], 12);
}

#[test]
fn restores_backup_when_current_file_is_missing() {
    let fixture = Fixture::new();
    let service = fixture.service();
    fs::write(fixture.0.join("config.json.bak"), r#"{"dns":"debug"}"#).unwrap();
    assert!(
        service.restore_backup().unwrap()["exists"]
            .as_bool()
            .unwrap()
    );
    assert!(fixture.0.join("config.json.bak").is_file());
}

#[test]
fn rejects_direct_reserved_record_overrides() {
    let fixture = Fixture::new();
    let service = fixture.service();
    for key in ["domain", "value", "record_type"] {
        let mut global = json!({"providers": [{"provider": "debug"}]});
        global[key] = json!("override");
        assert!(service.validate(global).is_err());
        let mut provider = json!({"providers": [{"provider": "debug"}]});
        provider["providers"][0][key] = json!("override");
        assert!(service.validate(provider).is_err());
    }
}

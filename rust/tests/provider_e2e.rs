use std::collections::{BTreeMap, VecDeque};
use std::path::Path;
use std::sync::{Arc, Mutex};

use ddns_rs::config::{AddressRules, CacheSetting, Config, LogConfig, TlsMode};
use ddns_rs::error::{Error, Result};
use ddns_rs::http::{HttpClient, HttpRequest, HttpResponse, Method};
use ddns_rs::logging::{Level, Logger};
use ddns_rs::provider::{RecordRequest, build};
use serde_json::{Value, json};

#[derive(Default)]
struct FakeHttpClient {
    responses: Mutex<VecDeque<HttpResponse>>,
    requests: Mutex<Vec<HttpRequest>>,
}

impl FakeHttpClient {
    fn with_json(responses: impl IntoIterator<Item = Value>) -> Arc<Self> {
        Arc::new(Self {
            responses: Mutex::new(
                responses
                    .into_iter()
                    .map(|body| HttpResponse {
                        status: 200,
                        reason: "OK".to_owned(),
                        headers: BTreeMap::new(),
                        body: body.to_string(),
                    })
                    .collect(),
            ),
            requests: Mutex::new(Vec::new()),
        })
    }

    fn requests(&self) -> Vec<HttpRequest> {
        self.requests.lock().unwrap().clone()
    }
}

impl HttpClient for FakeHttpClient {
    fn execute(&self, request: &HttpRequest) -> Result<HttpResponse> {
        self.requests.lock().unwrap().push(request.clone());
        self.responses
            .lock()
            .unwrap()
            .pop_front()
            .ok_or_else(|| Error::Http("fake response queue is empty".to_owned()))
    }
}

fn config(provider: &str, id: &str, token: &str) -> Config {
    Config {
        provider: provider.to_owned(),
        id: id.to_owned(),
        token: token.to_owned(),
        endpoint: Some("http://mock.local".to_owned()),
        index4: AddressRules::Disabled,
        index6: AddressRules::Disabled,
        ipv4: Vec::new(),
        ipv6: Vec::new(),
        ttl: Some(300),
        line: None,
        proxies: vec!["DIRECT".to_owned()],
        cache: CacheSetting::Disabled,
        cache_max_age: 3600,
        tls: TlsMode::Insecure,
        log: LogConfig {
            level: Level::Critical,
            file: None,
            format: None,
            date_format: None,
        },
        extra: BTreeMap::new(),
        debug: false,
    }
}

fn logger(token: &str) -> Logger {
    Logger::new(Level::Critical, None::<&Path>, vec![token.to_owned()]).unwrap()
}

fn request(address: &str) -> RecordRequest {
    RecordRequest {
        domain: "www.example.com".to_owned(),
        address: address.to_owned(),
        record_type: "A".to_owned(),
        ttl: Some(300),
        line: None,
        extra: BTreeMap::new(),
    }
}

#[test]
fn cloudflare_create_and_update_flows() {
    let token = "cloudflare-secret";
    let create_client = FakeHttpClient::with_json([
        json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
        json!({"success": true, "result": []}),
        json!({"success": true, "result": {"id": "record-1"}}),
    ]);
    let client: Arc<dyn HttpClient> = create_client.clone();
    let mut provider = build(&config("cloudflare", "", token), client, logger(token)).unwrap();
    provider.set_record(&request("192.0.2.10")).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert_eq!(requests[2].method, Method::Post);
    assert_eq!(
        requests[0].headers["authorization"],
        format!("Bearer {token}")
    );
    let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["name"], "www.example.com");
    assert_eq!(body["content"], "192.0.2.10");
    assert_eq!(
        body["comment"],
        "Managed by [DDNS](https://ddns.newfuture.cc)"
    );

    let update_client = FakeHttpClient::with_json([
        json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
        json!({"success": true, "result": [{
            "id": "record-1",
            "name": "www.example.com",
            "type": "A",
            "content": "192.0.2.10",
            "proxied": true
        }]}),
        json!({"success": true, "result": {"id": "record-1"}}),
    ]);
    let client: Arc<dyn HttpClient> = update_client.clone();
    let mut provider = build(&config("cloudflare", "", token), client, logger(token)).unwrap();
    provider.set_record(&request("192.0.2.11")).unwrap();
    let requests = update_client.requests();
    assert_eq!(requests[2].method, Method::Put);
    let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["content"], "192.0.2.11");
    assert_eq!(body["proxied"], true);
}

#[test]
fn alidns_create_and_unchanged_update_flows() {
    let token = "ali-secret";
    let create_client = FakeHttpClient::with_json([
        json!({"DomainName": "example.com", "RR": "www"}),
        json!({"DomainRecords": {"Record": []}}),
        json!({"RecordId": "record-1"}),
    ]);
    let client: Arc<dyn HttpClient> = create_client.clone();
    let mut provider = build(
        &config("alidns", "access-key", token),
        client,
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.20")).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert_eq!(requests[0].headers["x-acs-action"], "GetMainDomainName");
    assert_eq!(requests[2].headers["x-acs-action"], "AddDomainRecord");
    assert!(
        requests[2].headers["authorization"].starts_with("ACS3-HMAC-SHA256 Credential=access-key,")
    );
    assert!(
        requests[2]
            .body
            .as_deref()
            .unwrap()
            .contains("Value=192.0.2.20")
    );

    let unchanged_client = FakeHttpClient::with_json([
        json!({"DomainName": "example.com", "RR": "www"}),
        json!({"DomainRecords": {"Record": [{
            "RecordId": "record-1",
            "RR": "www",
            "DomainName": "example.com",
            "Value": "192.0.2.20",
            "Type": "A",
            "TTL": 300
        }]}}),
    ]);
    let client: Arc<dyn HttpClient> = unchanged_client.clone();
    let mut provider = build(
        &config("alidns", "access-key", token),
        client,
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.20")).unwrap();
    assert_eq!(unchanged_client.requests().len(), 2);
}

#[test]
fn dnspod_create_and_update_flows() {
    let token = "dnspod-secret";
    let create_client = FakeHttpClient::with_json([
        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
        json!({"status": {"code": "1"}, "records": []}),
        json!({"status": {"code": "1"}, "record": {"id": "record-1"}}),
    ]);
    let client: Arc<dyn HttpClient> = create_client.clone();
    let mut provider = build(&config("dnspod", "12345", token), client, logger(token)).unwrap();
    provider.set_record(&request("192.0.2.30")).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert!(requests[0].url.ends_with("/Domain.Info"));
    assert!(requests[2].url.ends_with("/Record.Create"));
    let body = requests[2].body.as_deref().unwrap();
    assert!(body.contains("login_token=12345%2Cdnspod-secret"));
    assert!(body.contains("record_line=%E9%BB%98%E8%AE%A4"));

    let update_client = FakeHttpClient::with_json([
        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
        json!({"status": {"code": "1"}, "records": [{
            "id": "record-1",
            "name": "www",
            "line": "Default"
        }]}),
        json!({"status": {"code": "1"}, "record": {"id": "record-1"}}),
    ]);
    let client: Arc<dyn HttpClient> = update_client.clone();
    let mut provider = build(&config("dnspod", "12345", token), client, logger(token)).unwrap();
    provider.set_record(&request("192.0.2.31")).unwrap();
    let requests = update_client.requests();
    assert!(requests[2].url.ends_with("/Record.Modify"));
    assert!(
        requests[2]
            .body
            .as_deref()
            .unwrap()
            .contains("record_line=default")
    );
    assert!(requests[2].body.as_deref().unwrap().contains("ttl=300"));
}

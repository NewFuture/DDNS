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
    fn responses(values: impl IntoIterator<Item = (u16, Value)>) -> Arc<Self> {
        Arc::new(Self {
            responses: Mutex::new(
                values
                    .into_iter()
                    .map(|(status, body)| HttpResponse {
                        status,
                        reason: if status < 300 { "OK" } else { "Error" }.to_owned(),
                        headers: BTreeMap::new(),
                        body: body.to_string(),
                    })
                    .collect(),
            ),
            requests: Mutex::new(Vec::new()),
        })
    }

    fn text<'a>(values: impl IntoIterator<Item = (u16, &'a str)>) -> Arc<Self> {
        Arc::new(Self {
            responses: Mutex::new(
                values
                    .into_iter()
                    .map(|(status, body)| HttpResponse {
                        status,
                        reason: if status < 300 { "OK" } else { "Error" }.to_owned(),
                        headers: BTreeMap::new(),
                        body: body.to_owned(),
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

fn request() -> RecordRequest {
    RecordRequest {
        domain: "www.example.com".to_owned(),
        address: "192.0.2.45".to_owned(),
        record_type: "A".to_owned(),
        ttl: Some(300),
        line: None,
        extra: BTreeMap::new(),
    }
}

fn run(provider: &str, id: &str, token: &str, client: Arc<FakeHttpClient>) -> Result<()> {
    run_request(provider, id, token, client, request())
}

fn run_request(
    provider: &str,
    id: &str,
    token: &str,
    client: Arc<FakeHttpClient>,
    request: RecordRequest,
) -> Result<()> {
    let client_for_provider: Arc<dyn HttpClient> = client;
    let mut provider = build(
        &config(provider, id, token),
        client_for_provider,
        logger(token),
    )?;
    provider.set_record(&request)
}

#[test]
fn aliases_build_their_canonical_provider() {
    for (alias, id, token, canonical) in [
        ("dnspod_cn", "id", "token", "dnspod"),
        ("aliyun", "id", "token", "alidns"),
        ("print", "", "", "debug"),
        ("dnspod_global", "id", "token", "dnspod_com"),
        ("tencent", "id", "token", "tencentcloud"),
        ("qcloud", "id", "token", "tencentcloud"),
        ("edgeone_acc", "id", "token", "edgeone"),
        ("teo_acc", "id", "token", "edgeone"),
        ("teo", "id", "token", "edgeone"),
        ("teo_dns", "id", "token", "edgeone_dns"),
        ("edgeone_noacc", "id", "token", "edgeone_dns"),
        ("esa", "id", "token", "aliesa"),
        ("51dns", "id", "token", "dnscom"),
        ("dns_com", "id", "token", "dnscom"),
        ("he_net", "", "token", "he"),
        ("huawei", "id", "token", "huaweidns"),
        ("huaweicloud", "id", "token", "huaweidns"),
        ("namesilo_com", "", "token", "namesilo"),
        ("no-ip", "id", "token", "noip"),
        ("noip_com", "id", "token", "noip"),
        ("webhook", "http://mock.local/callback", "", "callback"),
        ("http", "http://mock.local/callback", "", "callback"),
        ("west_cn", "id", "token", "west"),
        ("35cn", "id", "token", "west"),
    ] {
        let client: Arc<dyn HttpClient> = Arc::new(FakeHttpClient::default());
        assert_eq!(
            build(&config(alias, id, token), client, logger(token))
                .unwrap()
                .name(),
            canonical,
            "{alias}"
        );
    }
}

#[test]
fn dnspod_com_create_and_error_are_offline() {
    let success = FakeHttpClient::responses([
        (200, json!({"status":{"code":"1"},"domain":{"id":"zone"}})),
        (200, json!({"status":{"code":"10"},"records":[]})),
        (200, json!({"status":{"code":"1"},"record":{"id":"record"}})),
    ]);
    run("dnspod_com", "id", "secret", success.clone()).unwrap();
    assert!(success.requests()[2].url.ends_with("/Record.Create"));
    let failure =
        FakeHttpClient::responses([(200, json!({"status":{"code":"-1","message":"bad"}}))]);
    assert!(run("dnspod_com", "id", "secret", failure).is_err());
}

#[test]
fn tencent_and_edgeone_create_and_errors_are_offline() {
    let tencent = FakeHttpClient::responses([
        (200, json!({"Response":{"DomainInfo":{"DomainId":7}}})),
        (200, json!({"Response":{"RecordList":[]}})),
        (200, json!({"Response":{"RecordId":8}})),
    ]);
    run("tencentcloud", "id", "secret", tencent.clone()).unwrap();
    assert_eq!(tencent.requests()[2].headers["x-tc-action"], "CreateRecord");
    let edgeone = FakeHttpClient::responses([
        (
            200,
            json!({"Response":{"Zones":[{"ZoneId":"zone","ZoneName":"example.com"}]}}),
        ),
        (200, json!({"Response":{"AccelerationDomains":[]}})),
        (200, json!({"Response":{"RequestId":"request"}})),
    ]);
    run("edgeone", "id", "secret", edgeone.clone()).unwrap();
    assert_eq!(
        edgeone.requests()[2].headers["x-tc-action"],
        "CreateAccelerationDomain"
    );
    let edgeone_dns = FakeHttpClient::responses([
        (
            200,
            json!({"Response":{"Zones":[{"ZoneId":"zone","ZoneName":"example.com"}]}}),
        ),
        (200, json!({"Response":{"DnsRecords":[]}})),
        (200, json!({"Response":{"RequestId":"request"}})),
    ]);
    run("edgeone_dns", "id", "secret", edgeone_dns.clone()).unwrap();
    assert_eq!(
        edgeone_dns.requests()[2].headers["x-tc-action"],
        "CreateDnsRecord"
    );
    let failure = FakeHttpClient::responses([(
        200,
        json!({"Response":{"Error":{"Code":"AuthFailure","Message":"bad"}}}),
    )]);
    assert!(run("tencentcloud", "id", "secret", failure).is_err());
}

#[test]
fn cloudns_dnscom_and_namesilo_create_and_errors_are_offline() {
    let cloudns = FakeHttpClient::responses([
        (200, json!({"name":"example.com"})),
        (200, json!({})),
        (200, json!({"status":"Success"})),
    ]);
    run("cloudns", "id", "secret", cloudns.clone()).unwrap();
    assert!(cloudns.requests()[2].url.ends_with("/dns/add-record.json"));
    assert!(
        run(
            "cloudns",
            "id",
            "secret",
            FakeHttpClient::responses([(
                200,
                json!({"status":"Failed","statusDescription":"bad"})
            )])
        )
        .is_err()
    );

    let dnscom = FakeHttpClient::responses([
        (200, json!({"code":0,"data":{"domainID":"example.com"}})),
        (200, json!({"code":0,"data":{"data":[]}})),
        (200, json!({"code":0,"data":{"recordID":"record"}})),
    ]);
    run("dnscom", "id", "secret", dnscom.clone()).unwrap();
    assert!(dnscom.requests()[2].url.ends_with("/api/record/create/"));
    assert!(
        run(
            "dnscom",
            "id",
            "secret",
            FakeHttpClient::responses([(200, json!({"code":1,"message":"bad"}))])
        )
        .is_err()
    );

    let namesilo = FakeHttpClient::responses([
        (
            200,
            json!({"reply":{"code":"300","domain":{"domain":"example.com"}}}),
        ),
        (200, json!({"reply":{"code":"300","resource_record":[]}})),
        (200, json!({"reply":{"code":"300","record_id":"record"}})),
    ]);
    run("namesilo", "", "secret", namesilo.clone()).unwrap();
    assert!(namesilo.requests()[2].url.contains("/api/dnsAddRecord?"));
    assert!(
        run(
            "namesilo",
            "",
            "secret",
            FakeHttpClient::responses([(200, json!({"reply":{"code":"400","detail":"bad"}}))])
        )
        .is_err()
    );
}

#[test]
fn aliesa_and_huawei_create_and_errors_are_offline() {
    let aliesa = FakeHttpClient::responses([
        (
            200,
            json!({"Sites":[{"SiteId":7,"SiteName":"example.com"}]}),
        ),
        (200, json!({"Records":[]})),
        (200, json!({"RecordId":"record"})),
    ]);
    run("aliesa", "id", "secret", aliesa.clone()).unwrap();
    assert_eq!(aliesa.requests()[2].headers["x-acs-action"], "CreateRecord");
    assert!(
        run(
            "aliesa",
            "id",
            "secret",
            FakeHttpClient::responses([(200, json!({"Code":"Forbidden","Message":"bad"}))])
        )
        .is_err()
    );

    let aliesa_update = FakeHttpClient::responses([
        (
            200,
            json!({"Sites":[{"SiteId":7,"SiteName":"example.com"}]}),
        ),
        (
            200,
            json!({"Records":[{
                "RecordId": 123,
                "RecordName": "www",
                "RecordType": "A/AAAA",
                "Data": {"Value": "192.0.2.1"},
                "Ttl": 60,
                "Proxied": true
            }]}),
        ),
        (200, json!({"RecordId":123})),
    ]);
    run("aliesa", "id", "secret", aliesa_update.clone()).unwrap();
    let update_body: Value =
        serde_json::from_str(aliesa_update.requests()[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(update_body["RecordId"], 123);
    assert!(update_body["RecordId"].is_number());

    let huawei = FakeHttpClient::responses([
        (200, json!({"zones":[{"id":"zone","name":"example.com."}]})),
        (200, json!({"recordsets":[]})),
        (200, json!({"id":"record"})),
    ]);
    run("huaweidns", "id", "secret", huawei.clone()).unwrap();
    assert_eq!(huawei.requests()[2].method, Method::Post);
    let mut huawei_request = request();
    huawei_request
        .extra
        .insert("description".to_owned(), json!("custom description"));
    let huawei_description = FakeHttpClient::responses([
        (200, json!({"zones":[{"id":"zone","name":"example.com."}]})),
        (200, json!({"recordsets":[]})),
        (200, json!({"id":"record"})),
    ]);
    run_request(
        "huaweidns",
        "id",
        "secret",
        huawei_description.clone(),
        huawei_request,
    )
    .unwrap();
    let body: Value =
        serde_json::from_str(huawei_description.requests()[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["description"], "custom description");
    assert!(
        run(
            "huaweidns",
            "id",
            "secret",
            FakeHttpClient::responses([(200, json!({"zones":[]}))])
        )
        .is_err()
    );
}

#[test]
fn simple_providers_direct_success_and_error_are_offline() {
    for (provider, id, token, success, failure) in [
        ("he", "", "secret", "good 192.0.2.45", "badauth"),
        ("noip", "user", "secret", "nochg 192.0.2.45", "badauth"),
    ] {
        let client = FakeHttpClient::text([(200, success)]);
        run(provider, id, token, client.clone()).unwrap();
        assert!(client.requests()[0].url.contains("/nic/update"));
        assert!(run(provider, id, token, FakeHttpClient::text([(200, failure)])).is_err());
    }

    let callback = FakeHttpClient::text([(200, "ok")]);
    run(
        "callback",
        "http://mock.local/callback?host=__DOMAIN__&ip=__IP__",
        "",
        callback.clone(),
    )
    .unwrap();
    assert!(callback.requests()[0].url.contains("host=www.example.com"));
    assert!(
        run(
            "callback",
            "http://mock.local/callback",
            "",
            FakeHttpClient::text([(500, "bad")])
        )
        .is_err()
    );
    let west = FakeHttpClient::responses([(200, json!({"code":200,"body":{"record_id":1}}))]);
    run("west", "user", "secret", west.clone()).unwrap();
    assert_eq!(west.requests()[0].method, Method::Post);
    assert!(
        run(
            "west",
            "user",
            "secret",
            FakeHttpClient::responses([(200, json!({"code":500,"msg":"bad"}))])
        )
        .is_err()
    );
}

#[test]
fn namesilo_zone_candidates_and_string_ttl_are_preserved() {
    let client = FakeHttpClient::responses([
        (
            200,
            json!({"reply":{"code":"400","detail":"not in account"}}),
        ),
        (
            200,
            json!({"reply":{"code":"300","domain":{"domain":"example.co.uk"}}}),
        ),
        (
            200,
            json!({"reply":{"code":"300","resource_record":[{
                "record_id":"record",
                "host":"www",
                "type":"A",
                "ttl":"3600"
            }]}}),
        ),
        (200, json!({"reply":{"code":"300","record_id":"record"}})),
    ]);
    let mut namesilo_request = request();
    namesilo_request.domain = "www.example.co.uk".to_owned();
    namesilo_request.ttl = None;
    run_request("namesilo", "", "secret", client.clone(), namesilo_request).unwrap();
    let requests = client.requests();
    assert!(requests[0].url.contains("domain=co.uk"));
    assert!(requests[1].url.contains("domain=example.co.uk"));
    assert!(requests[3].url.contains("rrttl=3600"));
}

#[test]
fn provider_specific_create_extras_are_preserved() {
    let mut dnscom_request = request();
    dnscom_request
        .extra
        .insert("remark".to_owned(), json!("custom remark"));
    let dnscom = FakeHttpClient::responses([
        (200, json!({"code":0,"data":{"domainID":"example.com"}})),
        (200, json!({"code":0,"data":{"data":[]}})),
        (200, json!({"code":0,"data":{"recordID":"record"}})),
    ]);
    run_request("dnscom", "id", "secret", dnscom.clone(), dnscom_request).unwrap();
    assert!(
        dnscom.requests()[2]
            .body
            .as_deref()
            .unwrap()
            .contains("remark=custom+remark")
    );
}

#[test]
fn callback_object_body_is_not_written_to_debug_log() {
    let path =
        std::env::temp_dir().join(format!("ddns-rs-callback-log-{}.log", std::process::id()));
    let _ = std::fs::remove_file(&path);
    let client = FakeHttpClient::text([(200, "ok")]);
    let client_for_provider: Arc<dyn HttpClient> = client.clone();
    let mut provider = build(
        &config(
            "callback",
            "http://mock.local/callback",
            r#"{"api_key":"callback-secret","address":"__IP__"}"#,
        ),
        client_for_provider,
        Logger::new(Level::Debug, Some(&path), Vec::new()).unwrap(),
    )
    .unwrap();
    provider.set_record(&request()).unwrap();
    let body = client.requests()[0].body.clone().unwrap();
    assert!(body.contains("callback-secret"));
    let log = std::fs::read_to_string(&path).unwrap();
    assert!(!log.contains("callback-secret"));
    let _ = std::fs::remove_file(path);
}

#[test]
fn cloudns_validates_multi_label_zone_candidates() {
    let client = FakeHttpClient::responses([
        (
            200,
            json!({"status":"Failed","statusDescription":"zone not found"}),
        ),
        (200, json!({"name":"example.co.uk"})),
        (200, json!({})),
        (200, json!({"status":"Success"})),
    ]);
    let mut cloudns_request = request();
    cloudns_request.domain = "www.example.co.uk".to_owned();
    run_request("cloudns", "id", "secret", client.clone(), cloudns_request).unwrap();
    let requests = client.requests();
    assert!(
        requests[0]
            .body
            .as_deref()
            .unwrap()
            .contains("domain-name=co.uk")
    );
    assert!(
        requests[1]
            .body
            .as_deref()
            .unwrap()
            .contains("domain-name=example.co.uk")
    );
}

use std::collections::{BTreeMap, VecDeque};
use std::path::Path;
use std::sync::{Arc, LazyLock, Mutex};

use ddns_rs::config::{AddressRules, CacheSetting, Config, LogConfig, TlsMode};
use ddns_rs::error::{Error, Result};
use ddns_rs::http::{HttpClient, HttpRequest, HttpResponse};
use ddns_rs::logging::{Level, Logger};
use ddns_rs::provider::{ProviderId, RecordRequest};
use serde_json::Value;

static EMPTY_EXTRA: LazyLock<BTreeMap<String, Value>> = LazyLock::new(BTreeMap::new);

#[derive(Default)]
pub struct FakeHttpClient {
    responses: Mutex<VecDeque<HttpResponse>>,
    requests: Mutex<Vec<HttpRequest>>,
}

impl FakeHttpClient {
    pub fn new(responses: impl IntoIterator<Item = HttpResponse>) -> Arc<Self> {
        Arc::new(Self {
            responses: Mutex::new(responses.into_iter().collect()),
            requests: Mutex::new(Vec::new()),
        })
    }

    pub fn requests(&self) -> Vec<HttpRequest> {
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

pub fn config(provider: &str, id: &str, token: &str) -> Config {
    Config {
        provider: provider.parse::<ProviderId>().unwrap(),
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
    }
}

pub fn logger(token: &str) -> Logger {
    Logger::new(Level::Critical, None::<&Path>, vec![token.to_owned()]).unwrap()
}

pub fn request(address: &str) -> RecordRequest<'_> {
    RecordRequest {
        domain: "www.example.com",
        address,
        record_type: "A",
        ttl: Some(300),
        line: None,
        extra: &EMPTY_EXTRA,
    }
}

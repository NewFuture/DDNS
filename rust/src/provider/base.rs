use std::collections::BTreeMap;
use std::time::Duration;

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::{HttpClient, HttpRequest, HttpResponse, Method, append_query, redact_url};
use crate::logging::Logger;

#[derive(Clone, Copy, Debug)]
pub struct RecordRequest<'a> {
    pub domain: &'a str,
    pub address: &'a str,
    pub record_type: &'a str,
    pub ttl: Option<u32>,
    pub line: Option<&'a str>,
    pub extra: &'a BTreeMap<String, Value>,
}

pub struct ProviderContext<'a> {
    pub id: String,
    pub token: String,
    pub endpoint: String,
    pub proxies: Vec<String>,
    pub client: &'a dyn HttpClient,
    pub logger: Logger,
}

impl ProviderContext<'_> {
    pub fn url(&self, path: &str) -> String {
        if path.starts_with("http://") || path.starts_with("https://") {
            return path.to_owned();
        }
        format!(
            "{}/{}",
            self.endpoint.trim_end_matches('/'),
            path.trim_start_matches('/')
        )
    }

    pub fn send(
        &self,
        method: Method,
        path: &str,
        query: &BTreeMap<String, String>,
        body: Option<String>,
        headers: BTreeMap<String, String>,
    ) -> Result<HttpResponse> {
        self.send_internal(method, path, query, body, headers, true)
    }

    pub fn send_sensitive(
        &self,
        method: Method,
        path: &str,
        query: &BTreeMap<String, String>,
        body: Option<String>,
        headers: BTreeMap<String, String>,
    ) -> Result<HttpResponse> {
        self.send_internal(method, path, query, body, headers, false)
    }

    fn send_internal(
        &self,
        method: Method,
        path: &str,
        query: &BTreeMap<String, String>,
        body: Option<String>,
        headers: BTreeMap<String, String>,
        log_body: bool,
    ) -> Result<HttpResponse> {
        let url = append_query(&self.url(path), query);
        self.logger.info(
            "provider.http",
            format!("{} {}", method.as_str(), redact_url(&url)),
        );
        if log_body && let Some(body) = &body {
            self.logger.debug("provider.http", format!("body: {body}"));
        }
        let response = self.client.execute(&HttpRequest {
            method,
            url,
            headers,
            body,
            proxies: self.proxies.clone(),
            timeout: if method == Method::Get {
                Duration::from_secs(60)
            } else {
                Duration::from_secs(120)
            },
            retries: 2,
        })?;
        if !(200..300).contains(&response.status) {
            return Err(Error::Provider(format!(
                "HTTP {} {}: {}",
                response.status,
                response.reason,
                self.logger.mask(&response.body)
            )));
        }
        Ok(response)
    }

    pub fn send_json(
        &self,
        method: Method,
        path: &str,
        query: &BTreeMap<String, String>,
        body: Option<String>,
        headers: BTreeMap<String, String>,
    ) -> Result<Value> {
        let response = self.send(method, path, query, body, headers)?;
        serde_json::from_str(&response.body).map_err(|error| {
            Error::Provider(format!(
                "provider returned invalid JSON: {error}; body: {}",
                self.logger.mask(&response.body)
            ))
        })
    }
}

pub trait Provider {
    fn set_record(&mut self, request: &RecordRequest<'_>) -> Result<()>;
}

pub trait CrudProvider {
    fn context(&self) -> &ProviderContext<'_>;
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String>;
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>>;
    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>>;
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()>;
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
    ) -> Result<()>;

    fn split_zone_and_sub(&mut self, domain: &str) -> Result<ZoneMatch> {
        if let Some((subdomain, main_domain)) = split_custom_domain(domain) {
            let zone_id = self
                .get_zone_id(&main_domain)?
                .ok_or_else(|| Error::Provider(format!("zone not found for {main_domain}")))?;
            return Ok(ZoneMatch {
                zone_id,
                subdomain,
                main_domain,
            });
        }

        let labels = domain.split('.').collect::<Vec<_>>();
        if labels.len() < 2 {
            return Err(Error::Provider(format!("invalid domain `{domain}`")));
        }
        for count in 2..=labels.len() {
            let main_domain = labels[labels.len() - count..].join(".");
            if let Some(zone_id) = self.get_zone_id(&main_domain)? {
                let subdomain = labels[..labels.len() - count].join(".");
                return Ok(ZoneMatch {
                    zone_id,
                    subdomain: if subdomain.is_empty() {
                        "@".to_owned()
                    } else {
                        subdomain
                    },
                    main_domain,
                });
            }
        }
        Err(Error::Provider(format!("zone not found for {domain}")))
    }

    fn get_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        if let Some(zone_id) = self.zone_cache().get(domain) {
            return Ok(Some(zone_id.clone()));
        }
        let zone_id = self.query_zone_id(domain)?;
        if let Some(zone_id) = &zone_id {
            self.zone_cache().insert(domain.to_owned(), zone_id.clone());
        }
        Ok(zone_id)
    }

    fn apply(&mut self, request: &RecordRequest<'_>) -> Result<()>
    where
        Self: Sized,
    {
        let domain = request.domain.trim_end_matches('.').to_ascii_lowercase();
        let zone = self.split_zone_and_sub(&domain)?;
        self.context().logger.info(
            "provider",
            format!(
                "{} => {} ({}) [zone={}, sub={}]",
                domain, request.address, request.record_type, zone.main_domain, zone.subdomain
            ),
        );
        if let Some(record) =
            self.query_record(&zone.zone_id, &zone.subdomain, &zone.main_domain, request)?
        {
            self.update_record(&zone.zone_id, &record, request)
        } else {
            self.create_record(&zone.zone_id, &zone.subdomain, &zone.main_domain, request)
        }
    }
}

impl<T: CrudProvider> Provider for T {
    fn set_record(&mut self, request: &RecordRequest<'_>) -> Result<()> {
        self.apply(request)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ZoneMatch {
    pub zone_id: String,
    pub subdomain: String,
    pub main_domain: String,
}

pub fn split_custom_domain(domain: &str) -> Option<(String, String)> {
    for separator in ['~', '+'] {
        if let Some((subdomain, main_domain)) = domain.split_once(separator) {
            return Some((subdomain.to_owned(), main_domain.to_owned()));
        }
    }
    None
}

pub fn join_domain(subdomain: &str, main_domain: &str) -> String {
    let subdomain = subdomain.trim().trim_matches('.').to_ascii_lowercase();
    let main_domain = main_domain.trim().trim_matches('.').to_ascii_lowercase();
    if subdomain.is_empty() || subdomain == "@" {
        main_domain
    } else if main_domain.is_empty() {
        subdomain
    } else {
        format!("{subdomain}.{main_domain}")
    }
}

pub fn value_to_string(value: &Value) -> Option<String> {
    match value {
        Value::Null => None,
        Value::Bool(value) => Some(value.to_string().to_ascii_lowercase()),
        Value::Number(value) => Some(value.to_string()),
        Value::String(value) => Some(value.clone()),
        Value::Array(_) | Value::Object(_) => None,
    }
}

pub fn numeric_id(value: &str, name: &str) -> Result<u64> {
    value
        .parse()
        .map_err(|_| Error::Provider(format!("{name} `{value}` is not numeric")))
}

pub fn string_parameters(
    request: &RecordRequest<'_>,
    values: impl IntoIterator<Item = (&'static str, Option<String>)>,
) -> BTreeMap<String, String> {
    let mut parameters = request
        .extra
        .iter()
        .filter_map(|(key, value)| value_to_string(value).map(|value| (key.clone(), value)))
        .collect::<BTreeMap<_, _>>();
    parameters.extend(
        values
            .into_iter()
            .filter_map(|(key, value)| value.map(|value| (key.to_owned(), value))),
    );
    parameters
}

pub fn json_parameters(request: &RecordRequest<'_>) -> serde_json::Map<String, Value> {
    request
        .extra
        .iter()
        .map(|(key, value)| (key.clone(), value.clone()))
        .collect()
}

pub fn endpoint_host(endpoint: &str, provider: &str) -> Result<String> {
    endpoint
        .split_once("://")
        .map(|(_, host)| host)
        .unwrap_or(endpoint)
        .split('/')
        .next()
        .filter(|host| !host.is_empty())
        .map(ToOwned::to_owned)
        .ok_or_else(|| Error::Config(format!("invalid {provider} endpoint `{endpoint}`")))
}

#[cfg(test)]
mod tests {
    use super::{join_domain, numeric_id, split_custom_domain};

    #[test]
    fn handles_custom_domain_separators() {
        assert_eq!(
            split_custom_domain("www~example.com"),
            Some(("www".to_owned(), "example.com".to_owned()))
        );
        assert_eq!(
            split_custom_domain("api+example.com"),
            Some(("api".to_owned(), "example.com".to_owned()))
        );
    }

    #[test]
    fn joins_root_and_nested_records() {
        assert_eq!(join_domain("@", "example.com"), "example.com");
        assert_eq!(join_domain("www", "example.com"), "www.example.com");
    }

    #[test]
    fn rejects_non_numeric_ids() {
        assert_eq!(numeric_id("42", "record id").unwrap(), 42);
        assert!(numeric_id("invalid", "record id").is_err());
    }
}

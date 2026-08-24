use std::collections::BTreeMap;

use serde_json::{Map, Value, json};
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};
use crate::signature::{hmac_sha256_authorization, sha256_hex};

use super::base::{CrudProvider, Provider, ProviderContext, RecordRequest, join_domain};
use super::empty_zone_cache;

pub struct HuaweiDnsProvider {
    context: ProviderContext,
    zones: BTreeMap<String, String>,
}

impl HuaweiDnsProvider {
    pub fn new(context: ProviderContext) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "Huawei Cloud access key and secret must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: empty_zone_cache(),
        })
    }

    fn api(&self, method: Method, path: &str, values: Map<String, Value>) -> Result<Value> {
        let values = values
            .into_iter()
            .filter(|(_, value)| !value.is_null())
            .collect::<Map<_, _>>();
        let (query, body) = if matches!(method, Method::Get | Method::Delete) {
            (
                values
                    .iter()
                    .filter_map(|(key, value)| {
                        super::base::value_to_string(value).map(|value| (key.clone(), value))
                    })
                    .collect::<BTreeMap<_, _>>(),
                String::new(),
            )
        } else {
            (
                BTreeMap::new(),
                serde_json::to_string(&Value::Object(values))?,
            )
        };
        let canonical_query = form_encode(&query);
        let now = OffsetDateTime::now_utc();
        let timestamp = format!(
            "{:04}{:02}{:02}T{:02}{:02}{:02}Z",
            now.year(),
            u8::from(now.month()),
            now.day(),
            now.hour(),
            now.minute(),
            now.second()
        );
        let headers = BTreeMap::from([
            ("content-type".to_owned(), "application/json".to_owned()),
            ("host".to_owned(), endpoint_host(&self.context.endpoint)?),
            ("x-sdk-date".to_owned(), timestamp.clone()),
        ]);
        let signed_path = if path.ends_with('/') {
            path.to_owned()
        } else {
            format!("{path}/")
        };
        let authorization = hmac_sha256_authorization(
            &self.context.token,
            "SDK-HMAC-SHA256",
            &timestamp,
            &format!("Access={}", self.context.id),
            method_name(method),
            &signed_path,
            &canonical_query,
            &headers,
            &sha256_hex(&body),
        )?;
        let mut headers = headers;
        headers.insert("authorization".to_owned(), authorization);
        self.context.send_json(
            method,
            path,
            &query,
            (!body.is_empty()).then_some(body),
            headers,
        )
    }
}

impl Provider for HuaweiDnsProvider {
    fn name(&self) -> &'static str {
        "huaweidns"
    }
    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        CrudProvider::apply(self, request)
    }
}

impl CrudProvider for HuaweiDnsProvider {
    fn context(&self) -> &ProviderContext {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let domain = format!("{}.", domain.trim_end_matches('.'));
        let response = self.api(
            Method::Get,
            "/v2/zones",
            Map::from_iter([
                ("search_mode".to_owned(), json!("equal")),
                ("limit".to_owned(), json!(500)),
                ("name".to_owned(), json!(&domain)),
            ]),
        )?;
        Ok(response
            .get("zones")
            .and_then(Value::as_array)
            .and_then(|zones| {
                zones
                    .iter()
                    .find(|zone| zone.get("name").and_then(Value::as_str) == Some(domain.as_str()))
                    .and_then(|zone| zone.get("id"))
                    .and_then(Value::as_str)
                    .map(ToOwned::to_owned)
            }))
    }
    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<Option<Value>> {
        let name = format!("{}.", join_domain(subdomain, main_domain));
        let mut values = Map::from_iter([
            ("limit".to_owned(), json!(500)),
            ("name".to_owned(), json!(&name)),
            ("type".to_owned(), json!(&request.record_type)),
            ("search_mode".to_owned(), json!("equal")),
        ]);
        if let Some(line) = &request.line {
            values.insert("line_id".to_owned(), json!(line));
        }
        let response = self.api(
            Method::Get,
            &format!("/v2.1/zones/{zone_id}/recordsets"),
            values,
        )?;
        Ok(response
            .get("recordsets")
            .and_then(Value::as_array)
            .and_then(|records| {
                records
                    .iter()
                    .find(|record| {
                        record.get("name").and_then(Value::as_str) == Some(name.as_str())
                            && record.get("type").and_then(Value::as_str)
                                == Some(request.record_type.as_str())
                    })
                    .cloned()
            }))
    }
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<()> {
        let mut values = request.extra.clone().into_iter().collect::<Map<_, _>>();
        values.extend([
            (
                "name".to_owned(),
                json!(format!("{}.", join_domain(subdomain, main_domain))),
            ),
            ("type".to_owned(), json!(&request.record_type)),
            ("records".to_owned(), json!([&request.address])),
        ]);
        values
            .entry("description".to_owned())
            .or_insert_with(|| json!("Managed by DDNS"));
        if let Some(ttl) = request.ttl {
            values.insert("ttl".to_owned(), json!(ttl));
        }
        if let Some(line) = &request.line {
            values.insert("line".to_owned(), json!(line));
        }
        if self
            .api(
                Method::Post,
                &format!("/v2.1/zones/{zone_id}/recordsets"),
                values,
            )?
            .get("id")
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "Huawei DNS failed to create record".to_owned(),
            ))
        }
    }
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest,
    ) -> Result<()> {
        let record_id = record
            .get("id")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::Provider("Huawei DNS record has no id".to_owned()))?;
        let mut values = request.extra.clone().into_iter().collect::<Map<_, _>>();
        values.extend([
            (
                "name".to_owned(),
                record.get("name").cloned().unwrap_or(Value::Null),
            ),
            ("type".to_owned(), json!(&request.record_type)),
            ("records".to_owned(), json!([&request.address])),
        ]);
        values
            .entry("description".to_owned())
            .or_insert_with(|| json!("Managed by DDNS"));
        if let Some(ttl) = request.ttl.or_else(|| {
            record
                .get("ttl")
                .and_then(Value::as_u64)
                .map(|ttl| ttl as u32)
        }) {
            values.insert("ttl".to_owned(), json!(ttl));
        }
        if self
            .api(
                Method::Put,
                &format!("/v2.1/zones/{zone_id}/recordsets/{record_id}"),
                values,
            )?
            .get("id")
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "Huawei DNS failed to update record".to_owned(),
            ))
        }
    }
}

fn endpoint_host(endpoint: &str) -> Result<String> {
    endpoint
        .split_once("://")
        .map(|(_, value)| value)
        .unwrap_or(endpoint)
        .split('/')
        .next()
        .filter(|value| !value.is_empty())
        .map(ToOwned::to_owned)
        .ok_or_else(|| Error::Config(format!("invalid Huawei endpoint `{endpoint}`")))
}

const fn method_name(method: Method) -> &'static str {
    match method {
        Method::Get => "GET",
        Method::Post => "POST",
        Method::Put => "PUT",
        Method::Delete => "DELETE",
    }
}

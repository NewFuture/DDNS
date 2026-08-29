use std::collections::BTreeMap;

use serde_json::{Map, Value, json};

use crate::error::{Error, Result};
use crate::http::Method;
use crate::signature::{acs_timestamp, acs3_authorization, request_nonce, sha256_hex};

use super::base::{
    CrudProvider, ProviderContext, RecordRequest, endpoint_host, join_domain, json_parameters,
    numeric_id, value_to_string,
};

pub struct AliesaProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
}

impl<'a> AliesaProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "AliESA access key id and secret must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
        })
    }

    fn api(&self, method: Method, action: &str, values: Map<String, Value>) -> Result<Value> {
        let body = if matches!(method, Method::Get) {
            None
        } else {
            Some(serde_json::to_string(&Value::Object(values.clone()))?)
        };
        let query = if matches!(method, Method::Get) {
            values
                .iter()
                .filter_map(|(key, value)| value_to_string(value).map(|value| (key.clone(), value)))
                .collect()
        } else {
            BTreeMap::new()
        };
        let body_hash = sha256_hex(body.as_deref().unwrap_or(""));
        let headers = BTreeMap::from([
            (
                "host".to_owned(),
                endpoint_host(&self.context.endpoint, "AliESA")?,
            ),
            ("content-type".to_owned(), "application/json".to_owned()),
            ("x-acs-action".to_owned(), action.to_owned()),
            ("x-acs-content-sha256".to_owned(), body_hash.clone()),
            ("x-acs-date".to_owned(), acs_timestamp()),
            ("x-acs-signature-nonce".to_owned(), request_nonce()?),
            ("x-acs-version".to_owned(), "2024-09-10".to_owned()),
        ]);
        let authorization = acs3_authorization(
            &self.context.id,
            &self.context.token,
            method.as_str(),
            "/",
            &crate::http::form_encode(&query),
            &headers,
            &body_hash,
        )?;
        let mut headers = headers;
        headers.insert("authorization".to_owned(), authorization);
        let response = self.context.send_json(method, "/", &query, body, headers)?;
        if let Some(code) = response.get("Code").and_then(Value::as_str) {
            return Err(Error::Provider(format!(
                "AliESA API error {code}: {}",
                self.context.logger.mask(
                    response
                        .get("Message")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown error")
                )
            )));
        }
        Ok(response)
    }
}

impl CrudProvider for AliesaProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let response = self.api(
            Method::Get,
            "ListSites",
            Map::from_iter([
                ("SiteName".to_owned(), json!(domain)),
                ("PageSize".to_owned(), json!(500)),
            ]),
        )?;
        Ok(response
            .get("Sites")
            .and_then(Value::as_array)
            .and_then(|sites| {
                sites
                    .iter()
                    .find(|site| site.get("SiteName").and_then(Value::as_str) == Some(domain))
                    .and_then(|site| site.get("SiteId"))
                    .and_then(value_to_string)
            }))
    }
    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let response = self.api(
            Method::Get,
            "ListRecords",
            Map::from_iter([
                (
                    "SiteId".to_owned(),
                    json!(numeric_id(zone_id, "AliESA site id")?),
                ),
                (
                    "RecordName".to_owned(),
                    json!(join_domain(subdomain, main_domain)),
                ),
                (
                    "Type".to_owned(),
                    json!(if matches!(request.record_type, "A" | "AAAA") {
                        "A/AAAA"
                    } else {
                        request.record_type
                    }),
                ),
                ("RecordMatchType".to_owned(), json!("exact")),
                ("PageSize".to_owned(), json!(100)),
            ]),
        )?;
        Ok(response
            .get("Records")
            .and_then(Value::as_array)
            .and_then(|records| records.first().cloned()))
    }
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut values = json_parameters(request);
        values.extend([
            (
                "SiteId".to_owned(),
                json!(numeric_id(zone_id, "AliESA site id")?),
            ),
            (
                "RecordName".to_owned(),
                json!(join_domain(subdomain, main_domain)),
            ),
            (
                "Type".to_owned(),
                json!(if matches!(request.record_type, "A" | "AAAA") {
                    "A/AAAA"
                } else {
                    request.record_type
                }),
            ),
            ("Data".to_owned(), json!({"Value": request.address})),
            ("Ttl".to_owned(), json!(request.ttl.unwrap_or(1))),
        ]);
        values
            .entry("Comment".to_owned())
            .or_insert_with(|| json!("Managed by DDNS"));
        values
            .entry("BizName".to_owned())
            .or_insert_with(|| json!("web"));
        values
            .entry("Proxied".to_owned())
            .or_insert_with(|| json!(true));
        if self
            .api(Method::Post, "CreateRecord", values)?
            .get("RecordId")
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider("AliESA failed to create record".to_owned()))
        }
    }
    fn update_record(
        &mut self,
        _zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let unchanged = record.pointer("/Data/Value").and_then(Value::as_str)
            == Some(request.address)
            && request.ttl.is_none_or(|ttl| {
                record.get("Ttl").and_then(Value::as_u64) == Some(u64::from(ttl))
            });
        if unchanged {
            return Ok(());
        }
        let record_id = record
            .get("RecordId")
            .and_then(|value| match value {
                Value::Number(_) => Some(value.clone()),
                Value::String(value) => value.parse::<u64>().ok().map(|value| json!(value)),
                _ => None,
            })
            .ok_or_else(|| Error::Provider("AliESA record has no numeric RecordId".to_owned()))?;
        let mut values = json_parameters(request);
        values.extend([
            ("RecordId".to_owned(), record_id),
            ("Data".to_owned(), json!({"Value": request.address})),
        ]);
        values
            .entry("Comment".to_owned())
            .or_insert_with(|| json!("Managed by DDNS"));
        values
            .entry("Proxied".to_owned())
            .or_insert_with(|| record.get("Proxied").cloned().unwrap_or(Value::Null));
        if let Some(ttl) = request.ttl {
            values.insert("Ttl".to_owned(), json!(ttl));
        }
        if self
            .api(Method::Post, "UpdateRecord", values)?
            .get("RecordId")
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider("AliESA failed to update record".to_owned()))
        }
    }
}

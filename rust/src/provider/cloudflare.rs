use std::collections::BTreeMap;

use serde_json::{Map, Value, json};

use crate::error::{Error, Result};
use crate::http::Method;

use super::base::{
    CrudProvider, ProviderContext, RecordRequest, join_domain, json_parameters, value_to_string,
};

pub struct CloudflareProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
}

impl<'a> CloudflareProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        if context.token.is_empty() {
            return Err(Error::Config(
                "Cloudflare token must be configured".to_owned(),
            ));
        }
        if !context.id.is_empty() && !context.id.contains('@') {
            return Err(Error::Config(
                "Cloudflare id must be an email address or empty".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
        })
    }

    fn api(&self, method: Method, action: &str, parameters: &Map<String, Value>) -> Result<Value> {
        let mut headers = BTreeMap::new();
        if self.context.id.is_empty() {
            headers.insert(
                "authorization".to_owned(),
                format!("Bearer {}", self.context.token),
            );
        } else {
            headers.insert("x-auth-email".to_owned(), self.context.id.to_owned());
            headers.insert("x-auth-key".to_owned(), self.context.token.to_owned());
        }
        let path = format!("/client/v4/zones{action}");
        let (query, body) = if method == Method::Get || method == Method::Delete {
            let query = parameters
                .iter()
                .filter_map(|(key, value)| value_to_string(value).map(|value| (key.clone(), value)))
                .collect();
            (query, None)
        } else {
            headers.insert("content-type".to_owned(), "application/json".to_owned());
            (BTreeMap::new(), Some(serde_json::to_string(parameters)?))
        };
        let response = self
            .context
            .send_json(method, &path, &query, body, headers)?;
        if response.get("success").and_then(Value::as_bool) == Some(true) {
            return response
                .get("result")
                .cloned()
                .ok_or_else(|| Error::Provider("Cloudflare response has no result".to_owned()));
        }
        Err(Error::Provider(format!(
            "Cloudflare API error: {}",
            self.context.logger.mask(
                &response
                    .get("errors")
                    .cloned()
                    .unwrap_or(response)
                    .to_string()
            )
        )))
    }
}

impl CrudProvider for CloudflareProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let result = self.api(
            Method::Get,
            "",
            &Map::from_iter([
                ("name.exact".to_owned(), json!(domain)),
                ("per_page".to_owned(), json!(50)),
            ]),
        )?;
        let zones = result.as_array().ok_or_else(|| {
            Error::Provider("Cloudflare returned an invalid zone list".to_owned())
        })?;
        for zone in zones {
            let name = zone
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::Provider("Cloudflare zone has no name".to_owned()))?;
            let id = response_id(zone)?;
            if name == domain {
                return Ok(Some(id.to_owned()));
            }
        }
        Ok(None)
    }

    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let name = join_domain(subdomain, main_domain);
        let mut parameters = Map::from_iter([
            ("name.exact".to_owned(), json!(name)),
            ("type".to_owned(), json!(request.record_type)),
            ("per_page".to_owned(), json!(10_000)),
        ]);
        let proxied = request.extra.get("proxied");
        if let Some(proxied) = proxied {
            parameters.insert("proxied".to_owned(), proxied.clone());
        }
        let action = format!("/{zone_id}/dns_records");
        let result = self.api(Method::Get, &action, &parameters)?;
        let record = find_record(&result, &name, request.record_type)?;
        if record.is_none() && proxied.is_some() {
            parameters.remove("proxied");
            let result = self.api(Method::Get, &action, &parameters)?;
            return find_record(&result, &name, request.record_type);
        }
        Ok(record)
    }

    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut parameters = json_parameters(request);
        parameters
            .entry("comment".to_owned())
            .or_insert_with(|| json!("Managed by [DDNS](https://ddns.newfuture.cc)"));
        parameters.insert(
            "name".to_owned(),
            json!(join_domain(subdomain, main_domain)),
        );
        parameters.insert("type".to_owned(), json!(request.record_type));
        parameters.insert("content".to_owned(), json!(request.address));
        if let Some(ttl) = request.ttl {
            parameters.insert("ttl".to_owned(), json!(ttl));
        }
        let result = self.api(
            Method::Post,
            &format!("/{zone_id}/dns_records"),
            &parameters,
        )?;
        response_id(&result).map(|_| ())
    }

    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let record_id = response_id(record)?;
        let mut parameters = json_parameters(request);
        for key in ["proxied", "tags", "settings"] {
            if !parameters.contains_key(key)
                && let Some(value) = record.get(key)
            {
                parameters.insert(key.to_owned(), value.clone());
            }
        }
        parameters
            .entry("comment".to_owned())
            .or_insert_with(|| json!("Managed by [DDNS](https://ddns.newfuture.cc)"));
        parameters.insert(
            "name".to_owned(),
            record.get("name").cloned().unwrap_or(Value::Null),
        );
        parameters.insert("type".to_owned(), json!(request.record_type));
        parameters.insert("content".to_owned(), json!(request.address));
        if let Some(ttl) = request.ttl {
            parameters.insert("ttl".to_owned(), json!(ttl));
        }
        let result = self.api(
            Method::Put,
            &format!("/{zone_id}/dns_records/{record_id}"),
            &parameters,
        )?;
        if response_id(&result)? != record_id {
            return Err(Error::Provider(
                "Cloudflare returned a different record id".to_owned(),
            ));
        }
        Ok(())
    }
}

fn response_id(result: &Value) -> Result<&str> {
    result
        .get("id")
        .and_then(Value::as_str)
        .filter(|id| !id.is_empty())
        .ok_or_else(|| Error::Provider("Cloudflare response has no valid id".to_owned()))
}

fn find_record(result: &Value, name: &str, record_type: &str) -> Result<Option<Value>> {
    let records = result
        .as_array()
        .ok_or_else(|| Error::Provider("Cloudflare returned an invalid record list".to_owned()))?;
    for record in records {
        let record_name = record
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::Provider("Cloudflare record has no name".to_owned()))?;
        let kind = record
            .get("type")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::Provider("Cloudflare record has no type".to_owned()))?;
        response_id(record)?;
        if record_name == name && kind == record_type {
            return Ok(Some(record.clone()));
        }
    }
    Ok(None)
}

use std::collections::BTreeMap;

use serde_json::{Map, Value, json};

use crate::error::{Error, Result};
use crate::http::Method;

use super::base::{
    CrudProvider, Provider, ProviderContext, RecordRequest, join_domain, value_to_string,
};
use super::empty_zone_cache;

pub struct CloudflareProvider {
    context: ProviderContext,
    zones: BTreeMap<String, String>,
}

impl CloudflareProvider {
    pub fn new(context: ProviderContext) -> Result<Self> {
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
            zones: empty_zone_cache(),
        })
    }

    fn api(&self, method: Method, action: &str, parameters: Map<String, Value>) -> Result<Value> {
        let mut headers = BTreeMap::new();
        if self.context.id.is_empty() {
            headers.insert(
                "authorization".to_owned(),
                format!("Bearer {}", self.context.token),
            );
        } else {
            headers.insert("x-auth-email".to_owned(), self.context.id.clone());
            headers.insert("x-auth-key".to_owned(), self.context.token.clone());
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
            (
                BTreeMap::new(),
                Some(serde_json::to_string(&Value::Object(parameters))?),
            )
        };
        let response = self
            .context
            .send_json(method, &path, &query, body, headers)?;
        if response.get("success").and_then(Value::as_bool) == Some(true) {
            return Ok(response.get("result").cloned().unwrap_or(Value::Null));
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

impl Provider for CloudflareProvider {
    fn name(&self) -> &'static str {
        "cloudflare"
    }

    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        CrudProvider::apply(self, request)
    }
}

impl CrudProvider for CloudflareProvider {
    fn context(&self) -> &ProviderContext {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let result = self.api(
            Method::Get,
            "",
            Map::from_iter([
                ("name.exact".to_owned(), json!(domain)),
                ("per_page".to_owned(), json!(50)),
            ]),
        )?;
        Ok(result.as_array().and_then(|zones| {
            zones
                .iter()
                .find(|zone| zone.get("name").and_then(Value::as_str) == Some(domain))
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
        let name = join_domain(subdomain, main_domain);
        let mut parameters = Map::from_iter([
            ("name.exact".to_owned(), json!(name)),
            ("type".to_owned(), json!(request.record_type)),
            ("per_page".to_owned(), json!(10_000)),
        ]);
        let proxied = request.extra.get("proxied").cloned();
        if let Some(proxied) = &proxied {
            parameters.insert("proxied".to_owned(), proxied.clone());
        }
        let action = format!("/{zone_id}/dns_records");
        let mut result = self.api(Method::Get, &action, parameters.clone())?;
        let mut record = find_record(&result, &name, &request.record_type);
        if record.is_none() && proxied.is_some() {
            parameters.remove("proxied");
            result = self.api(Method::Get, &action, parameters)?;
            record = find_record(&result, &name, &request.record_type);
        }
        Ok(record)
    }

    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<()> {
        let mut parameters = request
            .extra
            .clone()
            .into_iter()
            .collect::<Map<String, Value>>();
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
        self.api(Method::Post, &format!("/{zone_id}/dns_records"), parameters)?;
        Ok(())
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
            .ok_or_else(|| Error::Provider("Cloudflare record has no id".to_owned()))?;
        let mut parameters = request
            .extra
            .clone()
            .into_iter()
            .collect::<Map<String, Value>>();
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
        self.api(
            Method::Put,
            &format!("/{zone_id}/dns_records/{record_id}"),
            parameters,
        )?;
        Ok(())
    }
}

fn find_record(result: &Value, name: &str, record_type: &str) -> Option<Value> {
    result.as_array().and_then(|records| {
        records
            .iter()
            .find(|record| {
                record.get("name").and_then(Value::as_str) == Some(name)
                    && record.get("type").and_then(Value::as_str) == Some(record_type)
            })
            .cloned()
    })
}

use std::collections::BTreeMap;

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::Method;

use super::base::{CrudProvider, Provider, ProviderContext, RecordRequest, value_to_string};
use super::empty_zone_cache;

pub struct NamesiloProvider {
    context: ProviderContext,
    zones: BTreeMap<String, String>,
}

impl NamesiloProvider {
    pub fn new(context: ProviderContext) -> Result<Self> {
        if context.token.is_empty() {
            return Err(Error::Config(
                "NameSilo API key must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: empty_zone_cache(),
        })
    }

    fn api(&self, action: &str, mut parameters: BTreeMap<String, String>) -> Result<Value> {
        parameters.extend([
            ("version".to_owned(), "1".to_owned()),
            ("type".to_owned(), "json".to_owned()),
            ("key".to_owned(), self.context.token.clone()),
        ]);
        let response = self.context.send_json(
            Method::Get,
            &format!("/api/{action}"),
            &parameters,
            None,
            BTreeMap::new(),
        )?;
        let reply = response.get("reply").cloned().unwrap_or(Value::Null);
        if reply.get("code").and_then(Value::as_str) == Some("300") {
            Ok(reply)
        } else {
            Err(Error::Provider(format!(
                "NameSilo API error {}: {}",
                reply
                    .get("code")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown"),
                self.context.logger.mask(
                    reply
                        .get("detail")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown error")
                )
            )))
        }
    }
}

impl Provider for NamesiloProvider {
    fn name(&self) -> &'static str {
        "namesilo"
    }
    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        CrudProvider::apply(self, request)
    }
}

impl CrudProvider for NamesiloProvider {
    fn context(&self) -> &ProviderContext {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let reply = match self.api(
            "getDomainInfo",
            BTreeMap::from([("domain".to_owned(), domain.to_owned())]),
        ) {
            Ok(reply) => reply,
            Err(Error::Provider(_)) => return Ok(None),
            Err(error) => return Err(error),
        };
        Ok(reply.get("domain").is_some().then(|| domain.to_owned()))
    }
    fn query_record(
        &mut self,
        _zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<Option<Value>> {
        let reply = self.api(
            "dnsListRecords",
            BTreeMap::from([("domain".to_owned(), main_domain.to_owned())]),
        )?;
        Ok(reply
            .get("resource_record")
            .and_then(Value::as_array)
            .and_then(|records| {
                records
                    .iter()
                    .find(|record| {
                        record.get("host").and_then(Value::as_str) == Some(subdomain)
                            && record.get("type").and_then(Value::as_str)
                                == Some(request.record_type.as_str())
                    })
                    .cloned()
            }))
    }
    fn create_record(
        &mut self,
        _zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<()> {
        let mut parameters = BTreeMap::from([
            ("domain".to_owned(), main_domain.to_owned()),
            ("rrtype".to_owned(), request.record_type.clone()),
            ("rrhost".to_owned(), subdomain.to_owned()),
            ("rrvalue".to_owned(), request.address.clone()),
        ]);
        if let Some(ttl) = request.ttl {
            parameters.insert("rrttl".to_owned(), ttl.to_string());
        }
        let reply = self.api("dnsAddRecord", parameters)?;
        if reply.get("record_id").is_some() {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "NameSilo failed to create record: {reply}"
            )))
        }
    }
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest,
    ) -> Result<()> {
        let record_id = record
            .get("record_id")
            .and_then(value_to_string)
            .ok_or_else(|| Error::Provider("NameSilo record has no record_id".to_owned()))?;
        let mut parameters = BTreeMap::from([
            ("rrid".to_owned(), record_id),
            ("domain".to_owned(), zone_id.to_owned()),
            (
                "rrhost".to_owned(),
                record
                    .get("host")
                    .and_then(value_to_string)
                    .unwrap_or_default(),
            ),
            ("rrvalue".to_owned(), request.address.clone()),
            ("rrtype".to_owned(), request.record_type.clone()),
        ]);
        if let Some(ttl) = request.ttl.or_else(|| {
            record
                .get("ttl")
                .and_then(value_to_string)
                .and_then(|ttl| ttl.parse::<u32>().ok())
        }) {
            parameters.insert("rrttl".to_owned(), ttl.to_string());
        }
        self.api("dnsUpdateRecord", parameters)?;
        Ok(())
    }
}

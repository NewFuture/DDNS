use std::collections::BTreeMap;

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::Method;

use super::base::{CrudProvider, ProviderContext, RecordRequest, value_to_string};

pub struct NamesiloProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
}

impl<'a> NamesiloProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        if context.token.is_empty() {
            return Err(Error::Config(
                "NameSilo API key must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
        })
    }

    fn api(&self, action: &str, mut parameters: BTreeMap<String, String>) -> Result<Option<Value>> {
        parameters.extend([
            ("version".to_owned(), "1".to_owned()),
            ("type".to_owned(), "json".to_owned()),
            ("key".to_owned(), self.context.token.to_owned()),
        ]);
        let response = self.context.send_json(
            Method::Get,
            &format!("/api/{action}"),
            &parameters,
            None,
            BTreeMap::new(),
        )?;
        let reply = response.get("reply").cloned().unwrap_or(Value::Null);
        let code = reply
            .get("code")
            .and_then(Value::as_str)
            .unwrap_or("unknown");
        match code {
            "300" => Ok(Some(reply)),
            // Code 200 means the domain is not active or not in this account.
            "200" if action == "getDomainInfo" => Ok(None),
            _ => {
                let detail = reply
                    .get("detail")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown error");
                Err(Error::Provider(
                    self.context
                        .logger
                        .mask(&format!("NameSilo API error {code}: {detail}")),
                ))
            }
        }
    }
}

impl CrudProvider for NamesiloProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        self.api(
            "getDomainInfo",
            BTreeMap::from([("domain".to_owned(), domain.to_owned())]),
        )?
        .map(|reply| {
            reply
                .get("domain")
                .filter(|value| !value.is_null())
                .map(|_| domain.to_owned())
                .ok_or_else(|| {
                    Error::Provider("NameSilo returned invalid domain information".to_owned())
                })
        })
        .transpose()
    }
    fn query_record(
        &mut self,
        _zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let reply = self
            .api(
                "dnsListRecords",
                BTreeMap::from([("domain".to_owned(), main_domain.to_owned())]),
            )?
            .ok_or_else(|| Error::Provider("NameSilo returned no record list".to_owned()))?;
        let records = reply
            .get("resource_record")
            .and_then(Value::as_array)
            .ok_or_else(|| {
                Error::Provider("NameSilo returned an invalid record list".to_owned())
            })?;
        for record in records {
            let record_host = record
                .get("host")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::Provider("NameSilo record has no host".to_owned()))?;
            let record_type = record
                .get("type")
                .and_then(Value::as_str)
                .filter(|value| !value.is_empty())
                .ok_or_else(|| Error::Provider("NameSilo record has no type".to_owned()))?;
            if record_host == subdomain && record_type == request.record_type {
                return Ok(Some(record.clone()));
            }
        }
        Ok(None)
    }
    fn create_record(
        &mut self,
        _zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut parameters = BTreeMap::from([
            ("domain".to_owned(), main_domain.to_owned()),
            ("rrtype".to_owned(), request.record_type.to_owned()),
            ("rrhost".to_owned(), subdomain.to_owned()),
            ("rrvalue".to_owned(), request.address.to_owned()),
        ]);
        if let Some(ttl) = request.ttl {
            parameters.insert("rrttl".to_owned(), ttl.to_string());
        }
        let reply = self.api("dnsAddRecord", parameters)?;
        if reply
            .as_ref()
            .and_then(|reply| reply.get("record_id"))
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "NameSilo failed to create record".to_owned(),
            ))
        }
    }
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
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
            ("rrvalue".to_owned(), request.address.to_owned()),
            ("rrtype".to_owned(), request.record_type.to_owned()),
        ]);
        if let Some(ttl) = request.ttl.or_else(|| {
            record
                .get("ttl")
                .and_then(value_to_string)
                .and_then(|ttl| ttl.parse::<u32>().ok())
        }) {
            parameters.insert("rrttl".to_owned(), ttl.to_string());
        }
        self.api("dnsUpdateRecord", parameters)?
            .map(|_| ())
            .ok_or_else(|| Error::Provider("NameSilo failed to update record".to_owned()))
    }
}

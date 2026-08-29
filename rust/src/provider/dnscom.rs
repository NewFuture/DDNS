use std::collections::BTreeMap;

use md5::{Digest, Md5};
use serde_json::Value;
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};

use super::base::{CrudProvider, ProviderContext, RecordRequest, value_to_string};

pub struct DnscomProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
}

impl<'a> DnscomProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "DNS.COM API key and secret must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
        })
    }

    fn api(&self, action: &str, mut parameters: BTreeMap<String, String>) -> Result<Value> {
        parameters.insert("apiKey".to_owned(), self.context.id.to_owned());
        parameters.insert(
            "timestamp".to_owned(),
            OffsetDateTime::now_utc().unix_timestamp().to_string(),
        );
        let canonical = form_encode(&parameters);
        let mut digest = Md5::new();
        digest.update(canonical.as_bytes());
        digest.update(self.context.token.as_bytes());
        parameters.insert("hash".to_owned(), format!("{:x}", digest.finalize()));
        let response = self.context.send_json(
            Method::Post,
            &format!("/api/{action}/"),
            &BTreeMap::new(),
            Some(form_encode(&parameters)),
            BTreeMap::from([(
                "content-type".to_owned(),
                "application/x-www-form-urlencoded".to_owned(),
            )]),
        )?;
        if response.get("code").and_then(Value::as_i64) == Some(0) {
            Ok(response.get("data").cloned().unwrap_or(Value::Null))
        } else {
            Err(Error::Provider(format!(
                "DNS.COM API error: {}",
                self.context.logger.mask(
                    response
                        .get("message")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown error")
                )
            )))
        }
    }
}

impl CrudProvider for DnscomProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        Ok(self
            .api(
                "domain/getsingle",
                BTreeMap::from([("domainID".to_owned(), domain.to_owned())]),
            )?
            .get("domainID")
            .and_then(value_to_string))
    }
    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let response = self.api(
            "record/list",
            BTreeMap::from([
                ("domainID".to_owned(), zone_id.to_owned()),
                ("host".to_owned(), subdomain.to_owned()),
                ("pageSize".to_owned(), "500".to_owned()),
            ]),
        )?;
        Ok(response
            .get("data")
            .and_then(Value::as_array)
            .and_then(|records| {
                records
                    .iter()
                    .find(|record| {
                        record.get("record").and_then(Value::as_str) == Some(subdomain)
                            && record.get("type").and_then(Value::as_str)
                                == Some(request.record_type)
                            && request.line.is_none_or(|line| {
                                record.get("viewID").and_then(value_to_string).as_deref()
                                    == Some(line)
                            })
                    })
                    .cloned()
            }))
    }
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut parameters = request
            .extra
            .iter()
            .filter_map(|(key, value)| value_to_string(value).map(|value| (key.clone(), value)))
            .collect::<BTreeMap<_, _>>();
        parameters.extend([
            ("domainID".to_owned(), zone_id.to_owned()),
            ("value".to_owned(), request.address.to_owned()),
            ("host".to_owned(), subdomain.to_owned()),
            ("type".to_owned(), request.record_type.to_owned()),
        ]);
        parameters
            .entry("remark".to_owned())
            .or_insert_with(|| "Managed by DDNS".to_owned());
        if let Some(ttl) = request.ttl {
            parameters.insert("TTL".to_owned(), ttl.to_string());
        }
        if let Some(line) = request.line {
            parameters.insert("viewID".to_owned(), line.to_owned());
        }
        if self
            .api("record/create", parameters)?
            .get("recordID")
            .is_some()
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "DNS.COM failed to create record".to_owned(),
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
            .get("recordID")
            .and_then(value_to_string)
            .ok_or_else(|| Error::Provider("DNS.COM record has no recordID".to_owned()))?;
        let mut parameters = BTreeMap::from([
            ("domainID".to_owned(), zone_id.to_owned()),
            ("recordID".to_owned(), record_id),
            ("newvalue".to_owned(), request.address.to_owned()),
        ]);
        if let Some(ttl) = request.ttl {
            parameters.insert("newTTL".to_owned(), ttl.to_string());
        }
        self.api("record/modify", parameters)?;
        Ok(())
    }
}

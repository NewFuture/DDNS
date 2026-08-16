use std::collections::BTreeMap;

use serde_json::Value;
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};
use crate::signature::{acs3_authorization, sha256_hex};

use super::base::{
    CrudProvider, Provider, ProviderContext, RecordRequest, ZoneMatch, join_domain, value_to_string,
};
use super::empty_zone_cache;

pub struct AlidnsProvider {
    context: ProviderContext,
    zones: BTreeMap<String, String>,
}

impl AlidnsProvider {
    pub fn new(context: ProviderContext) -> Result<Self> {
        if context.id.is_empty() {
            return Err(Error::Config(
                "AliDNS access key id must be configured".to_owned(),
            ));
        }
        if context.token.is_empty() {
            return Err(Error::Config(
                "AliDNS access key secret must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: empty_zone_cache(),
        })
    }

    fn api(&self, action: &str, parameters: BTreeMap<String, String>) -> Result<Value> {
        let body = form_encode(&parameters);
        let body_hash = sha256_hex(&body);
        let mut headers = BTreeMap::from([
            ("host".to_owned(), endpoint_host(&self.context.endpoint)?),
            (
                "content-type".to_owned(),
                "application/x-www-form-urlencoded".to_owned(),
            ),
            ("x-acs-action".to_owned(), action.to_owned()),
            ("x-acs-content-sha256".to_owned(), body_hash.clone()),
            ("x-acs-date".to_owned(), acs_timestamp()),
            ("x-acs-signature-nonce".to_owned(), nonce()?),
            ("x-acs-version".to_owned(), "2015-01-09".to_owned()),
        ]);
        let authorization = acs3_authorization(
            &self.context.id,
            &self.context.token,
            "POST",
            "/",
            "",
            &headers,
            &body_hash,
        )?;
        headers.insert("authorization".to_owned(), authorization);
        let response =
            self.context
                .send_json(Method::Post, "/", &BTreeMap::new(), Some(body), headers)?;
        if let Some(code) = response.get("Code").and_then(Value::as_str) {
            return Err(Error::Provider(format!(
                "AliDNS API error {code}: {}",
                response
                    .get("Message")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown error")
            )));
        }
        Ok(response)
    }

    fn parameters_with_extra(
        request: &RecordRequest,
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
}

impl Provider for AlidnsProvider {
    fn name(&self) -> &'static str {
        "alidns"
    }

    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        CrudProvider::apply(self, request)
    }
}

impl CrudProvider for AlidnsProvider {
    fn context(&self) -> &ProviderContext {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn split_zone_and_sub(&mut self, domain: &str) -> Result<ZoneMatch> {
        if let Some((subdomain, main_domain)) = super::base::split_custom_domain(domain) {
            return Ok(ZoneMatch {
                zone_id: main_domain.clone(),
                subdomain,
                main_domain,
            });
        }
        let response = self.api(
            "GetMainDomainName",
            BTreeMap::from([("InputString".to_owned(), domain.to_owned())]),
        )?;
        let main_domain = response
            .get("DomainName")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::Provider(format!("AliDNS could not split domain `{domain}`")))?
            .to_owned();
        let subdomain = response
            .get("RR")
            .and_then(Value::as_str)
            .unwrap_or("@")
            .to_owned();
        Ok(ZoneMatch {
            zone_id: main_domain.clone(),
            subdomain,
            main_domain,
        })
    }

    fn query_zone_id(&mut self, _domain: &str) -> Result<Option<String>> {
        Err(Error::Provider(
            "AliDNS obtains the main domain through GetMainDomainName".to_owned(),
        ))
    }

    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<Option<Value>> {
        let parameters = Self::parameters_with_extra(
            request,
            [
                ("SubDomain", Some(join_domain(subdomain, main_domain))),
                ("DomainName", Some(main_domain.to_owned())),
                ("Type", Some(request.record_type.clone())),
                ("Line", request.line.clone()),
                ("PageSize", Some("500".to_owned())),
                ("Lang", request.extra.get("Lang").and_then(value_to_string)),
                (
                    "Status",
                    request.extra.get("Status").and_then(value_to_string),
                ),
            ],
        );
        let response = self.api("DescribeSubDomainRecords", parameters)?;
        let record = response
            .pointer("/DomainRecords/Record")
            .and_then(Value::as_array)
            .and_then(|records| records.first())
            .cloned();
        if record.is_none() {
            self.context.logger.info(
                "alidns",
                format!("no {} record found in zone {zone_id}", request.record_type),
            );
        }
        Ok(record)
    }

    fn create_record(
        &mut self,
        _zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest,
    ) -> Result<()> {
        let parameters = Self::parameters_with_extra(
            request,
            [
                ("DomainName", Some(main_domain.to_owned())),
                ("RR", Some(subdomain.to_owned())),
                ("Value", Some(request.address.clone())),
                ("Type", Some(request.record_type.clone())),
                ("TTL", request.ttl.map(|ttl| ttl.to_string())),
                ("Line", request.line.clone()),
            ],
        );
        let response = self.api("AddDomainRecord", parameters)?;
        if response.get("RecordId").is_some() {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "AliDNS failed to create record: {response}"
            )))
        }
    }

    fn update_record(
        &mut self,
        _zone_id: &str,
        record: &Value,
        request: &RecordRequest,
    ) -> Result<()> {
        let unchanged = record.get("Value").and_then(Value::as_str)
            == Some(request.address.as_str())
            && record.get("Type").and_then(Value::as_str) == Some(request.record_type.as_str())
            && request.ttl.is_none_or(|ttl| {
                record
                    .get("TTL")
                    .and_then(Value::as_u64)
                    .is_some_and(|old| old == u64::from(ttl))
            });
        if unchanged {
            self.context
                .logger
                .info("alidns", "record already has the requested value");
            return Ok(());
        }
        let parameters = Self::parameters_with_extra(
            request,
            [
                ("RecordId", record.get("RecordId").and_then(value_to_string)),
                ("Value", Some(request.address.clone())),
                ("RR", record.get("RR").and_then(value_to_string)),
                ("Type", Some(request.record_type.clone())),
                ("TTL", request.ttl.map(|ttl| ttl.to_string())),
                (
                    "Line",
                    request
                        .line
                        .clone()
                        .or_else(|| record.get("Line").and_then(value_to_string)),
                ),
            ],
        );
        let response = self.api("UpdateDomainRecord", parameters)?;
        if response.get("RecordId").is_some() {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "AliDNS failed to update record: {response}"
            )))
        }
    }
}

fn endpoint_host(endpoint: &str) -> Result<String> {
    endpoint
        .split_once("://")
        .map(|(_, remainder)| remainder)
        .unwrap_or(endpoint)
        .split('/')
        .next()
        .filter(|host| !host.is_empty())
        .map(ToOwned::to_owned)
        .ok_or_else(|| Error::Config(format!("invalid AliDNS endpoint `{endpoint}`")))
}

fn acs_timestamp() -> String {
    let now = OffsetDateTime::now_utc();
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        now.year(),
        u8::from(now.month()),
        now.day(),
        now.hour(),
        now.minute(),
        now.second()
    )
}

fn nonce() -> Result<String> {
    let mut bytes = [0_u8; 16];
    getrandom::fill(&mut bytes)
        .map_err(|error| Error::Provider(format!("failed to generate request nonce: {error}")))?;
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(hex(byte >> 4));
        output.push(hex(byte & 0x0f));
    }
    Ok(output)
}

const fn hex(value: u8) -> char {
    match value {
        0..=9 => (b'0' + value) as char,
        _ => (b'a' + value - 10) as char,
    }
}

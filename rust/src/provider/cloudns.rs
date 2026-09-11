use std::collections::BTreeMap;

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};

use super::base::{CrudProvider, ProviderContext, RecordRequest, value_to_string};

pub struct CloudnsProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
}

impl<'a> CloudnsProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "ClouDNS auth id and password must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
        })
    }

    fn api(&self, path: &str, mut parameters: BTreeMap<String, String>) -> Result<Option<Value>> {
        parameters.insert("auth-id".to_owned(), self.context.id.to_owned());
        parameters.insert("auth-password".to_owned(), self.context.token.to_owned());
        let response = self.context.send_json(
            Method::Post,
            path,
            &BTreeMap::new(),
            Some(form_encode(&parameters)),
            BTreeMap::from([(
                "content-type".to_owned(),
                "application/x-www-form-urlencoded".to_owned(),
            )]),
        )?;
        if response.get("status").and_then(Value::as_str) == Some("Failed") {
            let description = response
                .get("statusDescription")
                .and_then(Value::as_str)
                .unwrap_or("unknown error");
            // This exact lookup miss is documented at cloudns.net/wiki/article/134/.
            if path == "/dns/get-zone-info.json" && description == "Missing domain-name" {
                return Ok(None);
            }
            return Err(Error::Provider(format!(
                "ClouDNS API error: {}",
                self.context.logger.mask(description)
            )));
        }
        Ok(Some(response))
    }
}

impl CrudProvider for CloudnsProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        self.api(
            "/dns/get-zone-info.json",
            BTreeMap::from([("domain-name".to_owned(), domain.to_owned())]),
        )?
        .map(|response| {
            if response.get("name").and_then(Value::as_str) == Some(domain) {
                Ok(domain.to_owned())
            } else {
                Err(Error::Provider(
                    "ClouDNS returned invalid zone information".to_owned(),
                ))
            }
        })
        .transpose()
    }

    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let host = if subdomain == "@" { "" } else { subdomain };
        let response = self
            .api(
                "/dns/records.json",
                BTreeMap::from([
                    ("domain-name".to_owned(), zone_id.to_owned()),
                    ("host".to_owned(), host.to_owned()),
                    ("type".to_owned(), request.record_type.to_owned()),
                ]),
            )?
            .ok_or_else(|| Error::Provider("ClouDNS returned no record list".to_owned()))?;
        // The API also uses [] for an empty record collection.
        if response.as_array().is_some_and(Vec::is_empty) {
            return Ok(None);
        }
        let records = response
            .as_object()
            .ok_or_else(|| Error::Provider("ClouDNS returned an invalid record list".to_owned()))?;
        for record in records.values() {
            let record_host = record
                .get("host")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::Provider("ClouDNS record has no host".to_owned()))?;
            let record_type = record
                .get("type")
                .and_then(Value::as_str)
                .filter(|value| !value.is_empty())
                .ok_or_else(|| Error::Provider("ClouDNS record has no type".to_owned()))?;
            let matches_host =
                record_host == host || (subdomain == "@" && matches!(record_host, "" | "@"));
            if matches_host && record_type == request.record_type {
                return Ok(Some(record.clone()));
            }
        }
        Ok(None)
    }

    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let response = self.api(
            "/dns/add-record.json",
            BTreeMap::from([
                ("domain-name".to_owned(), zone_id.to_owned()),
                ("record-type".to_owned(), request.record_type.to_owned()),
                (
                    "host".to_owned(),
                    if subdomain == "@" { "" } else { subdomain }.to_owned(),
                ),
                ("record".to_owned(), request.address.to_owned()),
                ("ttl".to_owned(), request.ttl.unwrap_or(60).to_string()),
            ]),
        )?;
        if response
            .as_ref()
            .and_then(|response| response.get("status"))
            .and_then(Value::as_str)
            == Some("Success")
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "ClouDNS failed to create record".to_owned(),
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
            .get("id")
            .and_then(value_to_string)
            .ok_or_else(|| Error::Provider("ClouDNS record has no id".to_owned()))?;
        let response = self.api(
            "/dns/mod-record.json",
            BTreeMap::from([
                ("domain-name".to_owned(), zone_id.to_owned()),
                ("record-id".to_owned(), record_id),
                (
                    "host".to_owned(),
                    record
                        .get("host")
                        .and_then(value_to_string)
                        .unwrap_or_default(),
                ),
                ("record".to_owned(), request.address.to_owned()),
                ("ttl".to_owned(), request.ttl.unwrap_or(60).to_string()),
            ]),
        )?;
        if response
            .as_ref()
            .and_then(|response| response.get("status"))
            .and_then(Value::as_str)
            == Some("Success")
        {
            Ok(())
        } else {
            Err(Error::Provider(
                "ClouDNS failed to update record".to_owned(),
            ))
        }
    }
}

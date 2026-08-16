use std::collections::BTreeMap;

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};

use super::base::{CrudProvider, Provider, ProviderContext, RecordRequest, value_to_string};
use super::empty_zone_cache;

pub struct DnspodProvider {
    context: ProviderContext,
    zones: BTreeMap<String, String>,
}

impl DnspodProvider {
    pub fn new(context: ProviderContext) -> Result<Self> {
        if context.id.is_empty() {
            return Err(Error::Config("DNSPod id must be configured".to_owned()));
        }
        if context.token.is_empty() {
            return Err(Error::Config("DNSPod token must be configured".to_owned()));
        }
        Ok(Self {
            context,
            zones: empty_zone_cache(),
        })
    }

    fn api(&self, action: &str, mut parameters: BTreeMap<String, String>) -> Result<Value> {
        parameters.insert(
            "login_token".to_owned(),
            format!("{},{}", self.context.id, self.context.token),
        );
        parameters.insert("format".to_owned(), "json".to_owned());
        let headers = BTreeMap::from([(
            "content-type".to_owned(),
            "application/x-www-form-urlencoded".to_owned(),
        )]);
        let response = self.context.send_json(
            Method::Post,
            &format!("/{action}"),
            &BTreeMap::new(),
            Some(form_encode(&parameters)),
            headers,
        )?;
        let status_code = response
            .pointer("/status/code")
            .and_then(value_to_string)
            .unwrap_or_else(|| "unknown".to_owned());
        let zone_candidate_miss =
            action == "Domain.Info" && matches!(status_code.as_str(), "6" | "7" | "8");
        if status_code == "1"
            || (action == "Record.List" && status_code == "10")
            || zone_candidate_miss
        {
            return Ok(response);
        }
        let message = response
            .pointer("/status/message")
            .and_then(Value::as_str)
            .unwrap_or("unknown error");
        Err(Error::Provider(format!(
            "DNSPod API error {status_code}: {}",
            self.context.logger.mask(message)
        )))
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

impl Provider for DnspodProvider {
    fn name(&self) -> &'static str {
        "dnspod"
    }

    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        CrudProvider::apply(self, request)
    }
}

impl CrudProvider for DnspodProvider {
    fn context(&self) -> &ProviderContext {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let response = self.api(
            "Domain.Info",
            BTreeMap::from([("domain".to_owned(), domain.to_owned())]),
        )?;
        Ok(response.pointer("/domain/id").and_then(value_to_string))
    }

    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest,
    ) -> Result<Option<Value>> {
        let mut parameters = BTreeMap::from([
            ("domain_id".to_owned(), zone_id.to_owned()),
            ("sub_domain".to_owned(), subdomain.to_owned()),
            ("record_type".to_owned(), request.record_type.clone()),
        ]);
        if let Some(line) = &request.line {
            parameters.insert("line".to_owned(), line.clone());
        }
        let response = self.api("Record.List", parameters)?;
        let records = response
            .get("records")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        Ok(if records.len() <= 1 {
            records.into_iter().next()
        } else {
            records
                .into_iter()
                .find(|record| record.get("name").and_then(Value::as_str) == Some(subdomain))
        })
    }

    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest,
    ) -> Result<()> {
        let parameters = Self::parameters_with_extra(
            request,
            [
                ("domain_id", Some(zone_id.to_owned())),
                ("sub_domain", Some(subdomain.to_owned())),
                ("value", Some(request.address.clone())),
                ("record_type", Some(request.record_type.clone())),
                (
                    "record_line",
                    Some(request.line.clone().unwrap_or_else(|| "默认".to_owned())),
                ),
                ("ttl", request.ttl.map(|ttl| ttl.to_string())),
            ],
        );
        let response = self.api("Record.Create", parameters)?;
        if response.get("record").is_some() {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "DNSPod failed to create record: {response}"
            )))
        }
    }

    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest,
    ) -> Result<()> {
        let record_line = request
            .line
            .clone()
            .or_else(|| {
                record
                    .get("line")
                    .and_then(Value::as_str)
                    .map(ToOwned::to_owned)
            })
            .unwrap_or_else(|| "默认".to_owned())
            .replace("Default", "default");
        let parameters = Self::parameters_with_extra(
            request,
            [
                ("domain_id", Some(zone_id.to_owned())),
                ("record_id", record.get("id").and_then(value_to_string)),
                ("sub_domain", record.get("name").and_then(value_to_string)),
                ("record_type", Some(request.record_type.clone())),
                ("value", Some(request.address.clone())),
                ("record_line", Some(record_line)),
                ("ttl", request.ttl.map(|ttl| ttl.to_string())),
            ],
        );
        let response = self.api("Record.Modify", parameters)?;
        if response.get("record").is_some() {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "DNSPod failed to update record: {response}"
            )))
        }
    }
}

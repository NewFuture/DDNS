use std::collections::BTreeMap;

use serde_json::{Map, Value, json};

use crate::error::{Error, Result};
use crate::http::{Method, form_encode};

use super::base::{CrudProvider, ProviderContext, RecordRequest, json_parameters, value_to_string};

pub struct DnspodProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
    default_line: &'static str,
}

impl<'a> DnspodProvider<'a> {
    pub fn new(context: ProviderContext<'a>) -> Result<Self> {
        Self::with_settings(context, "默认")
    }

    pub fn global(context: ProviderContext<'a>) -> Result<Self> {
        Self::with_settings(context, "default")
    }

    fn with_settings(context: ProviderContext<'a>, default_line: &'static str) -> Result<Self> {
        if context.id.is_empty() {
            return Err(Error::Config("DNSPod id must be configured".to_owned()));
        }
        if context.token.is_empty() {
            return Err(Error::Config("DNSPod token must be configured".to_owned()));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
            default_line,
        })
    }

    fn api(&self, action: &str, parameters: Map<String, Value>) -> Result<Value> {
        let mut parameters = parameters
            .into_iter()
            .filter_map(|(key, value)| value_to_string(&value).map(|value| (key, value)))
            .collect::<BTreeMap<_, _>>();
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
}

impl CrudProvider for DnspodProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }

    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }

    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        let response = self.api(
            "Domain.Info",
            Map::from_iter([("domain".to_owned(), json!(domain))]),
        )?;
        Ok(response.pointer("/domain/id").and_then(value_to_string))
    }

    fn query_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        _main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<Option<Value>> {
        let mut parameters = Map::from_iter([
            ("domain_id".to_owned(), json!(zone_id)),
            ("sub_domain".to_owned(), json!(subdomain)),
            ("record_type".to_owned(), json!(request.record_type)),
        ]);
        if let Some(line) = request.line {
            parameters.insert("line".to_owned(), json!(line));
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
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut parameters = Map::from_iter([
            ("domain_id".to_owned(), json!(zone_id)),
            ("sub_domain".to_owned(), json!(subdomain)),
            ("value".to_owned(), json!(request.address)),
            ("record_type".to_owned(), json!(request.record_type)),
            (
                "record_line".to_owned(),
                json!(request.line.unwrap_or(self.default_line)),
            ),
            ("ttl".to_owned(), json!(request.ttl)),
        ]);
        // DNSPod applies extras last, before omitting null/non-scalar form values.
        parameters.extend(json_parameters(request));
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
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let record_line = request
            .line
            .or_else(|| record.get("line").and_then(Value::as_str))
            .unwrap_or(self.default_line)
            .replace("Default", "default");
        let mut parameters = Map::from_iter([
            ("domain_id".to_owned(), json!(zone_id)),
            ("record_id".to_owned(), json!(record.get("id"))),
            ("sub_domain".to_owned(), json!(record.get("name"))),
            ("record_type".to_owned(), json!(request.record_type)),
            ("value".to_owned(), json!(request.address)),
            ("record_line".to_owned(), json!(record_line)),
            ("ttl".to_owned(), json!(request.ttl)),
        ]);
        parameters.extend(json_parameters(request));
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

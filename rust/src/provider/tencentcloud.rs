use std::collections::BTreeMap;

use serde_json::{Map, Value, json};
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::Method;
use crate::signature::{hmac_sha256, sha256_hex, tc3_authorization};

use super::base::{
    CrudProvider, ProviderContext, RecordRequest, endpoint_host, join_domain, numeric_id,
    value_to_string,
};

pub struct TencentCloudProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
    service: &'static str,
    version: &'static str,
    edgeone_dns: bool,
}

impl<'a> TencentCloudProvider<'a> {
    pub fn new(
        context: ProviderContext<'a>,
        service: &'static str,
        version: &'static str,
        edgeone_dns: bool,
    ) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "Tencent Cloud secret id and secret key must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
            service,
            version,
            edgeone_dns,
        })
    }

    fn api(&self, action: &str, values: Map<String, Value>) -> Result<Value> {
        let body = serde_json::to_string(&Value::Object(values))?;
        let now = OffsetDateTime::now_utc();
        let timestamp = now.unix_timestamp().to_string();
        let date = format!(
            "{:04}-{:02}-{:02}",
            now.year(),
            u8::from(now.month()),
            now.day()
        );
        let scope = format!("{date}/{}/tc3_request", self.service);
        let secret_date = hmac_sha256(format!("TC3{}", self.context.token), &date)?;
        let secret_service = hmac_sha256(secret_date, self.service)?;
        let secret_signing = hmac_sha256(secret_service, "tc3_request")?;
        let headers = BTreeMap::from([
            ("content-type".to_owned(), "application/json".to_owned()),
            (
                "host".to_owned(),
                endpoint_host(&self.context.endpoint, "Tencent Cloud")?,
            ),
        ]);
        let authorization = tc3_authorization(
            secret_signing,
            &timestamp,
            &self.context.id,
            &scope,
            "POST",
            "/",
            "",
            &headers,
            &sha256_hex(&body),
        )?;
        let mut headers = headers;
        headers.extend([
            ("x-tc-action".to_owned(), action.to_owned()),
            ("x-tc-version".to_owned(), self.version.to_owned()),
            ("x-tc-timestamp".to_owned(), timestamp),
            ("authorization".to_owned(), authorization),
        ]);
        let response =
            self.context
                .send_json(Method::Post, "/", &BTreeMap::new(), Some(body), headers)?;
        let response = response.get("Response").cloned().ok_or_else(|| {
            Error::Provider("Tencent Cloud returned an invalid response".to_owned())
        })?;
        if let Some(error) = response.get("Error") {
            return Err(Error::Provider(format!(
                "Tencent Cloud API error {}: {}",
                error
                    .get("Code")
                    .and_then(Value::as_str)
                    .unwrap_or("Unknown"),
                self.context.logger.mask(
                    error
                        .get("Message")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown error")
                )
            )));
        }
        Ok(response)
    }

    fn extra(request: &RecordRequest<'_>) -> Map<String, Value> {
        super::base::json_parameters(request)
    }

    fn edgeone_dns_request(&self, request: &RecordRequest<'_>) -> bool {
        request
            .extra
            .get("teoDomainType")
            .and_then(Value::as_str)
            .map_or(self.edgeone_dns, |value| value.eq_ignore_ascii_case("dns"))
    }
}

impl CrudProvider for TencentCloudProvider<'_> {
    fn context(&self) -> &ProviderContext<'_> {
        &self.context
    }
    fn zone_cache(&mut self) -> &mut BTreeMap<String, String> {
        &mut self.zones
    }
    fn query_zone_id(&mut self, domain: &str) -> Result<Option<String>> {
        if self.service == "dnspod" {
            return Ok(self
                .api(
                    "DescribeDomain",
                    Map::from_iter([("Domain".to_owned(), json!(domain))]),
                )?
                .pointer("/DomainInfo/DomainId")
                .and_then(value_to_string));
        }
        let response = self.api(
            "DescribeZones",
            Map::from_iter([(
                "Filters".to_owned(),
                json!([{"Name": "zone-name", "Values": [domain], "Fuzzy": false}]),
            )]),
        )?;
        Ok(response
            .get("Zones")
            .and_then(Value::as_array)
            .and_then(|zones| {
                zones
                    .iter()
                    .find(|zone| zone.get("ZoneName").and_then(Value::as_str) == Some(domain))
                    .and_then(|zone| zone.get("ZoneId"))
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
        if self.service == "dnspod" {
            let mut values = Self::extra(request);
            values.extend([
                (
                    "DomainId".to_owned(),
                    json!(numeric_id(zone_id, "Tencent Cloud domain id")?),
                ),
                ("Subdomain".to_owned(), json!(subdomain)),
                ("Domain".to_owned(), json!(main_domain)),
                ("RecordType".to_owned(), json!(request.record_type)),
            ]);
            if let Some(line) = request.line {
                values.insert("RecordLine".to_owned(), json!(line));
            }
            return Ok(self
                .api("DescribeRecordList", values)?
                .get("RecordList")
                .and_then(Value::as_array)
                .and_then(|records| {
                    records
                        .iter()
                        .find(|record| {
                            record.get("Name").and_then(Value::as_str) == Some(subdomain)
                                && record.get("Type").and_then(Value::as_str)
                                    == Some(request.record_type)
                        })
                        .cloned()
                }));
        }
        let domain = join_domain(subdomain, main_domain);
        let edgeone_dns = self.edgeone_dns_request(request);
        let (action, list_key, filter_name) = if edgeone_dns {
            ("DescribeDnsRecords", "DnsRecords", "name")
        } else {
            (
                "DescribeAccelerationDomains",
                "AccelerationDomains",
                "domain-name",
            )
        };
        let response = self.api(
            action,
            Map::from_iter([
                ("ZoneId".to_owned(), json!(zone_id)),
                (
                    "Filters".to_owned(),
                    json!([{"Name": filter_name, "Values": [domain], "Fuzzy": false}]),
                ),
            ]),
        )?;
        Ok(response
            .get(list_key)
            .and_then(Value::as_array)
            .and_then(|records| {
                records
                    .iter()
                    .find(|record| {
                        if edgeone_dns {
                            record.get("Name").and_then(Value::as_str) == Some(domain.as_str())
                                && record.get("Type").and_then(Value::as_str)
                                    == Some(request.record_type)
                        } else {
                            record.get("DomainName").and_then(Value::as_str)
                                == Some(domain.as_str())
                        }
                    })
                    .cloned()
            }))
    }
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut values = Self::extra(request);
        if self.service == "dnspod" {
            values
                .entry("Remark".to_owned())
                .or_insert_with(|| json!("Managed by DDNS"));
            values.extend([
                ("Domain".to_owned(), json!(main_domain)),
                (
                    "DomainId".to_owned(),
                    json!(numeric_id(zone_id, "Tencent Cloud domain id")?),
                ),
                ("SubDomain".to_owned(), json!(subdomain)),
                ("RecordType".to_owned(), json!(request.record_type)),
                ("Value".to_owned(), json!(request.address)),
                (
                    "RecordLine".to_owned(),
                    json!(request.line.unwrap_or("默认")),
                ),
            ]);
            if let Some(ttl) = request.ttl {
                values.insert("TTL".to_owned(), json!(ttl));
            }
            if self.api("CreateRecord", values)?.get("RecordId").is_some() {
                return Ok(());
            }
        } else if self.edgeone_dns_request(request) {
            values.remove("teoDomainType");
            values.extend([
                ("ZoneId".to_owned(), json!(zone_id)),
                (
                    "Name".to_owned(),
                    json!(join_domain(subdomain, main_domain)),
                ),
                ("Type".to_owned(), json!(request.record_type)),
                ("Content".to_owned(), json!(request.address)),
            ]);
            self.api("CreateDnsRecord", values)?;
            return Ok(());
        } else {
            values.remove("teoDomainType");
            values.extend([
                ("ZoneId".to_owned(), json!(zone_id)),
                (
                    "DomainName".to_owned(),
                    json!(join_domain(subdomain, main_domain)),
                ),
                (
                    "OriginInfo".to_owned(),
                    json!({"OriginType": "IP_DOMAIN", "Origin": request.address}),
                ),
            ]);
            self.api("CreateAccelerationDomain", values)?;
            return Ok(());
        }
        Err(Error::Provider(
            "Tencent Cloud failed to create record".to_owned(),
        ))
    }
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut values = Self::extra(request);
        if self.service == "dnspod" {
            values
                .entry("Remark".to_owned())
                .or_insert_with(|| json!("Managed by DDNS"));
            let domain_id = match record.get("DomainId") {
                Some(domain_id) => domain_id.clone(),
                None => json!(numeric_id(zone_id, "Tencent Cloud domain id")?),
            };
            values.extend([
                (
                    "Domain".to_owned(),
                    record.get("Domain").cloned().unwrap_or(Value::Null),
                ),
                ("DomainId".to_owned(), domain_id),
                (
                    "SubDomain".to_owned(),
                    record.get("Name").cloned().unwrap_or(Value::Null),
                ),
                (
                    "RecordId".to_owned(),
                    record.get("RecordId").cloned().unwrap_or(Value::Null),
                ),
                ("RecordType".to_owned(), json!(request.record_type)),
                (
                    "RecordLine".to_owned(),
                    record
                        .get("Line")
                        .cloned()
                        .unwrap_or_else(|| json!(request.line.unwrap_or("默认"))),
                ),
                ("Value".to_owned(), json!(request.address)),
            ]);
            if let Some(ttl) = request.ttl {
                values.insert("TTL".to_owned(), json!(ttl));
            }
            self.api("ModifyRecord", values)?;
            return Ok(());
        }
        values.remove("teoDomainType");
        values.insert("ZoneId".to_owned(), json!(zone_id));
        if self.edgeone_dns_request(request) {
            values.insert(
                "DnsRecords".to_owned(),
                json!([{
                    "RecordId": record.get("RecordId"),
                    "Name": record.get("Name"),
                    "Type": request.record_type,
                    "Content": request.address
                }]),
            );
            self.api("ModifyDnsRecords", values)?;
        } else {
            values.extend([
                (
                    "DomainName".to_owned(),
                    record.get("DomainName").cloned().unwrap_or(Value::Null),
                ),
                (
                    "OriginInfo".to_owned(),
                    json!({
                        "OriginType": "IP_DOMAIN",
                        "Origin": request.address,
                        "BackupOrigin": record.pointer("/OriginDetail/BackupOrigin").and_then(Value::as_str).unwrap_or("")
                    }),
                ),
            ]);
            self.api("ModifyAccelerationDomain", values)?;
        }
        Ok(())
    }
}

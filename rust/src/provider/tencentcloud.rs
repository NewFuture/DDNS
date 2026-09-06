use std::collections::BTreeMap;

use serde_json::{Map, Value, json};
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::Method;
use crate::signature::{hmac_sha256, sha256_hex, tc3_authorization};

use super::base::{
    CrudProvider, ProviderContext, RecordRequest, endpoint_host, join_domain, json_parameters,
    numeric_id, value_to_string,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TencentKind {
    Dnspod,
    EdgeOne,
    EdgeOneDns,
}

pub struct TencentCloudProvider<'a> {
    context: ProviderContext<'a>,
    zones: BTreeMap<String, String>,
    kind: TencentKind,
}

impl<'a> TencentCloudProvider<'a> {
    pub fn new(context: ProviderContext<'a>, kind: TencentKind) -> Result<Self> {
        if context.id.is_empty() || context.token.is_empty() {
            return Err(Error::Config(
                "Tencent Cloud secret id and secret key must be configured".to_owned(),
            ));
        }
        Ok(Self {
            context,
            zones: BTreeMap::new(),
            kind,
        })
    }

    fn api(&self, action: &str, values: Map<String, Value>) -> Result<Option<Value>> {
        let (service, version) = match self.kind {
            TencentKind::Dnspod => ("dnspod", "2021-03-23"),
            TencentKind::EdgeOne | TencentKind::EdgeOneDns => ("teo", "2022-09-01"),
        };
        let body = serde_json::to_string(&Value::Object(values))?;
        let now = OffsetDateTime::now_utc();
        let timestamp = now.unix_timestamp().to_string();
        let date = format!(
            "{:04}-{:02}-{:02}",
            now.year(),
            u8::from(now.month()),
            now.day()
        );
        let scope = format!("{date}/{service}/tc3_request");
        let secret_date = hmac_sha256(format!("TC3{}", self.context.token), &date)?;
        let secret_service = hmac_sha256(secret_date, service)?;
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
            ("x-tc-version".to_owned(), version.to_owned()),
            ("x-tc-timestamp".to_owned(), timestamp),
            ("authorization".to_owned(), authorization),
        ]);
        let response =
            self.context
                .send_json(Method::Post, "/", &BTreeMap::new(), Some(body), headers)?;
        let response = response
            .get("Response")
            .filter(|response| response.is_object())
            .cloned()
            .ok_or_else(|| {
                Error::Provider("Tencent Cloud returned an invalid response".to_owned())
            })?;
        if let Some(error) = response.get("Error") {
            let code = error
                .get("Code")
                .and_then(Value::as_str)
                .unwrap_or("Unknown");
            // Only documented lookup misses are absence; HTTP/auth/permission errors still fail.
            // https://cloud.tencent.com/document/api/1427/56173 and /56166
            if self.kind == TencentKind::Dnspod
                && matches!(
                    (action, code),
                    (
                        "DescribeDomain",
                        "InvalidParameter.DomainInvalid" | "InvalidParameterValue.DomainNotExists"
                    ) | ("DescribeRecordList", "ResourceNotFound.NoDataOfRecord")
                )
            {
                return Ok(None);
            }
            let message = error
                .get("Message")
                .and_then(Value::as_str)
                .unwrap_or("unknown error");
            return Err(Error::Provider(
                self.context
                    .logger
                    .mask(&format!("Tencent Cloud API error {code}: {message}")),
            ));
        }
        Ok(Some(response))
    }

    fn mutate(&self, action: &str, values: Map<String, Value>) -> Result<()> {
        let response = self.api(action, values)?;
        let (id_key, valid) = match self.kind {
            TencentKind::Dnspod => (
                "RecordId",
                response
                    .as_ref()
                    .and_then(|response| response.get("RecordId"))
                    .and_then(value_to_string)
                    .is_some_and(|id| id.parse::<u64>().is_ok()),
            ),
            TencentKind::EdgeOne | TencentKind::EdgeOneDns => (
                "RequestId",
                response
                    .as_ref()
                    .and_then(|response| response.get("RequestId"))
                    .and_then(Value::as_str)
                    .is_some_and(|id| !id.is_empty()),
            ),
        };
        if valid {
            Ok(())
        } else {
            Err(Error::Provider(format!(
                "Tencent Cloud {action} response has no valid {id_key}"
            )))
        }
    }

    fn edgeone_dns_request(&self, request: &RecordRequest<'_>) -> bool {
        request
            .extra
            .get("teoDomainType")
            .and_then(Value::as_str)
            .map_or(self.kind == TencentKind::EdgeOneDns, |value| {
                value.eq_ignore_ascii_case("dns")
            })
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
        let (action, values) = if self.kind == TencentKind::Dnspod {
            (
                "DescribeDomain",
                Map::from_iter([("Domain".to_owned(), json!(domain))]),
            )
        } else {
            (
                "DescribeZones",
                Map::from_iter([(
                    "Filters".to_owned(),
                    json!([{"Name": "zone-name", "Values": [domain], "Fuzzy": false}]),
                )]),
            )
        };
        let Some(response) = self.api(action, values)? else {
            return Ok(None);
        };
        if self.kind == TencentKind::Dnspod {
            return response
                .pointer("/DomainInfo/DomainId")
                .and_then(value_to_string)
                .filter(|id| id.parse::<u64>().is_ok())
                .map(Some)
                .ok_or_else(|| {
                    Error::Provider("Tencent Cloud response has no valid DomainId".to_owned())
                });
        }
        let zones = response
            .get("Zones")
            .and_then(Value::as_array)
            .ok_or_else(|| {
                Error::Provider("Tencent Cloud returned an invalid zone list".to_owned())
            })?;
        for zone in zones {
            let name = zone
                .get("ZoneName")
                .and_then(Value::as_str)
                .ok_or_else(|| Error::Provider("Tencent Cloud zone has no name".to_owned()))?;
            let id = zone
                .get("ZoneId")
                .and_then(Value::as_str)
                .filter(|id| !id.is_empty())
                .ok_or_else(|| {
                    Error::Provider("Tencent Cloud zone has no valid ZoneId".to_owned())
                })?;
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
        let dnspod = self.kind == TencentKind::Dnspod;
        let acceleration = !dnspod && !self.edgeone_dns_request(request);
        let name = if dnspod {
            if subdomain.is_empty() { "@" } else { subdomain }.to_owned()
        } else {
            join_domain(subdomain, main_domain)
        };
        let (action, list_key, values) = if dnspod {
            let mut values = json_parameters(request);
            values.extend([
                (
                    "DomainId".to_owned(),
                    json!(numeric_id(zone_id, "Tencent Cloud domain id")?),
                ),
                ("Subdomain".to_owned(), json!(name)),
                ("Domain".to_owned(), json!(main_domain)),
                ("RecordType".to_owned(), json!(request.record_type)),
            ]);
            if let Some(line) = request.line {
                values.insert("RecordLine".to_owned(), json!(line));
            }
            ("DescribeRecordList", "RecordList", values)
        } else {
            let (action, list_key, filter_name) = if acceleration {
                (
                    "DescribeAccelerationDomains",
                    "AccelerationDomains",
                    "domain-name",
                )
            } else {
                ("DescribeDnsRecords", "DnsRecords", "name")
            };
            (
                action,
                list_key,
                Map::from_iter([
                    ("ZoneId".to_owned(), json!(zone_id)),
                    (
                        "Filters".to_owned(),
                        json!([{"Name": filter_name, "Values": [name], "Fuzzy": false}]),
                    ),
                ]),
            )
        };
        let Some(response) = self.api(action, values)? else {
            return Ok(None);
        };
        let records = response
            .get(list_key)
            .and_then(Value::as_array)
            .ok_or_else(|| {
                Error::Provider("Tencent Cloud returned an invalid record list".to_owned())
            })?;
        let name_key = if acceleration { "DomainName" } else { "Name" };
        for record in records {
            let record_name = record
                .get(name_key)
                .and_then(Value::as_str)
                .ok_or_else(|| Error::Provider("Tencent Cloud record has no name".to_owned()))?;
            let type_matches = acceleration
                || record.get("Type").and_then(Value::as_str).ok_or_else(|| {
                    Error::Provider("Tencent Cloud record has no type".to_owned())
                })? == request.record_type;
            if record_name == name && type_matches {
                return Ok(Some(record.clone()));
            }
        }
        Ok(None)
    }
    fn create_record(
        &mut self,
        zone_id: &str,
        subdomain: &str,
        main_domain: &str,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut values = json_parameters(request);
        let action = if self.kind == TencentKind::Dnspod {
            let subdomain = if subdomain.is_empty() { "@" } else { subdomain };
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
            "CreateRecord"
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
            "CreateDnsRecord"
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
            "CreateAccelerationDomain"
        };
        self.mutate(action, values)
    }
    fn update_record(
        &mut self,
        zone_id: &str,
        record: &Value,
        request: &RecordRequest<'_>,
    ) -> Result<()> {
        let mut values = json_parameters(request);
        if self.kind == TencentKind::Dnspod {
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
            return self.mutate("ModifyRecord", values);
        }
        values.remove("teoDomainType");
        values.insert("ZoneId".to_owned(), json!(zone_id));
        let action = if self.edgeone_dns_request(request) {
            values.insert(
                "DnsRecords".to_owned(),
                json!([{
                    "RecordId": record.get("RecordId"),
                    "Name": record.get("Name"),
                    "Type": request.record_type,
                    "Content": request.address
                }]),
            );
            "ModifyDnsRecords"
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
            "ModifyAccelerationDomain"
        };
        self.mutate(action, values)
    }
}

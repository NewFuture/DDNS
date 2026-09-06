mod common;

use std::collections::BTreeMap;
use std::sync::Arc;

use common::{FakeHttpClient, config, logger, request};
use ddns_rs::error::Result;
use ddns_rs::http::{HttpResponse, Method};
use ddns_rs::logging::{Level, Logger};
use ddns_rs::provider::{ProviderId, RecordRequest, build};
use serde_json::{Value, json};

fn json_responses(values: impl IntoIterator<Item = (u16, Value)>) -> Arc<FakeHttpClient> {
    FakeHttpClient::new(values.into_iter().map(|(status, body)| HttpResponse {
        status,
        reason: if status < 300 { "OK" } else { "Error" }.to_owned(),
        body: body.to_string(),
    }))
}

fn text_responses<'a>(values: impl IntoIterator<Item = (u16, &'a str)>) -> Arc<FakeHttpClient> {
    FakeHttpClient::new(values.into_iter().map(|(status, body)| HttpResponse {
        status,
        reason: if status < 300 { "OK" } else { "Error" }.to_owned(),
        body: body.to_owned(),
    }))
}

fn run(provider: &str, id: &str, token: &str, client: Arc<FakeHttpClient>) -> Result<()> {
    run_request(provider, id, token, client, request("192.0.2.45"))
}

fn run_request(
    provider: &str,
    id: &str,
    token: &str,
    client: Arc<FakeHttpClient>,
    request: RecordRequest<'_>,
) -> Result<()> {
    let mut provider = build(&config(provider, id, token), client.as_ref(), logger(token))?;
    provider.set_record(&request)
}

#[test]
fn aliases_build_their_canonical_provider() {
    for (alias, canonical) in [
        ("dnspod_cn", "dnspod"),
        ("aliyun", "alidns"),
        ("print", "debug"),
        ("dnspod_global", "dnspod_com"),
        ("tencent", "tencentcloud"),
        ("qcloud", "tencentcloud"),
        ("edgeone_acc", "edgeone"),
        ("teo_acc", "edgeone"),
        ("teo", "edgeone"),
        ("teo_dns", "edgeone_dns"),
        ("edgeone_noacc", "edgeone_dns"),
        ("esa", "aliesa"),
        ("51dns", "dnscom"),
        ("dns_com", "dnscom"),
        ("he_net", "he"),
        ("huawei", "huaweidns"),
        ("huaweicloud", "huaweidns"),
        ("namesilo_com", "namesilo"),
        ("no-ip", "noip"),
        ("noip_com", "noip"),
        ("webhook", "callback"),
        ("http", "callback"),
        ("west_cn", "west"),
        ("35cn", "west"),
    ] {
        assert_eq!(
            alias.parse::<ProviderId>().unwrap().as_str(),
            canonical,
            "{alias}"
        );
    }
}

#[test]
fn aliyun_alias_uses_alidns_default_endpoint() {
    let client = json_responses([
        (200, json!({"DomainName":"example.com","RR":"www"})),
        (200, json!({"DomainRecords":{"Record":[]}})),
        (200, json!({"RecordId":"record"})),
    ]);
    let mut alias_config = config("aliyun", "id", "secret");
    alias_config.endpoint = None;
    let mut provider = build(&alias_config, client.as_ref(), logger("secret")).unwrap();
    provider.set_record(&request("192.0.2.45")).unwrap();
    assert!(
        client
            .requests()
            .iter()
            .all(|request| request.url.starts_with("https://alidns.aliyuncs.com/"))
    );
}

#[test]
fn dnspod_com_create_and_error_are_offline() {
    let success = json_responses([
        (200, json!({"status":{"code":"1"},"domain":{"id":"zone"}})),
        (200, json!({"status":{"code":"10"},"records":[]})),
        (200, json!({"status":{"code":"1"},"record":{"id":"record"}})),
    ]);
    run("dnspod_com", "id", "secret", success.clone()).unwrap();
    assert!(success.requests()[2].url.ends_with("/Record.Create"));
    assert!(
        success.requests()[2]
            .body
            .as_deref()
            .unwrap()
            .contains("record_line=default")
    );
    let failure = json_responses([(200, json!({"status":{"code":"-1","message":"bad"}}))]);
    assert!(run("dnspod_com", "id", "secret", failure).is_err());
}

#[test]
fn tencent_and_edgeone_create_and_errors_are_offline() {
    let tencent = json_responses([
        (200, json!({"Response":{"DomainInfo":{"DomainId":7}}})),
        (200, json!({"Response":{"RecordList":[]}})),
        (200, json!({"Response":{"RecordId":8}})),
    ]);
    run("tencentcloud", "id", "secret", tencent.clone()).unwrap();
    assert_eq!(tencent.requests()[2].headers["x-tc-action"], "CreateRecord");
    let invalid_id = json_responses([(200, json!({"Response":{"DomainInfo":{"DomainId":"bad"}}}))]);
    assert!(run("tencentcloud", "id", "secret", invalid_id.clone()).is_err());
    assert_eq!(invalid_id.requests().len(), 1);
    let edgeone = json_responses([
        (
            200,
            json!({"Response":{"Zones":[{"ZoneId":"zone","ZoneName":"example.com"}]}}),
        ),
        (200, json!({"Response":{"AccelerationDomains":[]}})),
        (200, json!({"Response":{"RequestId":"request"}})),
    ]);
    run("edgeone", "id", "secret", edgeone.clone()).unwrap();
    assert_eq!(
        edgeone.requests()[2].headers["x-tc-action"],
        "CreateAccelerationDomain"
    );
    let edgeone_dns = json_responses([
        (
            200,
            json!({"Response":{"Zones":[{"ZoneId":"zone","ZoneName":"example.com"}]}}),
        ),
        (200, json!({"Response":{"DnsRecords":[]}})),
        (200, json!({"Response":{"RequestId":"request"}})),
    ]);
    run("edgeone_dns", "id", "secret", edgeone_dns.clone()).unwrap();
    assert_eq!(
        edgeone_dns.requests()[2].headers["x-tc-action"],
        "CreateDnsRecord"
    );
    let failure = json_responses([(
        200,
        json!({"Response":{"Error":{"Code":"AuthFailure","Message":"bad"}}}),
    )]);
    assert!(run("tencentcloud", "id", "secret", failure).is_err());
}

#[test]
fn tencent_documented_empty_record_error_creates() {
    let client = json_responses([
        (200, json!({"Response": {"DomainInfo": {"DomainId": 7}}})),
        (
            200,
            json!({"Response": {"Error": {"Code": "ResourceNotFound.NoDataOfRecord"}}}),
        ),
        (200, json!({"Response": {"RecordId": 8}})),
    ]);
    run("tencentcloud", "id", "secret", client.clone()).unwrap();
    let requests = client.requests();
    assert_eq!(requests.len(), 3);
    assert_eq!(requests[1].headers["x-tc-action"], "DescribeRecordList");
    assert_eq!(requests[2].headers["x-tc-action"], "CreateRecord");
    let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["DomainId"], 7);
    assert_eq!(body["SubDomain"], "www");
    assert_eq!(body["RecordLine"], "默认");
    assert_eq!(body["Value"], "192.0.2.45");
    assert_eq!(body["TTL"], 300);
}

#[test]
fn tencent_documented_domain_candidate_misses_continue_lookup() {
    for code in [
        "InvalidParameter.DomainInvalid",
        "InvalidParameterValue.DomainNotExists",
    ] {
        let client = json_responses([
            (200, json!({"Response": {"Error": {"Code": code}}})),
            (200, json!({"Response": {"DomainInfo": {"DomainId": "7"}}})),
            (200, json!({"Response": {"RecordList": []}})),
            (200, json!({"Response": {"RecordId": 8}})),
        ]);
        let mut create = request("192.0.2.45");
        create.domain = "host.example.co.uk";
        run_request("tencentcloud", "id", "secret", client.clone(), create).unwrap();
        let requests = client.requests();
        assert_eq!(requests.len(), 4, "{code}");
        for (index, domain) in [(0, "co.uk"), (1, "example.co.uk")] {
            assert_eq!(requests[index].headers["x-tc-action"], "DescribeDomain");
            let body: Value =
                serde_json::from_str(requests[index].body.as_deref().unwrap()).unwrap();
            assert_eq!(body["Domain"], domain);
        }
        let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
        assert_eq!(body["DomainId"], 7);
        assert_eq!(body["Subdomain"], "host");
        assert_eq!(requests[3].headers["x-tc-action"], "CreateRecord");
    }
}

#[test]
fn tencent_lookup_errors_are_not_absence() {
    let token = "tencent-secret";
    for stage in 0..2 {
        let mut codes = vec![
            "AuthFailure",
            "AuthFailure.SignatureFailure",
            "UnauthorizedOperation",
            "OperationDenied.NoPermissionToOperateDomain",
            "OperationDenied.DomainOwnerAllowedOnly",
            "FailedOperation",
            "InternalError",
            "ResourceNotFound",
            "ResourceNotFound.Unknown",
            "ResourceNotFound.NoDataOfRecord.Unrecognized",
            "InvalidParameter.DomainIdInvalid",
            "UnexpectedProviderError",
            token,
        ];
        // Even documented absence codes are failures outside their lookup operation.
        if stage == 0 {
            codes.push("ResourceNotFound.NoDataOfRecord");
        } else {
            codes.extend([
                "InvalidParameter.DomainInvalid",
                "InvalidParameterValue.DomainNotExists",
            ]);
        }
        for code in codes {
            let mut responses = Vec::new();
            if stage == 1 {
                responses.push((200, json!({"Response": {"DomainInfo": {"DomainId": 7}}})));
            }
            responses.push((
                200,
                json!({"Response": {
                    "Error": {"Code": code, "Message": format!("rejected {token}")},
                    "RecordList": [], "RecordId": 8
                }}),
            ));
            let client = json_responses(responses);
            let error = run("tencentcloud", "id", token, client.clone())
                .unwrap_err()
                .to_string();
            assert!(error.contains("Tencent Cloud API error"));
            assert!(!error.contains(token));
            let requests = client.requests();
            assert_eq!(requests.len(), stage + 1, "{code}");
            assert!(
                requests
                    .iter()
                    .all(|request| request.headers["x-tc-action"].starts_with("Describe"))
            );
        }
    }
}

#[test]
fn tencent_malformed_lookup_responses_never_mutate() {
    for (provider, zone) in [
        (
            "tencentcloud",
            json!({"Response": {"DomainInfo": {"DomainId": 7}}}),
        ),
        (
            "edgeone",
            json!({"Response": {"Zones": [{"ZoneId": "zone", "ZoneName": "example.com"}]}}),
        ),
        (
            "edgeone_dns",
            json!({"Response": {"Zones": [{"ZoneId": "zone", "ZoneName": "example.com"}]}}),
        ),
    ] {
        for bad_response in [
            json!({}),
            json!({"Response": null}),
            json!({"Response": []}),
            json!({"Response": "invalid"}),
            json!({"Response": {}}),
            json!({"Response": {"Error": null}}),
            json!({"Response": {
                "DomainInfo": {}, "Zones": null, "RecordList": null,
                "DnsRecords": null, "AccelerationDomains": null
            }}),
            json!({"Response": {
                "DomainInfo": [], "Zones": {}, "RecordList": {},
                "DnsRecords": {}, "AccelerationDomains": {}
            }}),
            json!({"Response": {
                "DomainInfo": null, "Zones": [null], "RecordList": [null],
                "DnsRecords": [null], "AccelerationDomains": [null]
            }}),
            json!({"Response": {
                "DomainInfo": null, "Zones": [{}], "RecordList": [{}],
                "DnsRecords": [{}], "AccelerationDomains": [{}]
            }}),
        ] {
            for stage in 0..2 {
                let mut responses = Vec::new();
                if stage == 1 {
                    responses.push((200, zone.clone()));
                }
                responses.push((200, bad_response.clone()));
                let client = json_responses(responses);
                assert!(run(provider, "id", "secret", client.clone()).is_err());
                assert_eq!(
                    client.requests().len(),
                    stage + 1,
                    "{provider}: {bad_response}"
                );
            }
        }
    }
}

#[test]
fn tencent_http_errors_and_mutation_errors_are_never_absence_or_retried() {
    for status in [200, 401, 403, 429, 500] {
        for stage in 0..3 {
            for code in [
                "AuthFailure",
                "InvalidParameter.DomainInvalid",
                "InvalidParameterValue.DomainNotExists",
                "ResourceNotFound.NoDataOfRecord",
            ] {
                if status == 200
                    && ((stage == 0 && code.starts_with("InvalidParameter"))
                        || (stage == 1 && code == "ResourceNotFound.NoDataOfRecord"))
                {
                    continue;
                }
                let mut responses = vec![
                    (200, json!({"Response": {"DomainInfo": {"DomainId": 7}}})),
                    (200, json!({"Response": {"RecordList": []}})),
                ];
                responses.truncate(stage);
                responses.push((
                    status,
                    json!({"Response": {
                        "Error": {"Code": code, "Message": "rejected tencent-secret"}, "RecordId": 8
                    }}),
                ));
                let client = json_responses(responses);
                let error = run("tencentcloud", "id", "tencent-secret", client.clone())
                    .unwrap_err()
                    .to_string();
                assert!(!error.contains("tencent-secret"));
                assert_eq!(client.requests().len(), stage + 1, "HTTP {status}, {code}");
                if status != 200 {
                    assert!(error.contains(&format!("HTTP {status}")));
                }
            }
        }
    }
}

#[test]
fn tencent_mutations_require_a_numeric_record_id() {
    for modify in [false, true] {
        let records = if modify {
            json!([{"RecordId": 8, "Name": "www", "Type": "A", "Line": "默认"}])
        } else {
            json!([])
        };
        for (response, succeeds) in [
            (json!({"Response": {"RecordId": 8}}), true),
            (json!({"Response": {"RecordId": "8"}}), true),
            (json!({"Response": {}}), false),
            (json!({"Response": {"RequestId": "request"}}), false),
            (json!({"Response": {"RecordId": null}}), false),
            (json!({"Response": {"RecordId": ""}}), false),
            (json!({"Response": {"RecordId": false}}), false),
            (json!({"Response": {"RecordId": {}}}), false),
            (json!({"Response": {"RecordId": []}}), false),
            (json!({"Response": {"RecordId": "invalid"}}), false),
            (json!({"Response": {"RecordId": 1.5}}), false),
            (
                json!({"Response": {"Error": {"Code": "ResourceNotFound.NoDataOfRecord"}}}),
                false,
            ),
        ] {
            let client = json_responses([
                (200, json!({"Response": {"DomainInfo": {"DomainId": 7}}})),
                (200, json!({"Response": {"RecordList": records}})),
                (200, response.clone()),
            ]);
            assert_eq!(
                run("tencentcloud", "id", "secret", client.clone()).is_ok(),
                succeeds,
                "{response}"
            );
            let requests = client.requests();
            assert_eq!(requests.len(), 3);
            assert_eq!(
                requests[2].headers["x-tc-action"],
                if modify {
                    "ModifyRecord"
                } else {
                    "CreateRecord"
                }
            );
        }
    }
}

#[test]
fn edgeone_mutations_accept_request_id_only_but_reject_invalid_responses() {
    for (provider_id, list_key, record) in [
        (
            "edgeone",
            "AccelerationDomains",
            json!({"DomainName": "www.example.com"}),
        ),
        (
            "edgeone_dns",
            "DnsRecords",
            json!({"RecordId": "record", "Name": "www.example.com", "Type": "A"}),
        ),
    ] {
        for modify in [false, true] {
            let records = if modify { json!([record]) } else { json!([]) };
            for (status, response, succeeds) in [
                (200, json!({"Response": {"RequestId": "request"}}), true),
                (
                    200,
                    json!({"Response": {"RequestId": "request", "RecordId": "record"}}),
                    true,
                ),
                (200, json!({"Response": {}}), false),
                (200, json!({"Response": {"RequestId": null}}), false),
                (200, json!({"Response": {"RequestId": ""}}), false),
                (200, json!({"Response": {"RequestId": 42}}), false),
                (200, json!({"Response": {"RequestId": false}}), false),
                (
                    200,
                    json!({"Response": {"Error": {"Code": "AuthFailure", "Message": "edgeone-secret"}}}),
                    false,
                ),
                (
                    200,
                    json!({"Response": {"Error": {"Code": "ResourceNotFound.NoDataOfRecord"}}}),
                    false,
                ),
                (503, json!({"Response": {"RequestId": "request"}}), false),
            ] {
                let client = json_responses([
                    (
                        200,
                        json!({"Response": {"Zones": [{"ZoneId": "zone", "ZoneName": "example.com"}]}}),
                    ),
                    (200, json!({"Response": {list_key: records}})),
                    (status, response.clone()),
                ]);
                let result = run(provider_id, "id", "edgeone-secret", client.clone());
                assert_eq!(result.is_ok(), succeeds, "{provider_id}: {response}");
                if let Err(error) = result {
                    assert!(!error.to_string().contains("edgeone-secret"));
                }
                let requests = client.requests();
                assert_eq!(requests.len(), 3);
                assert!(requests[2].headers["x-tc-action"].starts_with(if modify {
                    "Modify"
                } else {
                    "Create"
                }));
            }
        }
    }
}

#[test]
fn tencent_empty_root_alias_is_normalized_for_lookup_and_creation() {
    for domain in [
        "~example.com",
        "+example.com",
        "@~example.com",
        "example.com",
    ] {
        for modify in [false, true] {
            let records = if modify {
                json!([{"RecordId": 8, "Name": "@", "Type": "A", "Line": "默认"}])
            } else {
                json!([])
            };
            let client = json_responses([
                (200, json!({"Response": {"DomainInfo": {"DomainId": 7}}})),
                (200, json!({"Response": {"RecordList": records}})),
                (200, json!({"Response": {"RecordId": 8}})),
            ]);
            let mut update = request("192.0.2.45");
            update.domain = domain;
            run_request("tencentcloud", "id", "secret", client.clone(), update).unwrap();
            let requests = client.requests();
            assert_eq!(requests.len(), 3);
            let query: Value = serde_json::from_str(requests[1].body.as_deref().unwrap()).unwrap();
            assert_eq!(query["Subdomain"], "@");
            let mutation: Value =
                serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
            assert_eq!(mutation["SubDomain"], "@");
            assert_eq!(
                requests[2].headers["x-tc-action"],
                if modify {
                    "ModifyRecord"
                } else {
                    "CreateRecord"
                }
            );
        }
    }
}

#[test]
fn tencent_modes_and_per_request_overrides_keep_headers_and_dispatch() {
    for (provider_id, service, version, default_dns) in [
        ("tencentcloud", "dnspod", "2021-03-23", false),
        ("edgeone", "teo", "2022-09-01", false),
        ("edgeone_dns", "teo", "2022-09-01", true),
    ] {
        for (override_value, dns) in [
            (None, default_dns),
            (Some(json!("DnS")), true),
            (Some(json!("acceleration")), false),
            (Some(json!("")), false),
            (Some(json!("unknown")), false),
            (Some(Value::Null), default_dns),
            (Some(json!(true)), default_dns),
            (Some(json!(42)), default_dns),
        ] {
            for modify in [false, true] {
                let (zone, list_key, record, query_action, mutation_action) = if service == "dnspod"
                {
                    (
                        json!({"DomainInfo": {"DomainId": 7}}),
                        "RecordList",
                        json!({"RecordId": 8, "Name": "www", "Type": "A", "Line": "old-line"}),
                        "DescribeRecordList",
                        if modify {
                            "ModifyRecord"
                        } else {
                            "CreateRecord"
                        },
                    )
                } else {
                    let zone = json!({"Zones": [{"ZoneId": "zone", "ZoneName": "example.com"}]});
                    if dns {
                        (
                            zone,
                            "DnsRecords",
                            json!({"RecordId": "record", "Name": "www.example.com", "Type": "A"}),
                            "DescribeDnsRecords",
                            if modify {
                                "ModifyDnsRecords"
                            } else {
                                "CreateDnsRecord"
                            },
                        )
                    } else {
                        (
                            zone,
                            "AccelerationDomains",
                            json!({"DomainName": "www.example.com", "OriginDetail": {"BackupOrigin": "198.51.100.9"}}),
                            "DescribeAccelerationDomains",
                            if modify {
                                "ModifyAccelerationDomain"
                            } else {
                                "CreateAccelerationDomain"
                            },
                        )
                    }
                };
                let records = if modify { json!([record]) } else { json!([]) };
                let client = json_responses([
                    (200, json!({"Response": zone})),
                    (200, json!({"Response": {list_key: records}})),
                    (
                        200,
                        json!({"Response": if service == "dnspod" {
                            json!({"RecordId": 8})
                        } else {
                            json!({"RequestId": "request"})
                        }}),
                    ),
                ]);
                let mut extra = BTreeMap::from([
                    ("TTL".to_owned(), json!(180)),
                    ("Remark".to_owned(), json!("custom")),
                ]);
                if let Some(value) = &override_value {
                    extra.insert("teoDomainType".to_owned(), value.clone());
                }
                let mut update = request("192.0.2.45");
                update.line = Some("request-line");
                update.extra = &extra;
                let mut provider_config = config(provider_id, "id", "secret");
                provider_config.endpoint = None;
                let mut provider =
                    build(&provider_config, client.as_ref(), logger("secret")).unwrap();
                provider.set_record(&update).unwrap();
                let requests = client.requests();
                assert_eq!(requests.len(), 3);
                for request in &requests {
                    assert_eq!(request.method, Method::Post);
                    assert_eq!(
                        request.url,
                        format!("https://{service}.tencentcloudapi.com/")
                    );
                    assert_eq!(
                        request.headers["host"],
                        format!("{service}.tencentcloudapi.com")
                    );
                    assert_eq!(request.headers["x-tc-version"], version);
                    assert!(request.headers["x-tc-timestamp"].parse::<i64>().is_ok());
                    assert!(
                        request.headers["authorization"]
                            .contains(&format!("/{service}/tc3_request"))
                    );
                    assert!(!request.headers["authorization"].contains("secret"));
                }
                assert_eq!(
                    requests[0].headers["x-tc-action"],
                    if service == "dnspod" {
                        "DescribeDomain"
                    } else {
                        "DescribeZones"
                    }
                );
                assert_eq!(requests[1].headers["x-tc-action"], query_action);
                assert_eq!(requests[2].headers["x-tc-action"], mutation_action);
                let query: Value =
                    serde_json::from_str(requests[1].body.as_deref().unwrap()).unwrap();
                let body: Value =
                    serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
                assert_eq!(body["Remark"], "custom");
                if service == "dnspod" {
                    assert_eq!(query.get("teoDomainType"), override_value.as_ref());
                    assert_eq!(body.get("teoDomainType"), override_value.as_ref());
                    assert_eq!(query["RecordLine"], "request-line");
                    assert_eq!(
                        body["RecordLine"],
                        if modify { "old-line" } else { "request-line" }
                    );
                    assert_eq!(body["DomainId"], 7);
                    assert_eq!(body["SubDomain"], "www");
                    assert_eq!(body["Value"], update.address);
                    assert_eq!(body["TTL"], 300);
                } else {
                    assert!(query.get("teoDomainType").is_none());
                    assert!(body.get("teoDomainType").is_none());
                    assert_eq!(
                        query["Filters"],
                        json!([{
                            "Name": if dns { "name" } else { "domain-name" },
                            "Values": ["www.example.com"], "Fuzzy": false
                        }])
                    );
                    assert_eq!(body["ZoneId"], "zone");
                    assert_eq!(body["TTL"], 180);
                    if dns && modify {
                        assert_eq!(
                            body["DnsRecords"],
                            json!([{
                                "RecordId": "record", "Name": "www.example.com", "Type": "A", "Content": update.address
                            }])
                        );
                    } else if dns {
                        assert_eq!(body["Name"], "www.example.com");
                        assert_eq!(body["Type"], "A");
                        assert_eq!(body["Content"], update.address);
                    } else {
                        assert_eq!(body["DomainName"], "www.example.com");
                        assert_eq!(body["OriginInfo"]["OriginType"], "IP_DOMAIN");
                        assert_eq!(body["OriginInfo"]["Origin"], update.address);
                        if modify {
                            assert_eq!(body["OriginInfo"]["BackupOrigin"], "198.51.100.9");
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn cloudns_dnscom_and_namesilo_create_and_errors_are_offline() {
    let cloudns = json_responses([
        (200, json!({"name":"example.com"})),
        (200, json!({})),
        (200, json!({"status":"Success"})),
    ]);
    run("cloudns", "id", "secret", cloudns.clone()).unwrap();
    assert!(cloudns.requests()[2].url.ends_with("/dns/add-record.json"));
    assert!(
        run(
            "cloudns",
            "id",
            "secret",
            json_responses([(200, json!({"status":"Failed","statusDescription":"bad"}))])
        )
        .is_err()
    );

    let dnscom = json_responses([
        (200, json!({"code":0,"data":{"domainID":"example.com"}})),
        (200, json!({"code":0,"data":{"data":[]}})),
        (200, json!({"code":0,"data":{"recordID":"record"}})),
    ]);
    run("dnscom", "id", "secret", dnscom.clone()).unwrap();
    assert!(dnscom.requests()[2].url.ends_with("/api/record/create/"));
    assert!(
        run(
            "dnscom",
            "id",
            "secret",
            json_responses([(200, json!({"code":1,"message":"bad"}))])
        )
        .is_err()
    );

    let namesilo = json_responses([
        (
            200,
            json!({"reply":{"code":"300","domain":{"domain":"example.com"}}}),
        ),
        (200, json!({"reply":{"code":"300","resource_record":[]}})),
        (200, json!({"reply":{"code":"300","record_id":"record"}})),
    ]);
    run("namesilo", "", "secret", namesilo.clone()).unwrap();
    assert!(namesilo.requests()[2].url.contains("/api/dnsAddRecord?"));
    assert!(
        run(
            "namesilo",
            "",
            "secret",
            json_responses([(200, json!({"reply":{"code":"400","detail":"bad"}}))])
        )
        .is_err()
    );
}

#[test]
fn aliesa_and_huawei_create_and_errors_are_offline() {
    let aliesa = json_responses([
        (
            200,
            json!({"Sites":[{"SiteId":7,"SiteName":"example.com"}]}),
        ),
        (200, json!({"Records":[]})),
        (200, json!({"RecordId":"record"})),
    ]);
    run("aliesa", "id", "secret", aliesa.clone()).unwrap();
    assert_eq!(aliesa.requests()[2].headers["x-acs-action"], "CreateRecord");
    let invalid_id = json_responses([(
        200,
        json!({"Sites":[{"SiteId":"bad","SiteName":"example.com"}]}),
    )]);
    assert!(run("aliesa", "id", "secret", invalid_id.clone()).is_err());
    assert_eq!(invalid_id.requests().len(), 1);
    assert!(
        run(
            "aliesa",
            "id",
            "secret",
            json_responses([(200, json!({"Code":"Forbidden","Message":"bad"}))])
        )
        .is_err()
    );

    let aliesa_update = json_responses([
        (
            200,
            json!({"Sites":[{"SiteId":7,"SiteName":"example.com"}]}),
        ),
        (
            200,
            json!({"Records":[{
                "RecordId": 123,
                "RecordName": "www",
                "RecordType": "A/AAAA",
                "Data": {"Value": "192.0.2.1"},
                "Ttl": 60,
                "Proxied": true
            }]}),
        ),
        (200, json!({"RecordId":123})),
    ]);
    run("aliesa", "id", "secret", aliesa_update.clone()).unwrap();
    let update_body: Value =
        serde_json::from_str(aliesa_update.requests()[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(update_body["RecordId"], 123);
    assert!(update_body["RecordId"].is_number());

    let huawei = json_responses([
        (200, json!({"zones":[{"id":"zone","name":"example.com."}]})),
        (200, json!({"recordsets":[]})),
        (200, json!({"id":"record"})),
    ]);
    run("huaweidns", "id", "secret", huawei.clone()).unwrap();
    assert_eq!(huawei.requests()[2].method, Method::Post);
    let huawei_extra = BTreeMap::from([("description".to_owned(), json!("custom description"))]);
    let mut huawei_request = request("192.0.2.45");
    huawei_request.extra = &huawei_extra;
    let huawei_description = json_responses([
        (200, json!({"zones":[{"id":"zone","name":"example.com."}]})),
        (200, json!({"recordsets":[]})),
        (200, json!({"id":"record"})),
    ]);
    run_request(
        "huaweidns",
        "id",
        "secret",
        huawei_description.clone(),
        huawei_request,
    )
    .unwrap();
    let body: Value =
        serde_json::from_str(huawei_description.requests()[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["description"], "custom description");
    assert!(
        run(
            "huaweidns",
            "id",
            "secret",
            json_responses([(200, json!({"zones":[]}))])
        )
        .is_err()
    );
}

#[test]
fn simple_providers_direct_success_and_error_are_offline() {
    for (provider, id, token, success, failure) in [
        ("he", "", "secret", "good 192.0.2.45", "badauth"),
        ("noip", "user", "secret", "nochg 192.0.2.45", "badauth"),
    ] {
        let client = text_responses([(200, success)]);
        run(provider, id, token, client.clone()).unwrap();
        assert!(client.requests()[0].url.contains("/nic/update"));
        assert!(run(provider, id, token, text_responses([(200, failure)])).is_err());
    }

    let callback = text_responses([(200, "ok")]);
    run(
        "callback",
        "http://mock.local/callback?host=__DOMAIN__&ip=__IP__",
        "",
        callback.clone(),
    )
    .unwrap();
    assert!(callback.requests()[0].url.contains("host=www.example.com"));
    assert!(
        run(
            "callback",
            "http://mock.local/callback",
            "",
            text_responses([(500, "bad")])
        )
        .is_err()
    );
    let west = json_responses([(200, json!({"code":200,"body":{"record_id":1}}))]);
    run("west", "user", "secret", west.clone()).unwrap();
    assert_eq!(west.requests()[0].method, Method::Post);
    assert!(
        run(
            "west",
            "user",
            "secret",
            json_responses([(200, json!({"code":500,"msg":"bad"}))])
        )
        .is_err()
    );
}

#[test]
fn namesilo_zone_candidates_and_string_ttl_are_preserved() {
    let client = json_responses([
        (
            200,
            json!({"reply":{"code":"400","detail":"not in account"}}),
        ),
        (
            200,
            json!({"reply":{"code":"300","domain":{"domain":"example.co.uk"}}}),
        ),
        (
            200,
            json!({"reply":{"code":"300","resource_record":[{
                "record_id":"record",
                "host":"www",
                "type":"A",
                "ttl":"3600"
            }]}}),
        ),
        (200, json!({"reply":{"code":"300","record_id":"record"}})),
    ]);
    let mut namesilo_request = request("192.0.2.45");
    namesilo_request.domain = "www.example.co.uk";
    namesilo_request.ttl = None;
    run_request("namesilo", "", "secret", client.clone(), namesilo_request).unwrap();
    let requests = client.requests();
    assert!(requests[0].url.contains("domain=co.uk"));
    assert!(requests[1].url.contains("domain=example.co.uk"));
    assert!(requests[3].url.contains("rrttl=3600"));
}

#[test]
fn provider_specific_create_extras_are_preserved() {
    let dnscom_extra = BTreeMap::from([("remark".to_owned(), json!("custom remark"))]);
    let mut dnscom_request = request("192.0.2.45");
    dnscom_request.extra = &dnscom_extra;
    let dnscom = json_responses([
        (200, json!({"code":0,"data":{"domainID":"example.com"}})),
        (200, json!({"code":0,"data":{"data":[]}})),
        (200, json!({"code":0,"data":{"recordID":"record"}})),
    ]);
    run_request("dnscom", "id", "secret", dnscom.clone(), dnscom_request).unwrap();
    assert!(
        dnscom.requests()[2]
            .body
            .as_deref()
            .unwrap()
            .contains("remark=custom+remark")
    );
}

#[test]
fn callback_object_body_is_not_written_to_debug_log() {
    let path =
        std::env::temp_dir().join(format!("ddns-rs-callback-log-{}.log", std::process::id()));
    let _ = std::fs::remove_file(&path);
    let client = text_responses([(200, "ok")]);
    let mut provider = build(
        &config(
            "callback",
            "http://mock.local/callback",
            r#"{"api_key":"callback-secret","address":"__IP__"}"#,
        ),
        client.as_ref(),
        Logger::new(Level::Debug, Some(&path), Vec::new()).unwrap(),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.45")).unwrap();
    let body = client.requests()[0].body.clone().unwrap();
    assert!(body.contains("callback-secret"));
    let log = std::fs::read_to_string(&path).unwrap();
    assert!(!log.contains("callback-secret"));
    let _ = std::fs::remove_file(path);
}

#[test]
fn cloudns_validates_multi_label_zone_candidates() {
    let client = json_responses([
        (
            200,
            json!({"status":"Failed","statusDescription":"zone not found"}),
        ),
        (200, json!({"name":"example.co.uk"})),
        (200, json!({})),
        (200, json!({"status":"Success"})),
    ]);
    let mut cloudns_request = request("192.0.2.45");
    cloudns_request.domain = "www.example.co.uk";
    run_request("cloudns", "id", "secret", client.clone(), cloudns_request).unwrap();
    let requests = client.requests();
    assert!(
        requests[0]
            .body
            .as_deref()
            .unwrap()
            .contains("domain-name=co.uk")
    );
    assert!(
        requests[1]
            .body
            .as_deref()
            .unwrap()
            .contains("domain-name=example.co.uk")
    );
}

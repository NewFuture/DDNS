mod common;

use std::collections::BTreeMap;

use common::{FakeHttpClient, config, logger, request};
use ddns_rs::http::{HttpResponse, Method, form_encode};
use ddns_rs::provider::build;
use serde_json::{Value, json};

fn json_responses(values: impl IntoIterator<Item = Value>) -> std::sync::Arc<FakeHttpClient> {
    FakeHttpClient::new(values.into_iter().map(|body| HttpResponse {
        status: 200,
        reason: "OK".to_owned(),
        body: body.to_string(),
    }))
}

#[test]
fn cloudflare_create_and_update_flows() {
    let token = "cloudflare-secret";
    let create_client = json_responses([
        json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
        json!({"success": true, "result": []}),
        json!({"success": true, "result": {"id": "record-1"}}),
    ]);
    let mut provider = build(
        &config("cloudflare", "", token),
        create_client.as_ref(),
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.10")).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert_eq!(requests[2].method, Method::Post);
    assert_eq!(
        requests[0].headers["authorization"],
        format!("Bearer {token}")
    );
    let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["name"], "www.example.com");
    assert_eq!(body["content"], "192.0.2.10");
    assert_eq!(
        body["comment"],
        "Managed by [DDNS](https://ddns.newfuture.cc)"
    );

    let update_client = json_responses([
        json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
        json!({"success": true, "result": [{
            "id": "record-1",
            "name": "www.example.com",
            "type": "A",
            "content": "192.0.2.10",
            "proxied": true,
            "tags": ["owner:ddns"],
            "settings": {"ipv4_only": true}
        }]}),
        json!({"success": true, "result": {"id": "record-1"}}),
    ]);
    let mut provider = build(
        &config("cloudflare", "", token),
        update_client.as_ref(),
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.11")).unwrap();
    let requests = update_client.requests();
    assert_eq!(requests[2].method, Method::Put);
    let body: Value = serde_json::from_str(requests[2].body.as_deref().unwrap()).unwrap();
    assert_eq!(body["content"], "192.0.2.11");
    assert_eq!(body["proxied"], true);
    assert_eq!(body["tags"], json!(["owner:ddns"]));
    assert_eq!(body["settings"], json!({"ipv4_only": true}));
}

#[test]
fn alidns_create_and_unchanged_update_flows() {
    let token = "ali-secret";
    let create_client = json_responses([
        json!({"DomainName": "example.com", "RR": "www"}),
        json!({"DomainRecords": {"Record": []}}),
        json!({"RecordId": "record-1"}),
    ]);
    let mut provider = build(
        &config("alidns", "access-key", token),
        create_client.as_ref(),
        logger(token),
    )
    .unwrap();
    let extra = BTreeMap::from([
        ("Priority".to_owned(), json!(10)),
        ("Remark".to_owned(), json!("managed")),
    ]);
    let mut create_request = request("192.0.2.20");
    create_request.extra = &extra;
    provider.set_record(&create_request).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert_eq!(requests[0].headers["x-acs-action"], "GetMainDomainName");
    assert_eq!(requests[2].headers["x-acs-action"], "AddDomainRecord");
    assert!(
        requests[2].headers["authorization"].starts_with("ACS3-HMAC-SHA256 Credential=access-key,")
    );
    assert!(
        requests[2]
            .body
            .as_deref()
            .unwrap()
            .contains("Value=192.0.2.20")
    );
    assert!(!requests[1].body.as_deref().unwrap().contains("Priority="));
    assert!(!requests[1].body.as_deref().unwrap().contains("Remark="));
    assert!(requests[2].body.as_deref().unwrap().contains("Priority=10"));
    assert!(
        requests[2]
            .body
            .as_deref()
            .unwrap()
            .contains("Remark=managed")
    );

    let unchanged_client = json_responses([
        json!({"DomainName": "example.com", "RR": "www"}),
        json!({"DomainRecords": {"Record": [{
            "RecordId": "record-1",
            "RR": "www",
            "DomainName": "example.com",
            "Value": "192.0.2.20",
            "Type": "A",
            "TTL": 300
        }]}}),
    ]);
    let mut provider = build(
        &config("alidns", "access-key", token),
        unchanged_client.as_ref(),
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.20")).unwrap();
    assert_eq!(unchanged_client.requests().len(), 2);

    let echoed_secret = json_responses([
        json!({"DomainName": "example.com", "RR": "www"}),
        json!({"Code": "InvalidAccessKey", "Message": format!("bad credential {token}")}),
    ]);
    let mut provider = build(
        &config("alidns", "access-key", token),
        echoed_secret.as_ref(),
        logger(token),
    )
    .unwrap();
    let error = provider
        .set_record(&request("192.0.2.21"))
        .unwrap_err()
        .to_string();
    assert!(!error.contains(token));
    assert_eq!(
        error,
        "AliDNS API error InvalidAccessKey: bad credential ***"
    );
}

#[test]
fn dnspod_create_and_update_flows() {
    let token = "dnspod-secret";
    let create_client = json_responses([
        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
        json!({"status": {"code": "10", "message": "Empty result"}}),
        json!({"status": {"code": "1"}, "record": {"id": "record-1"}}),
    ]);
    let mut provider = build(
        &config("dnspod", "12345", token),
        create_client.as_ref(),
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.30")).unwrap();
    let requests = create_client.requests();
    assert_eq!(requests.len(), 3);
    assert!(requests[0].url.ends_with("/Domain.Info"));
    assert!(requests[2].url.ends_with("/Record.Create"));
    let body = requests[2].body.as_deref().unwrap();
    assert!(body.contains("login_token=12345%2Cdnspod-secret"));
    assert!(body.contains("record_line=%E9%BB%98%E8%AE%A4"));

    let update_client = json_responses([
        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
        json!({"status": {"code": "1"}, "records": [{
            "id": "record-1",
            "name": "www",
            "line": "Default"
        }]}),
        json!({"status": {"code": "1"}, "record": {"id": "record-1"}}),
    ]);
    let mut provider = build(
        &config("dnspod", "12345", token),
        update_client.as_ref(),
        logger(token),
    )
    .unwrap();
    provider.set_record(&request("192.0.2.31")).unwrap();
    let requests = update_client.requests();
    assert!(requests[2].url.ends_with("/Record.Modify"));
    assert!(
        requests[2]
            .body
            .as_deref()
            .unwrap()
            .contains("record_line=default")
    );
    assert!(requests[2].body.as_deref().unwrap().contains("ttl=300"));

    let failed_lookup = json_responses([
        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
        json!({"status": {"code": "0", "message": "Authentication failed"}}),
    ]);
    let mut provider = build(
        &config("dnspod", "12345", token),
        failed_lookup.as_ref(),
        logger(token),
    )
    .unwrap();
    let error = provider.set_record(&request("192.0.2.32")).unwrap_err();
    assert!(error.to_string().contains("DNSPod API error 0"));
    assert_eq!(failed_lookup.requests().len(), 2);

    let multi_label_zone = json_responses([
        json!({"status": {"code": "7", "message": "No permission"}}),
        json!({"status": {"code": "1"}, "domain": {"id": "zone-uk"}}),
        json!({"status": {"code": "10", "message": "Empty result"}}),
        json!({"status": {"code": "1"}, "record": {"id": "record-uk"}}),
    ]);
    let mut provider = build(
        &config("dnspod", "12345", token),
        multi_label_zone.as_ref(),
        logger(token),
    )
    .unwrap();
    let mut multi_label_request = request("192.0.2.33");
    multi_label_request.domain = "host.example.co.uk";
    provider.set_record(&multi_label_request).unwrap();
    let requests = multi_label_zone.requests();
    assert_eq!(requests.len(), 4);
    assert!(
        requests[0]
            .body
            .as_deref()
            .unwrap()
            .contains("domain=co.uk")
    );
    assert!(
        requests[1]
            .body
            .as_deref()
            .unwrap()
            .contains("domain=example.co.uk")
    );

    let authentication_failure = json_responses([json!({
        "status": {"code": "-1", "message": "Authentication failed"}
    })]);
    let mut provider = build(
        &config("dnspod", "12345", token),
        authentication_failure.as_ref(),
        logger(token),
    )
    .unwrap();
    let error = provider.set_record(&request("192.0.2.34")).unwrap_err();
    assert!(error.to_string().contains("DNSPod API error -1"));
    assert_eq!(authentication_failure.requests().len(), 1);
}

#[test]
fn cloudflare_proxied_filter_and_explicit_extras_are_preserved() {
    let token = "cloudflare-secret";
    let extra = BTreeMap::from([
        ("proxied".to_owned(), json!(false)),
        ("tags".to_owned(), json!([])),
        ("settings".to_owned(), json!({"ipv6_only": true})),
        ("comment".to_owned(), json!("")),
    ]);
    let records = json!([{
        "id": "record-1", "name": "www.example.com", "type": "A",
        "proxied": true, "tags": ["owner:old"], "settings": {"ipv4_only": true}
    }]);
    for fallback in [false, true] {
        let mut responses = vec![json!({
            "success": true, "result": [{"id": "zone-1", "name": "example.com"}]
        })];
        if fallback {
            responses.push(json!({"success": true, "result": []}));
        }
        responses.extend([
            json!({"success": true, "result": records}),
            json!({"success": true, "result": {"id": "record-1"}}),
        ]);
        let client = json_responses(responses);
        let mut provider = build(
            &config("cloudflare", "", token),
            client.as_ref(),
            logger(token),
        )
        .unwrap();
        let mut update = request("192.0.2.40");
        update.extra = &extra;
        provider.set_record(&update).unwrap();

        let requests = client.requests();
        assert_eq!(requests.len(), if fallback { 4 } else { 3 });
        assert!(requests[1].url.contains("proxied=false"));
        if fallback {
            assert_eq!(requests[2].method, Method::Get);
            assert!(!requests[2].url.contains("proxied="));
        }
        let mutation = requests.last().unwrap();
        assert_eq!(mutation.method, Method::Put);
        assert!(mutation.url.ends_with("/dns_records/record-1"));
        let body: Value = serde_json::from_str(mutation.body.as_deref().unwrap()).unwrap();
        assert_eq!(body["proxied"], false);
        assert_eq!(body["tags"], json!([]));
        assert_eq!(body["settings"], json!({"ipv6_only": true}));
        assert_eq!(body["comment"], "");
        assert_eq!(body["content"], update.address);
    }
}

#[test]
fn cloudflare_invalid_lookup_results_never_fall_back_or_mutate() {
    let token = "cloudflare-secret";
    let extra = BTreeMap::from([("proxied".to_owned(), json!(true))]);
    for bad_response in [
        json!({"success": true}),
        json!({"success": true, "result": null}),
        json!({"success": true, "result": {}}),
        json!({"success": true, "result": "invalid"}),
        json!({"success": true, "result": false}),
        json!({"success": true, "result": 42}),
        json!({"success": true, "result": [null]}),
        json!({"success": true, "result": [{}]}),
        json!({"success": true, "result": [{"name": "www.example.com", "type": "A"}]}),
        json!({"success": false, "errors": [{"code": 10000, "message": token}]}),
        json!({"success": "true", "result": []}),
        json!({"result": []}),
    ] {
        // Fail at zone lookup, filtered record lookup, or the unfiltered fallback.
        for stage in 0..3 {
            let mut responses = Vec::new();
            if stage > 0 {
                responses.push(json!({
                    "success": true, "result": [{"id": "zone-1", "name": "example.com"}]
                }));
            }
            if stage > 1 {
                responses.push(json!({"success": true, "result": []}));
            }
            responses.push(bad_response.clone());
            let client = json_responses(responses);
            let mut provider = build(
                &config("cloudflare", "", token),
                client.as_ref(),
                logger(token),
            )
            .unwrap();
            let mut update = request("192.0.2.40");
            update.extra = &extra;
            let error = provider.set_record(&update).unwrap_err().to_string();
            assert!(!error.contains(token));
            let requests = client.requests();
            assert_eq!(requests.len(), stage + 1, "stage {stage}: {bad_response}");
            assert!(requests.iter().all(|request| request.method == Method::Get));
        }
    }
}

#[test]
fn cloudflare_empty_zone_and_record_lists_allow_creation() {
    let token = "cloudflare-secret";
    let client = json_responses([
        json!({"success": true, "result": []}),
        json!({"success": true, "result": [{"id": "zone-1", "name": "example.co.uk"}]}),
        json!({"success": true, "result": []}),
        json!({"success": true, "result": []}),
        json!({"success": true, "result": {"id": "record-1"}}),
    ]);
    let mut provider = build(
        &config("cloudflare", "", token),
        client.as_ref(),
        logger(token),
    )
    .unwrap();
    let extra = BTreeMap::from([("proxied".to_owned(), json!(false))]);
    let mut create = request("192.0.2.40");
    create.domain = "host.example.co.uk";
    create.extra = &extra;
    provider.set_record(&create).unwrap();
    let requests = client.requests();
    assert_eq!(requests.len(), 5);
    assert!(requests[0].url.contains("name.exact=co.uk"));
    assert!(requests[1].url.contains("name.exact=example.co.uk"));
    assert!(requests[2].url.contains("proxied=false"));
    assert!(!requests[3].url.contains("proxied="));
    assert_eq!(requests[4].method, Method::Post);
}

#[test]
fn cloudflare_mutations_require_a_valid_record_id() {
    let token = "cloudflare-secret";
    for modify in [false, true] {
        let records = if modify {
            json!([{"id": "record-1", "name": "www.example.com", "type": "A"}])
        } else {
            json!([])
        };
        let mut invalid = vec![
            json!({"success": true}),
            json!({"success": true, "result": null}),
            json!({"success": true, "result": []}),
            json!({"success": true, "result": {}}),
            json!({"success": true, "result": {"id": null}}),
            json!({"success": true, "result": {"id": ""}}),
            json!({"success": true, "result": {"id": 42}}),
            json!({"success": true, "result": {"id": false}}),
            json!({"success": false, "errors": [{"code": 10000, "message": token}]}),
        ];
        if modify {
            invalid.push(json!({"success": true, "result": {"id": "different-record"}}));
        }
        for response in invalid {
            let client = json_responses([
                json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
                json!({"success": true, "result": records}),
                response.clone(),
            ]);
            let mut provider = build(
                &config("cloudflare", "", token),
                client.as_ref(),
                logger(token),
            )
            .unwrap();
            let error = provider
                .set_record(&request("192.0.2.40"))
                .unwrap_err()
                .to_string();
            assert!(!error.contains(token));
            let requests = client.requests();
            assert_eq!(requests.len(), 3, "must not retry: {response}");
            assert_eq!(
                requests[2].method,
                if modify { Method::Put } else { Method::Post }
            );
        }
    }
}

#[test]
fn cloudflare_http_failures_do_not_fall_back_or_retry_mutations() {
    let token = "cloudflare-secret";
    for status in [401, 403, 429, 500] {
        for stage in 0..4 {
            let mut responses = vec![
                json!({"success": true, "result": [{"id": "zone-1", "name": "example.com"}]}),
                json!({"success": true, "result": []}),
                json!({"success": true, "result": []}),
            ];
            responses.truncate(stage);
            let mut responses = responses
                .into_iter()
                .map(|body| HttpResponse {
                    status: 200,
                    reason: "OK".to_owned(),
                    body: body.to_string(),
                })
                .collect::<Vec<_>>();
            responses.push(HttpResponse {
                status,
                reason: "Error".to_owned(),
                body: json!({"success": true, "result": {"id": "record-1"}, "echo": token})
                    .to_string(),
            });
            let client = FakeHttpClient::new(responses);
            let mut provider = build(
                &config("cloudflare", "", token),
                client.as_ref(),
                logger(token),
            )
            .unwrap();
            let extra = BTreeMap::from([("proxied".to_owned(), json!(true))]);
            let mut create = request("192.0.2.40");
            create.extra = &extra;
            let error = provider.set_record(&create).unwrap_err().to_string();
            assert!(error.contains(&format!("HTTP {status}")));
            assert!(!error.contains(token));
            let requests = client.requests();
            assert_eq!(requests.len(), stage + 1);
            assert!(
                requests[..stage]
                    .iter()
                    .all(|request| request.method == Method::Get)
            );
            assert_eq!(
                requests[stage].method,
                if stage == 3 {
                    Method::Post
                } else {
                    Method::Get
                }
            );
        }
    }
}

#[test]
fn dnspod_extras_override_defaults_and_previous_records_for_both_endpoints() {
    let token = "dnspod-secret";
    for provider_id in ["dnspod", "dnspod_com"] {
        for modify in [false, true] {
            for line in [None, Some("request-line")] {
                for (extra_line, expected_line) in [
                    (json!("custom"), Some("custom")),
                    (json!(""), Some("")),
                    (json!(false), Some("false")),
                    (json!(0), Some("0")),
                    (Value::Null, None),
                ] {
                    let records = if modify {
                        json!({"status": {"code": "1"}, "records": [{
                            "id": "record-1", "name": "www", "line": "previous-line"
                        }]})
                    } else {
                        json!({"status": {"code": "10"}})
                    };
                    let client = json_responses([
                        json!({"status": {"code": "1"}, "domain": {"id": "zone-1"}}),
                        records,
                        json!({"status": {"code": "1"}, "record": {"id": "record-1"}}),
                    ]);
                    let mut provider = build(
                        &config(provider_id, "12345", token),
                        client.as_ref(),
                        logger(token),
                    )
                    .unwrap();
                    let extra = BTreeMap::from([
                        ("record_line".to_owned(), extra_line),
                        ("ttl".to_owned(), json!(600)),
                        ("value".to_owned(), json!("192.0.2.41")),
                        ("empty".to_owned(), json!("")),
                        ("flag".to_owned(), json!(false)),
                        ("number".to_owned(), json!(1.5)),
                        ("null".to_owned(), Value::Null),
                        ("array".to_owned(), json!([])),
                        ("object".to_owned(), json!({})),
                        ("login_token".to_owned(), json!("ignored")),
                        ("format".to_owned(), json!("xml")),
                    ]);
                    let mut update = request("192.0.2.40");
                    update.extra = &extra;
                    update.line = line;
                    provider.set_record(&update).unwrap();

                    let requests = client.requests();
                    assert_eq!(requests.len(), 3);
                    assert!(requests[2].url.ends_with(if modify {
                        "/Record.Modify"
                    } else {
                        "/Record.Create"
                    }));
                    let mut expected = BTreeMap::from([
                        ("domain_id".to_owned(), "zone-1".to_owned()),
                        ("sub_domain".to_owned(), "www".to_owned()),
                        ("record_type".to_owned(), "A".to_owned()),
                        ("value".to_owned(), "192.0.2.41".to_owned()),
                        ("ttl".to_owned(), "600".to_owned()),
                        ("empty".to_owned(), String::new()),
                        ("flag".to_owned(), "false".to_owned()),
                        ("number".to_owned(), "1.5".to_owned()),
                        ("login_token".to_owned(), format!("12345,{token}")),
                        ("format".to_owned(), "json".to_owned()),
                    ]);
                    if modify {
                        expected.insert("record_id".to_owned(), "record-1".to_owned());
                    }
                    if let Some(line) = expected_line {
                        expected.insert("record_line".to_owned(), line.to_owned());
                    }
                    assert_eq!(requests[2].body.as_deref().unwrap(), form_encode(&expected));
                    let query = requests[1].body.as_deref().unwrap();
                    assert!(!query.contains("record_line="));
                    assert!(!query.contains("empty="));
                    assert_eq!(query.contains("line=request-line"), line.is_some());
                }
            }
        }
    }
}

#[test]
fn alidns_standard_parameters_still_override_extras() {
    let token = "ali-secret";
    let extra = BTreeMap::from([
        ("Value".to_owned(), json!("192.0.2.99")),
        ("TTL".to_owned(), json!(600)),
        ("Line".to_owned(), json!("extra-line")),
    ]);
    for ttl in [None, Some(300)] {
        let client = json_responses([
            json!({"DomainName": "example.com", "RR": "www"}),
            json!({"DomainRecords": {"Record": []}}),
            json!({"RecordId": "record-1"}),
        ]);
        let mut provider = build(
            &config("alidns", "id", token),
            client.as_ref(),
            logger(token),
        )
        .unwrap();
        let mut create = request("192.0.2.40");
        create.extra = &extra;
        create.ttl = ttl;
        create.line = Some("request-line");
        provider.set_record(&create).unwrap();
        let requests = client.requests();
        let body = requests[2].body.as_deref().unwrap();
        assert!(body.contains("Value=192.0.2.40"));
        assert!(!body.contains("Value=192.0.2.99"));
        assert!(body.contains("Line=request-line"));
        assert!(body.contains(&format!("TTL={}", ttl.unwrap_or(600))));
    }
}

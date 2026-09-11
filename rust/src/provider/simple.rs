use std::collections::BTreeMap;

use serde_json::{Map, Value};
use time::OffsetDateTime;

use crate::error::{Error, Result};
use crate::http::{Method, form_encode, percent_encode};

use super::base::{Provider, ProviderContext, RecordRequest, split_custom_domain, value_to_string};

pub enum SimpleKind {
    Callback,
    He,
    NoIp,
    West,
}

pub struct SimpleProvider<'a> {
    context: ProviderContext<'a>,
    kind: SimpleKind,
}

impl<'a> SimpleProvider<'a> {
    pub fn new(context: ProviderContext<'a>, kind: SimpleKind) -> Result<Self> {
        match kind {
            SimpleKind::Callback if !context.id.contains("://") => {
                return Err(Error::Config("callback id must be a URL".to_owned()));
            }
            SimpleKind::He if !context.id.is_empty() => {
                return Err(Error::Config(
                    "Hurricane Electric does not use id; use token as the password".to_owned(),
                ));
            }
            SimpleKind::He | SimpleKind::West if context.token.is_empty() => {
                return Err(Error::Config(
                    "provider token must be configured".to_owned(),
                ));
            }
            SimpleKind::NoIp if context.id.is_empty() || context.token.is_empty() => {
                return Err(Error::Config(
                    "No-IP username and password must be configured".to_owned(),
                ));
            }
            _ => {}
        }
        Ok(Self { context, kind })
    }

    fn form(&self, path: &str, values: BTreeMap<String, String>) -> Result<String> {
        self.context
            .send(
                Method::Post,
                path,
                &BTreeMap::new(),
                Some(form_encode(&values)),
                BTreeMap::from([(
                    "content-type".to_owned(),
                    "application/x-www-form-urlencoded".to_owned(),
                )]),
            )
            .map(|response| response.body)
    }

    fn callback(&self, request: &RecordRequest<'_>) -> Result<()> {
        let variables = callback_variables(request);
        let url = replace_variables(&self.context.id, &variables);
        let token = self.context.token.trim();
        if token.is_empty() {
            self.context
                .send(Method::Get, &url, &BTreeMap::new(), None, BTreeMap::new())?;
            return Ok(());
        }
        let parsed: Value = serde_json::from_str(token).map_err(|error| {
            Error::Config(format!("callback token must be a JSON object: {error}"))
        })?;
        let Value::Object(values) = parsed else {
            return Err(Error::Config(
                "callback token must be a JSON object".to_owned(),
            ));
        };
        let values = values
            .into_iter()
            .map(|(key, value)| {
                (
                    key,
                    match value {
                        Value::String(value) => {
                            Value::String(replace_variables(&value, &variables))
                        }
                        value => value,
                    },
                )
            })
            .collect::<Map<_, _>>();
        self.context.send_sensitive(
            Method::Post,
            &url,
            &BTreeMap::new(),
            Some(serde_json::to_string(&Value::Object(values))?),
            BTreeMap::from([("content-type".to_owned(), "application/json".to_owned())]),
        )?;
        Ok(())
    }

    fn west(&self, request: &RecordRequest<'_>) -> Result<()> {
        let domain = request.domain.to_ascii_lowercase();
        let candidates = if let Some((subdomain, main_domain)) = split_custom_domain(&domain) {
            vec![(subdomain, main_domain)]
        } else {
            let labels = domain.split('.').collect::<Vec<_>>();
            if labels.len() <= 2 {
                vec![("@".to_owned(), domain)]
            } else {
                (1..labels.len() - 1)
                    .rev()
                    .map(|index| (labels[..index].join("."), labels[index..].join(".")))
                    .chain(std::iter::once(("@".to_owned(), domain.clone())))
                    .collect()
            }
        };
        for (host, domain) in candidates {
            let mut values = BTreeMap::from([
                ("act".to_owned(), "dnsrec.update".to_owned()),
                ("domain".to_owned(), domain),
                ("hostname".to_owned(), host),
                ("record_value".to_owned(), request.address.to_owned()),
            ]);
            if self.context.id.is_empty() {
                values.insert("apidomainkey".to_owned(), self.context.token.to_owned());
            } else {
                values.insert("username".to_owned(), self.context.id.to_owned());
                values.insert("apikey".to_owned(), self.context.token.to_owned());
            }
            if let Some(line) = request.line {
                values.insert("record_line".to_owned(), line.to_owned());
            }
            let result: Value = serde_json::from_str(&self.form("", values)?).map_err(|error| {
                Error::Provider(format!("West API returned invalid JSON: {error}"))
            })?;
            match result.get("code").and_then(Value::as_i64) {
                Some(200) => return Ok(()),
                Some(404) => continue,
                code => {
                    return Err(Error::Provider(format!(
                        "West API error {}: {}",
                        code.map_or_else(|| "unknown".to_owned(), |code| code.to_string()),
                        self.context.logger.mask(
                            result
                                .get("msg")
                                .and_then(Value::as_str)
                                .unwrap_or("unknown error")
                        )
                    )));
                }
            }
        }
        Err(Error::Provider(format!(
            "West API could not find a zone for {}",
            request.domain
        )))
    }
}

impl Provider for SimpleProvider<'_> {
    fn set_record(&mut self, request: &RecordRequest<'_>) -> Result<()> {
        match self.kind {
            SimpleKind::Callback => self.callback(request),
            SimpleKind::He => {
                let response = self.form(
                    "/nic/update",
                    BTreeMap::from([
                        ("hostname".to_owned(), request.domain.to_owned()),
                        ("myip".to_owned(), request.address.to_owned()),
                        ("password".to_owned(), self.context.token.to_owned()),
                    ]),
                )?;
                if response.starts_with("good") || response.starts_with("nochg") {
                    Ok(())
                } else {
                    Err(Error::Provider(format!(
                        "HE API error: {}",
                        self.context.logger.mask(&response)
                    )))
                }
            }
            SimpleKind::NoIp => {
                let endpoint = self.context.endpoint.trim_end_matches('/');
                let (_, authority) = endpoint
                    .split_once("://")
                    .ok_or_else(|| Error::Config(format!("invalid No-IP endpoint `{endpoint}`")))?;
                let url = format!(
                    "{}://{}:{}@{authority}",
                    endpoint.split_once("://").map_or("", |(scheme, _)| scheme),
                    percent_encode(&self.context.id),
                    percent_encode(&self.context.token),
                );
                let response = self.context.send(
                    Method::Get,
                    &format!("{url}/nic/update"),
                    &BTreeMap::from([
                        ("hostname".to_owned(), request.domain.to_owned()),
                        ("myip".to_owned(), request.address.to_owned()),
                    ]),
                    None,
                    BTreeMap::new(),
                )?;
                if response.body.starts_with("good") || response.body.starts_with("nochg") {
                    Ok(())
                } else {
                    Err(Error::Provider(format!(
                        "No-IP API error: {}",
                        self.context.logger.mask(&response.body)
                    )))
                }
            }
            SimpleKind::West => self.west(request),
        }
    }
}

fn callback_variables(request: &RecordRequest<'_>) -> BTreeMap<String, String> {
    let mut values = request
        .extra
        .iter()
        .filter_map(|(key, value)| value_to_string(value).map(|value| (key.clone(), value)))
        .collect::<BTreeMap<_, _>>();
    values.extend([
        ("__DOMAIN__".to_owned(), request.domain.to_owned()),
        ("__RECORDTYPE__".to_owned(), request.record_type.to_owned()),
        (
            "__TTL__".to_owned(),
            request
                .ttl
                .map_or_else(|| "None".to_owned(), |ttl| ttl.to_string()),
        ),
        ("__IP__".to_owned(), request.address.to_owned()),
        (
            "__LINE__".to_owned(),
            request
                .line
                .map_or_else(|| "None".to_owned(), ToOwned::to_owned),
        ),
        (
            "__TIMESTAMP__".to_owned(),
            (OffsetDateTime::now_utc().unix_timestamp_nanos() as f64 / 1_000_000_000.0).to_string(),
        ),
    ]);
    values
}

fn replace_variables(value: &str, values: &BTreeMap<String, String>) -> String {
    values
        .iter()
        .fold(value.to_owned(), |output, (key, value)| {
            output.replace(key, value)
        })
}

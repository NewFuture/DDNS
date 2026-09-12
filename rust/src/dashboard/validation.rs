use std::collections::BTreeMap;
use std::sync::LazyLock;

use regex::Regex;
use serde_json::{Map, Value, json};

use crate::config;
use crate::provider::ProviderId;

use super::{DashboardError, Result};

pub(super) static MODEL: LazyLock<Value> = LazyLock::new(|| {
    serde_json::from_str(include_str!("../../../ddns/config/field-model.json"))
        .expect("canonical field model must be valid JSON")
});
static DOMAIN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        MODEL["rules"]["domainPattern"]
            .as_str()
            .expect("domain pattern"),
    )
    .expect("valid domain pattern")
});
static PROXY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        MODEL["rules"]["proxyPattern"]
            .as_str()
            .expect("proxy pattern"),
    )
    .expect("valid proxy pattern")
});

const GLOBAL: &[&str] = &[
    "ssl",
    "proxy",
    "cache",
    "cache_max_age",
    "interval",
    "http",
    "log",
];
const FIELDS: &[&str] = &[
    "id",
    "token",
    "endpoint",
    "ipv4",
    "ipv6",
    "index4",
    "index6",
    "ttl",
    "line",
    "proxy",
    "cache",
    "cache_max_age",
    "ssl",
    "extra",
    "log",
];
const METADATA: &[&str] = &[
    "$schema",
    "command",
    "config",
    "debug",
    "dns",
    "provider",
    "interval",
    "http",
    "http_host",
    "http_port",
    "http_token",
    "http_origins",
];

pub(super) fn interval(value: u16) -> Result<u16> {
    if (1..=1440).contains(&value) {
        Ok(value)
    } else {
        Err(invalid("interval must be between 1 and 1440 minutes"))
    }
}

pub(super) fn invalid(message: impl Into<String>) -> DashboardError {
    DashboardError {
        status: 400,
        code: "invalid_config",
        message: message.into(),
    }
}

fn structured(mut object: Map<String, Value>) -> Map<String, Value> {
    for (prefix, keys) in [
        ("log", &["level", "file", "format", "datefmt"][..]),
        ("http", &["host", "port", "token", "origins"][..]),
    ] {
        for key in keys {
            if let Some(value) = object.remove(&format!("{prefix}_{key}")) {
                let nested = object.entry(prefix).or_insert_with(|| json!({}));
                if let Some(nested) = nested.as_object_mut() {
                    nested.insert((*key).to_owned(), value);
                }
            }
        }
    }
    object
}

fn legacy_provider(
    object: Map<String, Value>,
    fallback: Option<&str>,
    exclude: &[&str],
) -> Result<Value> {
    let mut object = structured(object);
    let name = object
        .remove("provider")
        .or_else(|| object.remove("dns"))
        .or_else(|| fallback.map(|name| json!(name)))
        .unwrap_or(json!(""));
    let mut result = Map::from_iter([("provider".to_owned(), name)]);
    let mut extra = match object.remove("extra") {
        None => Map::new(),
        Some(Value::Object(extra)) => extra,
        Some(_) => return Err(invalid("extra must be an object")),
    };
    for (key, value) in object {
        if exclude.contains(&key.as_str()) || METADATA.contains(&key.as_str()) {
            continue;
        }
        if FIELDS.contains(&key.as_str()) {
            result.insert(key, value);
        } else {
            extra.insert(key.strip_prefix("extra_").unwrap_or(&key).to_owned(), value);
        }
    }
    if !extra.is_empty() {
        result.insert("extra".to_owned(), Value::Object(extra));
    }
    Ok(Value::Object(result))
}

fn normalize(document: Value, fallback: Option<&str>) -> Result<Value> {
    match document {
        Value::Object(object) if object.contains_key("providers") => Ok(Value::Object(object)),
        Value::Object(object) => {
            let object = structured(object);
            let mut result = Map::new();
            for key in GLOBAL {
                if let Some(value) = object.get(*key) {
                    result.insert((*key).to_owned(), value.clone());
                }
            }
            let has_provider = object
                .get("dns")
                .or_else(|| object.get("provider"))
                .is_some()
                || fallback.is_some();
            let providers = if has_provider {
                vec![legacy_provider(object, fallback, GLOBAL)?]
            } else if object.keys().any(|key| key != "$schema") {
                return Err(invalid(
                    "single-provider configuration requires dns or DDNS_DNS",
                ));
            } else {
                Vec::new()
            };
            result.insert("providers".to_owned(), json!(providers));
            Ok(Value::Object(result))
        }
        Value::Array(items) => {
            let mut providers = Vec::new();
            for item in items {
                let object = item
                    .as_object()
                    .ok_or_else(|| invalid("legacy provider entries must be objects"))?;
                providers.push(legacy_provider(object.clone(), fallback, &[])?);
            }
            if providers.is_empty()
                && let Some(name) = fallback
            {
                providers.push(json!({"provider":name}));
            }
            Ok(json!({"providers":providers}))
        }
        _ => Err(invalid("configuration root must be an object or array")),
    }
}

pub(super) fn validate(document: Value, environment: &BTreeMap<String, Value>) -> Result<Value> {
    let fallback = environment
        .get("dns")
        .and_then(Value::as_str)
        .filter(|name| !name.is_empty());
    let mut document = normalize(document, fallback)?;
    let object = document.as_object_mut().expect("normalized object");
    for key in MODEL["rules"]["legacyProviderKeys"]
        .as_array()
        .expect("legacy keys")
    {
        if object.contains_key(key.as_str().expect("key")) {
            return Err(invalid(
                "providers cannot be combined with legacy provider fields",
            ));
        }
    }
    inherited(object)?;
    if let Some(value) = object.get("interval") {
        let value = value
            .as_u64()
            .and_then(|value| u16::try_from(value).ok())
            .ok_or_else(|| invalid("interval must be an integer"))?;
        interval(value)?;
    }
    if let Some(value) = object.get_mut("http") {
        validate_http(value)?;
    }
    let providers = object
        .get_mut("providers")
        .and_then(Value::as_array_mut)
        .ok_or_else(|| invalid("providers must be an array"))?;
    if providers.len() > MODEL["limits"]["providers"].as_u64().unwrap_or(128) as usize {
        return Err(invalid("too many providers"));
    }
    for provider in providers {
        let provider = provider
            .as_object_mut()
            .ok_or_else(|| invalid("provider entries must be objects"))?;
        if [
            "dns",
            "interval",
            "http",
            "http_host",
            "http_port",
            "http_token",
            "http_origins",
        ]
        .iter()
        .any(|key| provider.contains_key(*key))
        {
            return Err(invalid(
                "provider entries cannot contain dns, interval, or HTTP settings",
            ));
        }
        let name = provider
            .get("provider")
            .and_then(Value::as_str)
            .ok_or_else(|| invalid("provider must be a string"))?
            .trim()
            .to_ascii_lowercase();
        name.parse::<ProviderId>()
            .map_err(|_| invalid("unsupported DNS provider"))?;
        provider.insert("provider".to_owned(), json!(name));
        inherited(provider)?;
    }
    object.insert("$schema".to_owned(), MODEL["schema"]["url"].clone());
    let mut runtime_document = document.clone();
    // Even an empty providers list must validate inherited runtime settings.
    if runtime_document["providers"]
        .as_array()
        .is_some_and(Vec::is_empty)
    {
        runtime_document["providers"] = json!([{"provider":"debug"}]);
    }
    let configs = config::from_document(runtime_document, environment)
        .map_err(|_| invalid("configuration or environment contains invalid runtime settings"))?;
    for config in configs {
        if config
            .ipv4
            .iter()
            .chain(&config.ipv6)
            .any(|domain| domain.len() > 253 || !DOMAIN.is_match(domain))
        {
            return Err(invalid("runtime configuration contains an invalid domain"));
        }
    }
    Ok(document)
}

fn inherited(object: &mut Map<String, Value>) -> Result<()> {
    if ["domain", "value", "record_type"]
        .iter()
        .any(|key| object.contains_key(*key))
    {
        return Err(invalid("configuration contains reserved record fields"));
    }
    for key in ["id", "endpoint", "line"] {
        if let Some(value) = object.get(key)
            && !(value.is_null() || value.is_string())
        {
            return Err(invalid(format!("{key} must be a string or null")));
        }
    }
    if let Some(value) = object.get("token")
        && !(value.is_string() || value.is_object())
    {
        return Err(invalid(
            "token must be a string (or a callback body object)",
        ));
    }
    for key in ["ipv4", "ipv6"] {
        if let Some(value) = object.get_mut(key) {
            let values = strings(value, false)?
                .into_iter()
                .map(|domain| domain.trim().to_ascii_lowercase())
                .collect::<Vec<_>>();
            if values
                .iter()
                .any(|domain| domain.len() > 253 || !DOMAIN.is_match(domain))
            {
                return Err(invalid(format!("{key} contains an invalid domain")));
            }
            unique(&values)?;
            *value = json!(values);
        }
    }
    for key in ["index4", "index6"] {
        if let Some(value) = object.get_mut(key) {
            if value == &Value::Bool(false) {
                continue;
            }
            let values = strings(value, true)?
                .into_iter()
                .map(|source| source.trim().to_owned())
                .collect::<Vec<_>>();
            for source in &values {
                validate_source(source)?;
            }
            unique(&values)?;
            *value = if values.is_empty() {
                json!(false)
            } else {
                json!(values)
            };
        }
    }
    if let Some(value) = object.get_mut("proxy") {
        let proxies = strings(value, false)?
            .into_iter()
            .map(|proxy| proxy.trim().to_owned())
            .collect::<Vec<_>>();
        if proxies.iter().any(|proxy| !PROXY.is_match(proxy)) {
            return Err(invalid("proxy contains an invalid value"));
        }
        unique(&proxies)?;
        *value = json!(proxies);
    }
    for key in ["ttl", "cache_max_age"] {
        if let Some(value) = object.get_mut(key)
            && !value.is_null()
        {
            let parsed = value
                .as_u64()
                .or_else(|| value.as_str().and_then(|v| v.parse::<u64>().ok()));
            *value = json!(
                parsed.ok_or_else(|| invalid(format!("{key} must be a non-negative integer")))?
            );
        }
    }
    if let Some(extra) = object.get("extra") {
        let extra = extra
            .as_object()
            .ok_or_else(|| invalid("extra must be an object"))?;
        if MODEL["rules"]["reservedExtraKeys"]
            .as_array()
            .expect("reserved keys")
            .iter()
            .any(|key| extra.contains_key(key.as_str().expect("key")))
        {
            return Err(invalid("extra contains reserved record fields"));
        }
    }
    for key in MODEL["rules"]["reservedExtraKeys"]
        .as_array()
        .expect("reserved keys")
    {
        if object.contains_key(&format!("extra_{}", key.as_str().expect("key"))) {
            return Err(invalid("extra contains reserved record fields"));
        }
    }
    if let Some(log) = object.get("log") {
        let log = log
            .as_object()
            .ok_or_else(|| invalid("log must be an object"))?;
        if log
            .keys()
            .any(|key| !["level", "file", "format", "datefmt"].contains(&key.as_str()))
        {
            return Err(invalid("unknown log setting"));
        }
        for value in log.values() {
            if !value.is_null() && !value.is_string() {
                return Err(invalid("log settings must be strings or null"));
            }
        }
    }
    Ok(())
}

fn strings(value: &Value, sources: bool) -> Result<Vec<String>> {
    if value.is_object() || value.is_boolean() || (!sources && value.is_number()) {
        return Err(invalid("expected a string or array"));
    }
    if let Value::Array(values) = value
        && values
            .iter()
            .any(|v| !v.is_string() && !(sources && v.as_u64().is_some()))
    {
        return Err(invalid("invalid array element"));
    }
    config::value_list(Some(value), sources).map_err(|_| invalid("invalid list value"))
}

fn unique(values: &[String]) -> Result<()> {
    if values
        .iter()
        .collect::<std::collections::BTreeSet<_>>()
        .len()
        != values.len()
    {
        return Err(invalid("duplicate list entries are not allowed"));
    }
    Ok(())
}

fn validate_source(source: &str) -> Result<()> {
    if source.parse::<u64>().is_ok()
        || MODEL["rules"]["addressSourceNames"]
            .as_array()
            .expect("source names")
            .iter()
            .any(|name| name.as_str() == Some(source))
    {
        return Ok(());
    }
    for prefix in MODEL["rules"]["addressSourcePrefixes"]
        .as_array()
        .expect("source prefixes")
    {
        let prefix = prefix.as_str().expect("prefix");
        if let Some(argument) = source.strip_prefix(prefix) {
            if argument.trim().is_empty() {
                return Err(invalid("address source argument is empty"));
            }
            if prefix == "url:" {
                let uri = argument
                    .parse::<ureq::http::Uri>()
                    .map_err(|_| invalid("invalid IP URL"))?;
                if !matches!(uri.scheme_str(), Some("http" | "https"))
                    || uri.host().is_none_or(str::is_empty)
                {
                    return Err(invalid("IP URL must have an HTTP(S) host"));
                }
            }
            if prefix == "regex:" {
                Regex::new(argument).map_err(|_| invalid("invalid source regular expression"))?;
            }
            return Ok(());
        }
    }
    Err(invalid("unsupported address source"))
}

fn validate_http(value: &mut Value) -> Result<()> {
    if let Some(origins) = value.get("origins")
        && !origins.is_array()
    {
        return Err(invalid("HTTP origins must be an array"));
    }
    let settings = crate::http_settings::HttpSettings::from_value(value, false)
        .map_err(|_| invalid("invalid HTTP settings"))?;
    let normalized = json!({"host":settings.host, "port":settings.port, "token":settings.token, "origins":settings.origins});
    for (key, value) in value.as_object_mut().expect("validated HTTP object") {
        *value = normalized[key].clone();
    }
    Ok(())
}

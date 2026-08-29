pub mod env;
pub mod file;
mod legacy;
mod merge;

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};

use crate::cli::CliOptions;
use crate::error::{Error, Result};
use crate::logging::Level;
use crate::provider::ProviderId;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AddressRules {
    Disabled,
    Rules(Vec<String>),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CacheSetting {
    Disabled,
    Default,
    Path(PathBuf),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TlsMode {
    Auto,
    Verify,
    Insecure,
    CustomCa(PathBuf),
}

#[derive(Debug)]
pub struct LogConfig {
    pub level: Level,
    pub file: Option<PathBuf>,
    pub format: Option<String>,
    pub date_format: Option<String>,
}

#[derive(Debug)]
pub struct Config {
    pub provider: ProviderId,
    pub id: String,
    pub token: String,
    pub endpoint: Option<String>,
    pub index4: AddressRules,
    pub index6: AddressRules,
    pub ipv4: Vec<String>,
    pub ipv6: Vec<String>,
    pub ttl: Option<u32>,
    pub line: Option<String>,
    pub proxies: Vec<String>,
    pub cache: CacheSetting,
    pub cache_max_age: u64,
    pub tls: TlsMode,
    pub log: LogConfig,
    pub extra: BTreeMap<String, Value>,
}

#[derive(Debug)]
pub struct Bootstrap {
    pub proxies: Vec<String>,
    pub tls: TlsMode,
}

impl Bootstrap {
    pub fn from_sources(
        cli: &BTreeMap<String, Value>,
        environment: &BTreeMap<String, Value>,
    ) -> Result<Self> {
        let value = |key| cli.get(key).or_else(|| environment.get(key));
        Ok(Self {
            proxies: value_list(value("proxy"), false)?,
            tls: parse_tls(value("ssl"))?,
        })
    }
}

pub fn load(
    cli: &CliOptions,
    environment: &BTreeMap<String, Value>,
    fetch: &dyn Fn(&str) -> Result<String>,
) -> Result<Vec<Config>> {
    let paths = config_paths(cli, environment)?;
    let allow_debug_provider =
        paths.is_empty() && cli.values.get("debug").and_then(Value::as_bool) == Some(true);
    let mut documents = Vec::new();
    if paths.is_empty() {
        documents.push(BTreeMap::new());
    } else {
        for path in &paths {
            let document = file::load(path, fetch)?;
            let expanded = merge::expand_document(document)?;
            if expanded.is_empty() {
                return Err(Error::Config(format!(
                    "configuration `{}` does not contain any provider entries",
                    crate::http::redact_url(path)
                )));
            }
            documents.extend(expanded);
        }
    }

    documents
        .iter()
        .enumerate()
        .map(|(index, document)| {
            Config::from_sources(&cli.values, document, environment, allow_debug_provider)
                .map_err(|error| Error::Config(format!("configuration {}: {error}", index + 1)))
        })
        .collect()
}

fn config_paths(cli: &CliOptions, environment: &BTreeMap<String, Value>) -> Result<Vec<String>> {
    if let Some(paths) = &cli.config_paths {
        return Ok(paths.clone());
    }
    if let Some(value) = environment.get("config") {
        return value_list(Some(value), false);
    }
    Ok(file::existing_default().into_iter().collect())
}

impl Config {
    fn from_sources(
        cli: &BTreeMap<String, Value>,
        document: &BTreeMap<String, Value>,
        environment: &BTreeMap<String, Value>,
        allow_debug_provider: bool,
    ) -> Result<Self> {
        let value = |key| {
            cli.get(key)
                .or_else(|| document.get(key))
                .or_else(|| environment.get(key))
        };
        parse_bool(value("debug"), false)?;
        let mut provider = optional_string(value("dns"))?
            .unwrap_or_default()
            .to_ascii_lowercase();
        if provider.is_empty() && allow_debug_provider {
            provider = "debug".to_owned();
        }
        if provider.is_empty() {
            return Err(Error::Config(
                "no DNS provider specified; set `dns` or use `--dns`".to_owned(),
            ));
        }
        let provider = provider.parse::<ProviderId>()?;

        let id = optional_string(value("id"))?.unwrap_or_default();
        let token = match value("token") {
            Some(Value::Object(value)) if provider == ProviderId::Callback => {
                serde_json::to_string(value)?
            }
            value => optional_string(value)?.unwrap_or_default(),
        };
        let endpoint = optional_string(value("endpoint"))?.filter(|endpoint| !endpoint.is_empty());
        if let Some(endpoint) = &endpoint
            && !endpoint.starts_with("http://")
            && !endpoint.starts_with("https://")
        {
            return Err(Error::Config(
                "`endpoint` must start with http:// or https://".to_owned(),
            ));
        }

        let ipv4 = domain_list(value("ipv4"))?;
        let ipv6 = domain_list(value("ipv6"))?;
        let index4 = address_rules(value("index4"), &["default"])?;
        let index6 = address_rules(value("index6"), &["default"])?;
        let ttl = optional_u32(value("ttl"), "ttl")?;
        let line = optional_string(value("line"))?;
        let proxies = value_list(value("proxy"), false)?;
        let cache = parse_cache(value("cache"))?;
        let cache_max_age =
            optional_u64(value("cache_max_age"), "cache_max_age")?.unwrap_or(259_200);
        let tls = parse_tls(value("ssl"))?;
        let level = Level::parse(
            optional_string(value("log_level"))?
                .as_deref()
                .unwrap_or("INFO"),
        )?;
        let log = LogConfig {
            level,
            file: optional_string(value("log_file"))?.map(PathBuf::from),
            format: optional_string(value("log_format"))?,
            date_format: optional_string(value("log_datefmt"))?,
        };
        let extra = collect_extra(environment, document, cli)?;

        Ok(Self {
            provider,
            id,
            token,
            endpoint,
            index4,
            index6,
            ipv4,
            ipv6,
            ttl,
            line,
            proxies,
            cache,
            cache_max_age,
            tls,
            log,
            extra,
        })
    }

    pub fn cache_identity(&self) -> Value {
        json!({
            "provider": self.provider.as_str(),
            "id": self.id,
            "token": self.token,
            "endpoint": self.endpoint,
            "index4": rules_value(&self.index4),
            "index6": rules_value(&self.index6),
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "ttl": self.ttl,
            "line": self.line,
            "proxy": self.proxies,
            "ssl": tls_value(&self.tls),
            "extra": self.extra,
        })
    }
}

pub fn write_template(path: &Path, cli: &BTreeMap<String, Value>) -> Result<()> {
    if let Some(parent) = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
    {
        fs::create_dir_all(parent)?;
    }
    let value = |key: &str, default: Value| cli.get(key).cloned().unwrap_or(default);
    let mut document = Map::from_iter([
        (
            "$schema".to_owned(),
            json!("https://ddns.newfuture.cc/schema/v4.1.json"),
        ),
        ("dns".to_owned(), value("dns", json!("debug"))),
        (
            "id".to_owned(),
            value("id", json!("YOUR ID or EMAIL for DNS Provider")),
        ),
        (
            "token".to_owned(),
            value("token", json!("YOUR TOKEN or KEY for DNS Provider")),
        ),
        ("endpoint".to_owned(), value("endpoint", Value::Null)),
        (
            "ipv4".to_owned(),
            value("ipv4", json!(["ddns.newfuture.cc"])),
        ),
        ("index4".to_owned(), value("index4", json!(["default"]))),
        ("ipv6".to_owned(), value("ipv6", json!([]))),
        ("index6".to_owned(), value("index6", json!([]))),
        ("ttl".to_owned(), value("ttl", json!(600))),
        ("line".to_owned(), value("line", Value::Null)),
        ("proxy".to_owned(), value("proxy", json!([]))),
        ("cache".to_owned(), value("cache", Value::Bool(true))),
        (
            "cache_max_age".to_owned(),
            value("cache_max_age", json!(259_200)),
        ),
        ("ssl".to_owned(), value("ssl", json!("auto"))),
        (
            "log".to_owned(),
            json!({
                "level": value("log_level", json!("INFO")),
                "file": value("log_file", Value::Null),
                "format": value("log_format", Value::Null),
                "datefmt": value("log_datefmt", Value::Null),
            }),
        ),
    ]);
    let extra = cli
        .iter()
        .filter_map(|(key, value)| {
            key.strip_prefix("extra_")
                .map(|key| (key.to_owned(), value.clone()))
        })
        .collect::<Map<String, Value>>();
    if !extra.is_empty() {
        document.insert("extra".to_owned(), Value::Object(extra));
    }
    let serialized = serde_json::to_string_pretty(&Value::Object(document))?;
    fs::write(path, format!("{serialized}\n"))?;
    Ok(())
}

fn collect_extra(
    environment: &BTreeMap<String, Value>,
    document: &BTreeMap<String, Value>,
    cli: &BTreeMap<String, Value>,
) -> Result<BTreeMap<String, Value>> {
    let mut result = BTreeMap::new();
    for source in [environment, document, cli] {
        if let Some(value) = source.get("extra") {
            let Value::Object(extra) = value else {
                return Err(Error::Config("`extra` must be an object".to_owned()));
            };
            result.extend(extra.clone());
        }
        for (key, value) in source {
            if let Some(key) = key.strip_prefix("extra_") {
                result.insert(key.to_owned(), value.clone());
            } else if !KNOWN_KEYS.contains(&key.as_str()) {
                result.insert(key.clone(), value.clone());
            }
        }
    }
    Ok(result)
}

const KNOWN_KEYS: &[&str] = &[
    "$schema",
    "cache",
    "cache_max_age",
    "command",
    "config",
    "debug",
    "dns",
    "endpoint",
    "extra",
    "id",
    "http",
    "http_host",
    "http_origins",
    "http_port",
    "http_token",
    "index4",
    "index6",
    "interval",
    "ipv4",
    "ipv6",
    "line",
    "log_datefmt",
    "log_file",
    "log_format",
    "log_level",
    "proxy",
    "ssl",
    "token",
    "ttl",
];

fn domain_list(value: Option<&Value>) -> Result<Vec<String>> {
    let domains = value_list(value, false)?;
    for domain in &domains {
        if domain.trim().is_empty() || !domain.contains('.') {
            return Err(Error::Config(format!("invalid domain: `{domain}`")));
        }
    }
    Ok(domains)
}

fn address_rules(value: Option<&Value>, default: &[&str]) -> Result<AddressRules> {
    if value == Some(&Value::Bool(false)) {
        return Ok(AddressRules::Disabled);
    }
    if value.is_none() {
        return Ok(AddressRules::Rules(
            default.iter().map(|value| (*value).to_owned()).collect(),
        ));
    }
    let rules = value_list(value, true)?;
    if rules.is_empty() {
        Ok(AddressRules::Disabled)
    } else {
        Ok(AddressRules::Rules(rules))
    }
}

pub fn value_list(value: Option<&Value>, preserve_special: bool) -> Result<Vec<String>> {
    match value {
        None | Some(Value::Null) | Some(Value::Bool(false)) => Ok(Vec::new()),
        Some(Value::Array(values)) => values.iter().map(value_string).collect(),
        Some(Value::String(value))
            if matches!(value.trim().to_ascii_lowercase().as_str(), "false" | "none") =>
        {
            Ok(Vec::new())
        }
        Some(Value::String(value)) => Ok(split_array_string(value, preserve_special)),
        Some(value) => Ok(vec![value_string(value)?]),
    }
}

pub fn split_array_string(value: &str, preserve_special: bool) -> Vec<String> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Vec::new();
    }
    let scope_end = if preserve_special {
        ["url:", "regex:", "cmd:", "shell:"]
            .iter()
            .filter_map(|prefix| {
                trimmed.match_indices(prefix).find_map(|(position, _)| {
                    let preceding = trimmed[..position].trim_end();
                    (preceding.is_empty() || preceding.ends_with(',') || preceding.ends_with(';'))
                        .then_some(position)
                })
            })
            .min()
            .unwrap_or(trimmed.len())
    } else {
        trimmed.len()
    };
    let delimiter = if trimmed[..scope_end].contains(',') {
        Some(',')
    } else if trimmed[..scope_end].contains(';') {
        Some(';')
    } else {
        None
    };
    let Some(delimiter) = delimiter else {
        return vec![trimmed.to_owned()];
    };
    let parts = trimmed.split(delimiter).collect::<Vec<_>>();
    let mut result = Vec::new();
    let mut index = 0;
    while index < parts.len() {
        let part = parts[index].trim();
        if part.is_empty() {
            index += 1;
            continue;
        }
        if preserve_special
            && ["url:", "regex:", "cmd:", "shell:"]
                .iter()
                .any(|prefix| part.starts_with(prefix))
        {
            result.push(
                parts[index..]
                    .join(&delimiter.to_string())
                    .trim()
                    .to_owned(),
            );
            break;
        }
        result.push(part.to_owned());
        index += 1;
    }
    result
}

fn optional_string(value: Option<&Value>) -> Result<Option<String>> {
    match value {
        None | Some(Value::Null) => Ok(None),
        Some(Value::String(value)) => Ok(Some(value.clone())),
        Some(value) => Ok(Some(value_string(value)?)),
    }
}

fn value_string(value: &Value) -> Result<String> {
    match value {
        Value::String(value) => Ok(value.clone()),
        Value::Number(value) => Ok(value.to_string()),
        Value::Bool(value) => Ok(value.to_string().to_ascii_lowercase()),
        Value::Null => Ok(String::new()),
        Value::Array(_) | Value::Object(_) => Err(Error::Config(
            "expected a scalar or list of scalars".to_owned(),
        )),
    }
}

fn parse_bool(value: Option<&Value>, default: bool) -> Result<bool> {
    match value {
        None | Some(Value::Null) => Ok(default),
        Some(Value::Bool(value)) => Ok(*value),
        Some(Value::Number(value)) => Ok(value.as_i64().unwrap_or_default() != 0),
        Some(Value::String(value)) => match value.to_ascii_lowercase().as_str() {
            "yes" | "true" | "t" | "y" | "1" => Ok(true),
            "no" | "false" | "f" | "n" | "0" | "none" => Ok(false),
            _ => Err(Error::Config(format!("invalid boolean value: `{value}`"))),
        },
        Some(_) => Err(Error::Config("invalid boolean value".to_owned())),
    }
}

fn optional_u64(value: Option<&Value>, field: &str) -> Result<Option<u64>> {
    match value {
        None | Some(Value::Null) => Ok(None),
        Some(Value::Number(value)) => value
            .as_u64()
            .map(Some)
            .ok_or_else(|| Error::Config(format!("`{field}` must be a non-negative integer"))),
        Some(Value::String(value)) => value
            .parse::<u64>()
            .map(Some)
            .map_err(|_| Error::Config(format!("`{field}` must be a non-negative integer"))),
        _ => Err(Error::Config(format!(
            "`{field}` must be a non-negative integer"
        ))),
    }
}

fn optional_u32(value: Option<&Value>, field: &str) -> Result<Option<u32>> {
    optional_u64(value, field)?
        .map(|value| {
            u32::try_from(value).map_err(|_| Error::Config(format!("`{field}` is too large")))
        })
        .transpose()
}

fn parse_cache(value: Option<&Value>) -> Result<CacheSetting> {
    match value {
        None | Some(Value::Null) | Some(Value::Bool(true)) => Ok(CacheSetting::Default),
        Some(Value::Bool(false)) => Ok(CacheSetting::Disabled),
        Some(Value::String(value)) => match value.to_ascii_lowercase().as_str() {
            "yes" | "true" | "t" | "y" | "1" => Ok(CacheSetting::Default),
            "no" | "false" | "f" | "n" | "0" | "none" => Ok(CacheSetting::Disabled),
            _ => Ok(CacheSetting::Path(PathBuf::from(value))),
        },
        _ => Err(Error::Config(
            "`cache` must be a boolean or path".to_owned(),
        )),
    }
}

pub fn parse_tls(value: Option<&Value>) -> Result<TlsMode> {
    match value {
        None | Some(Value::Null) => Ok(TlsMode::Auto),
        Some(Value::Bool(true)) => Ok(TlsMode::Verify),
        Some(Value::Bool(false)) => Ok(TlsMode::Insecure),
        Some(Value::String(value)) => match value.to_ascii_lowercase().as_str() {
            "auto" => Ok(TlsMode::Auto),
            "yes" | "true" | "t" | "y" | "1" => Ok(TlsMode::Verify),
            "" | "no" | "false" | "f" | "n" | "0" | "none" => Ok(TlsMode::Insecure),
            _ => Ok(TlsMode::CustomCa(PathBuf::from(value))),
        },
        _ => Err(Error::Config(
            "`ssl` must be true, false, auto, or a CA file path".to_owned(),
        )),
    }
}

fn rules_value(rules: &AddressRules) -> Value {
    match rules {
        AddressRules::Disabled => Value::Bool(false),
        AddressRules::Rules(rules) => json!(rules),
    }
}

fn tls_value(tls: &TlsMode) -> Value {
    match tls {
        TlsMode::Auto => Value::String("auto".to_owned()),
        TlsMode::Verify => Value::Bool(true),
        TlsMode::Insecure => Value::Bool(false),
        TlsMode::CustomCa(path) => Value::String(path.display().to_string()),
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use serde_json::json;

    use crate::logging::Level;

    use crate::provider::ProviderId;

    use super::{AddressRules, Config, TlsMode, parse_tls, split_array_string};

    #[test]
    fn preserves_special_rule_tail() {
        assert_eq!(
            split_array_string("public,regex:192\\.168\\..*,backup", true),
            vec!["public", "regex:192\\.168\\..*,backup"]
        );
    }

    #[test]
    fn merges_cli_over_file_over_environment() {
        let environment = BTreeMap::from([
            ("dns".to_owned(), json!("debug")),
            ("ttl".to_owned(), json!("100")),
        ]);
        let document = BTreeMap::from([("ttl".to_owned(), json!(200))]);
        let cli = BTreeMap::from([("ttl".to_owned(), json!(300))]);
        let config = Config::from_sources(&cli, &document, &environment, false).unwrap();
        assert_eq!(config.ttl, Some(300));
        assert_eq!(
            config.index4,
            AddressRules::Rules(vec!["default".to_owned()])
        );
    }

    #[test]
    fn explicit_false_disables_address_family() {
        let cli = BTreeMap::from([
            ("dns".to_owned(), json!("debug")),
            ("index4".to_owned(), json!(false)),
        ]);
        let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new(), false).unwrap();
        assert_eq!(config.index4, AddressRules::Disabled);
    }

    #[test]
    fn normalizes_provider_names_and_empty_tls_environment_value() {
        let cli = BTreeMap::from([("dns".to_owned(), json!("CloudFlare"))]);
        let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new(), false).unwrap();
        assert_eq!(config.provider, ProviderId::Cloudflare);
        assert_eq!(
            parse_tls(Some(&serde_json::Value::String(String::new()))).unwrap(),
            TlsMode::Insecure
        );
        assert_eq!(
            parse_tls(Some(&serde_json::Value::String("none".to_owned()))).unwrap(),
            TlsMode::Insecure
        );
    }

    #[test]
    fn accepts_named_aliases_and_numeric_log_thresholds() {
        for (value, expected) in [
            (json!("NOTSET"), Level::NotSet),
            (json!("FATAL"), Level::Critical),
            (json!(25), Level::Custom(25)),
        ] {
            let cli = BTreeMap::from([
                ("dns".to_owned(), json!("debug")),
                ("log_level".to_owned(), value),
            ]);
            let config =
                Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new(), false).unwrap();
            assert_eq!(config.log.level, expected);
        }
    }

    #[test]
    fn limits_debug_provider_fallback_and_ignores_empty_endpoint() {
        let cli_debug = BTreeMap::from([("debug".to_owned(), json!(true))]);
        let config =
            Config::from_sources(&cli_debug, &BTreeMap::new(), &BTreeMap::new(), true).unwrap();
        assert_eq!(config.provider, ProviderId::Debug);
        assert!(
            Config::from_sources(&cli_debug, &BTreeMap::new(), &BTreeMap::new(), false).is_err()
        );

        let environment_debug = BTreeMap::from([("debug".to_owned(), json!("true"))]);
        assert!(
            Config::from_sources(
                &BTreeMap::new(),
                &BTreeMap::new(),
                &environment_debug,
                false
            )
            .is_err()
        );

        let cli = BTreeMap::from([
            ("dns".to_owned(), json!("debug")),
            ("endpoint".to_owned(), json!("")),
        ]);
        let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new(), false).unwrap();
        assert_eq!(config.endpoint, None);
    }

    #[test]
    fn serializes_callback_object_tokens() {
        let document = BTreeMap::from([
            ("dns".to_owned(), json!("callback")),
            ("id".to_owned(), json!("https://callback.example/update")),
            (
                "token".to_owned(),
                json!({"api_key": "secret", "address": "__IP__"}),
            ),
        ]);
        let config =
            Config::from_sources(&BTreeMap::new(), &document, &BTreeMap::new(), false).unwrap();
        assert_eq!(
            serde_json::from_str::<serde_json::Value>(&config.token).unwrap(),
            json!({"api_key": "secret", "address": "__IP__"})
        );
    }

    #[test]
    fn aliases_share_canonical_cache_identity() {
        let config = |provider| {
            Config::from_sources(
                &BTreeMap::from([("dns".to_owned(), json!(provider))]),
                &BTreeMap::new(),
                &BTreeMap::new(),
                false,
            )
            .unwrap()
        };
        assert_eq!(
            config("aliyun").cache_identity(),
            config("alidns").cache_identity()
        );
    }
}

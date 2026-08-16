pub mod env;
pub mod file;
mod legacy;
mod merge;

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};

use crate::cli::CliOptions;
use crate::error::{Error, Result};
use crate::logging::Level;

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

#[derive(Clone, Debug)]
pub struct LogConfig {
    pub level: Level,
    pub file: Option<PathBuf>,
    pub format: Option<String>,
    pub date_format: Option<String>,
}

#[derive(Clone, Debug)]
pub struct Config {
    pub provider: String,
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
    pub debug: bool,
}

#[derive(Clone, Debug)]
pub struct Bootstrap {
    pub proxies: Vec<String>,
    pub tls: TlsMode,
}

impl Bootstrap {
    pub fn from_sources(
        cli: &BTreeMap<String, Value>,
        environment: &BTreeMap<String, Value>,
    ) -> Result<Self> {
        let mut merged = environment.clone();
        merged.extend(cli.clone());
        Ok(Self {
            proxies: value_list(merged.get("proxy"), false)?,
            tls: parse_tls(merged.get("ssl"))?,
        })
    }
}

pub fn load(
    cli: &CliOptions,
    environment: &BTreeMap<String, Value>,
    fetch: &dyn Fn(&str) -> Result<String>,
) -> Result<Vec<Config>> {
    let paths = config_paths(cli, environment)?;
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
            Config::from_sources(&cli.values, document, environment)
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
    ) -> Result<Self> {
        let merged = merge::merge(environment, document, cli);
        let debug = parse_bool(merged.get("debug"), false)?;
        let mut provider = optional_string(merged.get("dns"))?
            .unwrap_or_default()
            .to_ascii_lowercase();
        if provider.is_empty() && debug {
            provider = "debug".to_owned();
        }
        if provider.is_empty() {
            return Err(Error::Config(
                "no DNS provider specified; set `dns` or use `--dns`".to_owned(),
            ));
        }
        if !matches!(
            provider.as_str(),
            "debug" | "cloudflare" | "alidns" | "dnspod"
        ) {
            return Err(Error::Unsupported(format!(
                "provider `{provider}` is not supported by the Rust MVP"
            )));
        }

        let id = optional_string(merged.get("id"))?.unwrap_or_default();
        let token = optional_string(merged.get("token"))?.unwrap_or_default();
        let endpoint = optional_string(merged.get("endpoint"))?;
        if let Some(endpoint) = &endpoint
            && !endpoint.starts_with("http://")
            && !endpoint.starts_with("https://")
        {
            return Err(Error::Config(
                "`endpoint` must start with http:// or https://".to_owned(),
            ));
        }

        let ipv4 = domain_list(merged.get("ipv4"))?;
        let ipv6 = domain_list(merged.get("ipv6"))?;
        let index4 = address_rules(merged.get("index4"), &["default"])?;
        let index6 = address_rules(merged.get("index6"), &["default"])?;
        let ttl = optional_u32(merged.get("ttl"), "ttl")?;
        let line = optional_string(merged.get("line"))?;
        let proxies = value_list(merged.get("proxy"), false)?;
        let cache = parse_cache(merged.get("cache"))?;
        let cache_max_age =
            optional_u64(merged.get("cache_max_age"), "cache_max_age")?.unwrap_or(259_200);
        let tls = parse_tls(merged.get("ssl"))?;
        let level = Level::parse(
            optional_string(merged.get("log_level"))?
                .as_deref()
                .unwrap_or("INFO"),
        )?;
        let log = LogConfig {
            level,
            file: optional_string(merged.get("log_file"))?.map(PathBuf::from),
            format: optional_string(merged.get("log_format"))?,
            date_format: optional_string(merged.get("log_datefmt"))?,
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
            debug,
        })
    }

    pub fn cache_identity(&self) -> Value {
        json!({
            "provider": self.provider,
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
    let mut document = Map::new();
    document.insert(
        "$schema".to_owned(),
        Value::String("https://ddns.newfuture.cc/schema/v4.1.json".to_owned()),
    );
    document.insert(
        "dns".to_owned(),
        cli.get("dns")
            .cloned()
            .unwrap_or_else(|| Value::String("debug".to_owned())),
    );
    document.insert(
        "id".to_owned(),
        cli.get("id")
            .cloned()
            .unwrap_or_else(|| Value::String("YOUR ID or EMAIL for DNS Provider".to_owned())),
    );
    document.insert(
        "token".to_owned(),
        cli.get("token")
            .cloned()
            .unwrap_or_else(|| Value::String("YOUR TOKEN or KEY for DNS Provider".to_owned())),
    );
    document.insert(
        "endpoint".to_owned(),
        cli.get("endpoint").cloned().unwrap_or(Value::Null),
    );
    document.insert(
        "ipv4".to_owned(),
        cli.get("ipv4")
            .cloned()
            .unwrap_or_else(|| json!(["ddns.newfuture.cc"])),
    );
    document.insert(
        "index4".to_owned(),
        cli.get("index4")
            .cloned()
            .unwrap_or_else(|| json!(["default"])),
    );
    document.insert(
        "ipv6".to_owned(),
        cli.get("ipv6").cloned().unwrap_or_else(|| json!([])),
    );
    document.insert(
        "index6".to_owned(),
        cli.get("index6").cloned().unwrap_or_else(|| json!([])),
    );
    document.insert(
        "ttl".to_owned(),
        cli.get("ttl").cloned().unwrap_or(Value::Null),
    );
    document.insert(
        "line".to_owned(),
        cli.get("line").cloned().unwrap_or(Value::Null),
    );
    document.insert(
        "proxy".to_owned(),
        cli.get("proxy").cloned().unwrap_or_else(|| json!([])),
    );
    document.insert(
        "cache".to_owned(),
        cli.get("cache").cloned().unwrap_or(Value::Bool(true)),
    );
    document.insert(
        "cache_max_age".to_owned(),
        cli.get("cache_max_age")
            .cloned()
            .unwrap_or_else(|| json!(259_200)),
    );
    document.insert(
        "ssl".to_owned(),
        cli.get("ssl")
            .cloned()
            .unwrap_or_else(|| Value::String("auto".to_owned())),
    );
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
    document.insert(
        "log".to_owned(),
        json!({
            "level": cli.get("log_level").cloned().unwrap_or_else(|| Value::String("INFO".to_owned())),
            "file": cli.get("log_file").cloned().unwrap_or(Value::Null),
            "format": cli.get("log_format").cloned().unwrap_or(Value::Null),
            "datefmt": cli.get("log_datefmt").cloned().unwrap_or(Value::Null),
        }),
    );
    let serialized = serde_json::to_string_pretty(&Value::Object(document))?;
    fs::write(path, format!("{serialized}\n"))?;
    Ok(())
}

fn collect_extra(
    environment: &BTreeMap<String, Value>,
    document: &BTreeMap<String, Value>,
    cli: &BTreeMap<String, Value>,
) -> Result<BTreeMap<String, Value>> {
    let known = known_keys();
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
            } else if !known.contains(key.as_str()) {
                result.insert(key.clone(), value.clone());
            }
        }
    }
    Ok(result)
}

fn known_keys() -> BTreeSet<&'static str> {
    [
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
    ]
    .into_iter()
    .collect()
}

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
            "" | "no" | "false" | "f" | "n" | "0" => Ok(TlsMode::Insecure),
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
        let config = Config::from_sources(&cli, &document, &environment).unwrap();
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
        let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new()).unwrap();
        assert_eq!(config.index4, AddressRules::Disabled);
    }

    #[test]
    fn normalizes_provider_names_and_empty_tls_environment_value() {
        let cli = BTreeMap::from([("dns".to_owned(), json!("CloudFlare"))]);
        let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new()).unwrap();
        assert_eq!(config.provider, "cloudflare");
        assert_eq!(
            parse_tls(Some(&serde_json::Value::String(String::new()))).unwrap(),
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
            let config = Config::from_sources(&cli, &BTreeMap::new(), &BTreeMap::new()).unwrap();
            assert_eq!(config.log.level, expected);
        }
    }
}

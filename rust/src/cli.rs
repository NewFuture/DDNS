use std::collections::BTreeMap;
use std::ffi::{OsStr, OsString};

use serde_json::{Number, Value};

use crate::error::{Error, Result};

pub const HELP: &str = "\
DDNS Rust client

Usage: ddns-rs [OPTIONS]

Options:
  -c, --config <FILE>...       Load local or remote configuration files
      --dns <PROVIDER>         DNS provider
      --id <ID>                API ID, account, or email
      --token <TOKEN>          API token or secret
      --endpoint <URL>         Override the provider API endpoint
      --index4 <RULE>...       IPv4 discovery rules
      --index6 <RULE>...       IPv6 discovery rules
      --ipv4 <DOMAIN>...       IPv4 domains
      --ipv6 <DOMAIN>...       IPv6 domains
      --ttl <SECONDS>          DNS TTL
      --line <LINE>            DNS route/line
      --proxy <PROXY>...       Proxy fallback list
      --cache [PATH|BOOL]      Enable cache or select a cache path
      --cache-max-age <SEC>    Cache file maximum age
      --no-cache               Disable cache
      --ssl [BOOL|auto|CA]     TLS verification policy
      --no-ssl                 Disable TLS certificate verification
      --log-level <LEVEL>      NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL/FATAL, or integer
      --log-file <FILE>        Write logs to a file
      --log-format <FORMAT>    Accepted for Python CLI compatibility
      --log-datefmt <FORMAT>   Accepted for Python CLI compatibility
      --extra.<KEY> [VALUE]    Provider-specific option
      --debug                  Debug logging and no cache by default
      --new-config [FILE]      Generate a template configuration
  -v, --version                Print version information
  -h, --help                   Print help

Providers:
  debug, cloudflare, alidns, dnspod, dnspod_com, tencentcloud, edgeone,
  edgeone_dns, cloudns, aliesa, dnscom, he, huaweidns, namesilo, noip,
  callback, west
Documented compatibility aliases are also accepted.
Regex note: regex: rules use Rust regex syntax; Python look-around/backreferences are unsupported.
";

#[derive(Clone, Debug, Default)]
pub struct CliOptions {
    pub values: BTreeMap<String, Value>,
    pub config_paths: Option<Vec<String>>,
    pub new_config: Option<Option<String>>,
}

#[derive(Clone, Debug)]
pub enum Command {
    Help,
    Version,
    Run(CliOptions),
}

pub fn parse<I, S>(arguments: I) -> Result<Command>
where
    I: IntoIterator<Item = S>,
    S: Into<OsString> + Clone,
{
    let args = arguments
        .into_iter()
        .map(Into::into)
        .collect::<Vec<OsString>>();
    let mut index = usize::from(!args.is_empty());
    let mut options = CliOptions::default();

    while index < args.len() {
        let raw = os_to_string(&args[index])?;
        if raw == "-h" || raw == "--help" {
            return Ok(Command::Help);
        }
        if raw == "-v" || raw == "--version" {
            return Ok(Command::Version);
        }
        if matches!(raw.as_str(), "task" | "web" | "mcp") {
            return Err(Error::Unsupported(format!(
                "the `{raw}` command is not supported by the Rust MVP"
            )));
        }
        if !raw.starts_with('-') {
            return Err(Error::Usage(format!("unexpected argument: {raw}")));
        }

        let (name, inline) = split_option(&raw);
        match name {
            "-c" | "--config" => {
                let values = collect_list(&args, &mut index, inline)?;
                options
                    .config_paths
                    .get_or_insert_with(Vec::new)
                    .extend(values);
            }
            "--index4" | "--index6" | "--ipv4" | "--ipv6" | "--proxy" => {
                let key = name.trim_start_matches('-').replace('-', "_");
                let values = collect_list(&args, &mut index, inline)?;
                append_array(&mut options.values, &key, values);
            }
            "--dns" | "--id" | "--token" | "--endpoint" | "--line" => {
                let key = name.trim_start_matches('-').replace('-', "_");
                let value = collect_scalar(&args, &mut index, inline, name)?;
                options.values.insert(key, Value::String(value));
            }
            "--ttl" | "--cache-max-age" | "--cache_max_age" => {
                let key = name
                    .trim_start_matches('-')
                    .replace('-', "_")
                    .to_ascii_lowercase();
                let value = collect_scalar(&args, &mut index, inline, name)?;
                let parsed = value
                    .parse::<u64>()
                    .map_err(|_| Error::Usage(format!("{name} must be a non-negative integer")))?;
                options
                    .values
                    .insert(key, Value::Number(Number::from(parsed)));
            }
            "--cache" => {
                let value = collect_optional(&args, &mut index, inline)
                    .map_or(Value::Bool(true), |value| parse_bool_or_string(&value));
                options.values.insert("cache".to_owned(), value);
            }
            "--no-cache" => {
                options
                    .values
                    .insert("cache".to_owned(), Value::Bool(false));
                index += 1;
            }
            "--ssl" => {
                let value = collect_optional(&args, &mut index, inline)
                    .map_or(Value::Bool(true), |value| parse_bool_or_string(&value));
                options.values.insert("ssl".to_owned(), value);
            }
            "--no-ssl" => {
                options.values.insert("ssl".to_owned(), Value::Bool(false));
                index += 1;
            }
            "--debug" => {
                options.values.insert("debug".to_owned(), Value::Bool(true));
                index += 1;
            }
            "--log_file" | "--log.file" | "--log-file" | "--log_level" | "--log.level"
            | "--log-level" | "--log_format" | "--log.format" | "--log-format"
            | "--log_datefmt" | "--log.datefmt" | "--log-datefmt" => {
                let value = collect_scalar(&args, &mut index, inline, name)?;
                options
                    .values
                    .insert(format!("log_{}", &name[6..]), Value::String(value));
            }
            "--new-config" => {
                options.new_config = Some(collect_optional(&args, &mut index, inline));
            }
            value if value.starts_with("--extra.") => {
                let key = format!("extra_{}", &value[8..]);
                let value = collect_optional(&args, &mut index, inline)
                    .map_or(Value::Bool(true), Value::String);
                options.values.insert(key, value);
            }
            _ => return Err(Error::Usage(format!("unknown option: {name}"))),
        }
    }

    if options.values.get("debug") == Some(&Value::Bool(true)) {
        options
            .values
            .insert("log_level".to_owned(), Value::String("DEBUG".to_owned()));
        options
            .values
            .entry("cache".to_owned())
            .or_insert(Value::Bool(false));
    }
    normalize_singleton_lists(&mut options.values);

    Ok(Command::Run(options))
}

fn normalize_singleton_lists(values: &mut BTreeMap<String, Value>) {
    for key in ["index4", "index6", "ipv4", "ipv6", "proxy"] {
        let Some(Value::Array(items)) = values.get_mut(key) else {
            continue;
        };
        let [Value::String(item)] = items.as_slice() else {
            continue;
        };
        if matches!(item.trim().to_ascii_lowercase().as_str(), "false" | "none") {
            items.clear();
            continue;
        }
        let normalized =
            crate::config::split_array_string(item, matches!(key, "index4" | "index6"));
        *items = normalized.into_iter().map(Value::String).collect();
    }
}

fn split_option(raw: &str) -> (&str, Option<&str>) {
    raw.split_once('=')
        .map_or((raw, None), |(name, value)| (name, Some(value)))
}

fn collect_scalar(
    args: &[OsString],
    index: &mut usize,
    inline: Option<&str>,
    name: &str,
) -> Result<String> {
    if let Some(value) = inline {
        *index += 1;
        return Ok(value.to_owned());
    }
    let value = args
        .get(*index + 1)
        .ok_or_else(|| Error::Usage(format!("{name} requires a value")))?;
    let value = os_to_string(value)?;
    if value.starts_with('-') {
        return Err(Error::Usage(format!("{name} requires a value")));
    }
    *index += 2;
    Ok(value)
}

fn collect_optional(args: &[OsString], index: &mut usize, inline: Option<&str>) -> Option<String> {
    if let Some(value) = inline {
        *index += 1;
        return Some(value.to_owned());
    }
    if let Some(value) = args.get(*index + 1)
        && !value.to_string_lossy().starts_with('-')
    {
        *index += 2;
        return Some(value.to_string_lossy().into_owned());
    }
    *index += 1;
    None
}

fn collect_list(args: &[OsString], index: &mut usize, inline: Option<&str>) -> Result<Vec<String>> {
    if let Some(value) = inline {
        *index += 1;
        return Ok(vec![value.to_owned()]);
    }
    let mut values = Vec::new();
    *index += 1;
    while let Some(value) = args.get(*index) {
        let value = os_to_string(value)?;
        if value.starts_with('-') {
            break;
        }
        values.push(value);
        *index += 1;
    }
    Ok(values)
}

fn append_array(map: &mut BTreeMap<String, Value>, key: &str, values: Vec<String>) {
    let entry = map
        .entry(key.to_owned())
        .or_insert_with(|| Value::Array(Vec::new()));
    let array = entry
        .as_array_mut()
        .expect("CLI list values always remain arrays");
    array.extend(values.into_iter().map(Value::String));
}

fn parse_bool_or_string(value: &str) -> Value {
    match value.to_ascii_lowercase().as_str() {
        "yes" | "true" | "t" | "y" | "1" => Value::Bool(true),
        "no" | "false" | "f" | "n" | "0" => Value::Bool(false),
        _ => Value::String(value.to_owned()),
    }
}

fn os_to_string(value: &OsStr) -> Result<String> {
    value
        .to_str()
        .map(ToOwned::to_owned)
        .ok_or_else(|| Error::Usage("arguments must be valid UTF-8".to_owned()))
}

#[cfg(test)]
mod tests {
    use super::{Command, parse};

    #[test]
    fn parses_repeated_and_space_separated_lists() {
        let Command::Run(options) = parse([
            "ddns-rs",
            "--ipv4",
            "a.example.com",
            "b.example.com",
            "--ipv4=c.example.com",
        ])
        .unwrap() else {
            panic!("expected run command");
        };
        assert_eq!(
            options.values["ipv4"],
            serde_json::json!(["a.example.com", "b.example.com", "c.example.com"])
        );
    }

    #[test]
    fn debug_sets_defaults_without_overriding_explicit_cache() {
        let Command::Run(options) = parse(["ddns-rs", "--debug", "--cache", "cache.json"]).unwrap()
        else {
            panic!("expected run command");
        };
        assert_eq!(options.values["log_level"], "DEBUG");
        assert_eq!(options.values["cache"], "cache.json");
    }

    #[test]
    fn rejects_mvp_subcommands() {
        let error = parse(["ddns-rs", "web"]).unwrap_err();
        assert!(error.to_string().contains("not supported"));
    }

    #[test]
    fn empty_list_clears_inherited_values() {
        let Command::Run(options) = parse(["ddns-rs", "--ipv4", "--ipv6", "--index4"]).unwrap()
        else {
            panic!("expected run command");
        };
        assert_eq!(options.values["ipv4"], serde_json::json!([]));
        assert_eq!(options.values["ipv6"], serde_json::json!([]));
        assert_eq!(options.values["index4"], serde_json::json!([]));
    }

    #[test]
    fn splits_singleton_cli_lists_like_python_config() {
        let Command::Run(options) = parse([
            "ddns-rs",
            "--ipv4=a.example.com,b.example.com",
            "--index4=public,default",
            "--proxy=DIRECT;SYSTEM",
        ])
        .unwrap() else {
            panic!("expected run command");
        };
        assert_eq!(
            options.values["ipv4"],
            serde_json::json!(["a.example.com", "b.example.com"])
        );
        assert_eq!(
            options.values["index4"],
            serde_json::json!(["public", "default"])
        );
        assert_eq!(
            options.values["proxy"],
            serde_json::json!(["DIRECT", "SYSTEM"])
        );
    }

    #[test]
    fn preserves_repeated_cli_list_items_without_resplitting() {
        let Command::Run(options) = parse([
            "ddns-rs",
            "--ipv4=a.example.com,b.example.com",
            "--ipv4=c.example.com,d.example.com",
        ])
        .unwrap() else {
            panic!("expected run command");
        };
        assert_eq!(
            options.values["ipv4"],
            serde_json::json!(["a.example.com,b.example.com", "c.example.com,d.example.com"])
        );
    }

    #[test]
    fn singleton_false_and_none_disable_cli_lists() {
        let Command::Run(options) = parse([
            "ddns-rs", "--ipv4", "none", "--index4", "false", "--proxy", "none",
        ])
        .unwrap() else {
            panic!("expected run command");
        };
        assert_eq!(options.values["ipv4"], serde_json::json!([]));
        assert_eq!(options.values["index4"], serde_json::json!([]));
        assert_eq!(options.values["proxy"], serde_json::json!([]));
    }

    #[test]
    fn help_describes_full_provider_support() {
        for provider in [
            "debug",
            "cloudflare",
            "alidns",
            "dnspod",
            "dnspod_com",
            "tencentcloud",
            "edgeone",
            "edgeone_dns",
            "cloudns",
            "aliesa",
            "dnscom",
            "he",
            "huaweidns",
            "namesilo",
            "noip",
            "callback",
            "west",
        ] {
            assert!(super::HELP.contains(provider), "missing {provider}");
        }
        assert!(!super::HELP.contains("MVP providers:"));
    }
}

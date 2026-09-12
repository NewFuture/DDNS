use std::ffi::OsString;
use std::path::{Path, PathBuf};

use crate::cache::Cache;
use crate::cli::{self, Command};
use crate::config::{self, AddressRules, Bootstrap};
use crate::error::{Error, Result};
use crate::http::{HttpClient, HttpRequest, UreqClient, redact_url};
use crate::ip::{self, AddressFamily};
use crate::logging::{Level, Logger};
use crate::provider::{self, ProviderId, RecordRequest};

pub fn run<I, S>(arguments: I) -> Result<()>
where
    I: IntoIterator<Item = S>,
    S: Into<OsString> + Clone,
{
    let command = cli::parse(arguments)?;
    match command {
        Command::Help => {
            print!("{}", cli::HELP);
            Ok(())
        }
        Command::Version => {
            println!(
                "ddns-rs v{} ({})",
                env!("CARGO_PKG_VERSION"),
                std::env::consts::OS
            );
            Ok(())
        }
        Command::Run(options) => run_options(options),
    }
}

fn run_options(options: cli::CliOptions) -> Result<()> {
    if let Some(path) = &options.new_config {
        let explicit = path.is_some();
        let path = PathBuf::from(path.as_deref().unwrap_or("config.json"));
        if !explicit && path.exists() {
            return Err(Error::Config(format!(
                "the default {} already exists; pass --new-config=FILE to overwrite another path",
                path.display()
            )));
        }
        config::write_template(&path, &options.values)?;
        println!("{} is generated.", path.display());
        return Ok(());
    }

    let environment = config::env::load();
    if options.values.is_empty()
        && options.config_paths.is_none()
        && environment.is_empty()
        && config::file::existing_default().is_none()
    {
        let path = Path::new("config.json");
        config::write_template(path, &options.values)?;
        return Err(Error::Provider(
            "no configuration was found; generated config.json".to_owned(),
        ));
    }

    let bootstrap_logger = Logger::new(
        bootstrap_level(&options.values, &environment)?,
        None::<&Path>,
        bootstrap_secrets(&options.values, &environment),
    )?;
    let bootstrap = Bootstrap::from_sources(&options.values, &environment)?;
    let bootstrap_client = UreqClient::new(bootstrap_logger.clone(), bootstrap.tls);
    let fetch = |url: &str| -> Result<String> {
        let response =
            bootstrap_client.execute(&HttpRequest::get(url, bootstrap.proxies.clone()))?;
        if !(200..300).contains(&response.status) || response.body.is_empty() {
            return Err(Error::Config(format!(
                "failed to load remote configuration `{}`: HTTP {} {}",
                redact_url(url),
                response.status,
                response.reason
            )));
        }
        Ok(response.body)
    };
    let configs = config::load(&options, &environment, &fetch)?;
    let outcomes = update_configs_with_output(&configs, &|| false, true);
    let failures: Vec<_> = outcomes
        .iter()
        .enumerate()
        .flat_map(|(index, outcome)| {
            outcome
                .failures
                .iter()
                .map(move |failure| format!("configuration {} {failure}", index + 1))
        })
        .collect();
    if failures.is_empty() {
        Ok(())
    } else {
        Err(Error::Provider(format!(
            "{} update operation(s) failed: {}",
            failures.len(),
            failures.join(" | ")
        )))
    }
}

#[derive(Clone, Debug)]
pub struct UpdatedRecord {
    pub domain: String,
    pub record_type: &'static str,
    pub address: String,
    pub changed: bool,
}

#[derive(Clone, Debug, Default)]
pub struct UpdateOutcome {
    pub failures: Vec<String>,
    pub records: Vec<UpdatedRecord>,
    pub cancelled: bool,
}

pub fn update_configs(
    configs: &[config::Config],
    cancelled: &(dyn Fn() -> bool + Sync),
) -> Vec<UpdateOutcome> {
    update_configs_with_output(configs, cancelled, false)
}

fn update_configs_with_output(
    configs: &[config::Config],
    cancelled: &(dyn Fn() -> bool + Sync),
    emit_debug: bool,
) -> Vec<UpdateOutcome> {
    let mut outcomes = Vec::new();
    for config in configs {
        let outcome = update_config_with_output(config, cancelled, emit_debug);
        let stopped = outcome.cancelled;
        outcomes.push(outcome);
        if stopped {
            break;
        }
    }
    outcomes
}

pub fn update_config(
    config: &config::Config,
    cancelled: &(dyn Fn() -> bool + Sync),
) -> UpdateOutcome {
    update_config_with_output(config, cancelled, false)
}

fn update_config_with_output(
    config: &config::Config,
    cancelled: &(dyn Fn() -> bool + Sync),
    emit_debug: bool,
) -> UpdateOutcome {
    let mut result = UpdateOutcome::default();
    if cancelled() {
        result.cancelled = true;
        return result;
    }
    let secrets = provider_secrets(config.provider, &config.id, &config.token);
    let logger = match Logger::new(
        config.log.level,
        config.log.file.as_deref(),
        secrets.clone(),
    ) {
        Ok(logger) => logger,
        Err(error) => {
            let logger = Logger::stderr(config.log.level, secrets);
            let message = masked_error(&logger, &error);
            logger.error("config", format!("failed to configure log file: {message}"));
            result.failures.push(format!("log setup: {message}"));
            logger
        }
    };
    if config.log.format.is_some() || config.log.date_format.is_some() {
        logger.warning(
            "config",
            "custom Python log format strings are accepted but not rendered by the Rust MVP",
        );
    }
    if [&config.index4, &config.index6].iter().any(|rules| {
        matches!(
            rules,
            AddressRules::Rules(rules)
                if rules
                    .iter()
                    .any(|rule| rule.starts_with("cmd:") || rule.starts_with("shell:"))
        )
    }) {
        logger.warning(
            "config",
            "cmd: and shell: address rules execute local commands; use only trusted configuration sources",
        );
    }
    logger.info("ddns", format!("running provider {}", config.provider));
    let client = UreqClient::new(logger.clone(), config.tls.clone());
    let mut provider =
        match provider::build_with_output(config, &client, logger.clone(), emit_debug) {
            Ok(provider) => provider,
            Err(error) => {
                let message = masked_error(&logger, &error);
                logger.error("ddns", &message);
                result.failures.push(message);
                return result;
            }
        };
    let mut cache = match Cache::open(
        &config.cache,
        &config.cache_identity(),
        config.cache_max_age,
        logger.clone(),
    ) {
        Ok(cache) => cache,
        Err(error) => {
            let message = masked_error(&logger, &error);
            logger.error("cache", &message);
            result.failures.push(format!("cache: {message}"));
            None
        }
    };

    for (family, rules, domains) in [
        (AddressFamily::V4, &config.index4, &config.ipv4),
        (AddressFamily::V6, &config.index6, &config.ipv6),
    ] {
        if cancelled() {
            result.cancelled = true;
            break;
        }
        let AddressRules::Rules(rules) = rules else {
            continue;
        };
        if domains.is_empty() {
            continue;
        }
        let address = match ip::resolve(family, rules, &client, &logger) {
            Ok(address) => address,
            Err(error) => {
                let message = masked_error(&logger, &error);
                logger.error("ip", &message);
                result
                    .failures
                    .push(format!("{} discovery: {message}", family.record_type()));
                continue;
            }
        };
        let domain_result = update_domains(
            provider.as_mut(),
            config.provider,
            cache.as_mut(),
            family,
            address,
            domains,
            config.ttl,
            config.line.as_deref(),
            &config.extra,
            &logger,
            cancelled,
        );
        result.failures.extend(domain_result.failures);
        result.records.extend(domain_result.records);
        if domain_result.cancelled {
            result.cancelled = true;
            break;
        }
    }

    if let Some(cache) = &mut cache
        && let Err(error) = cache.sync()
    {
        let message = masked_error(&logger, &error);
        logger.error("cache", &message);
        result.failures.push(format!("cache sync: {message}"));
    }
    result
}

#[allow(clippy::too_many_arguments)]
fn update_domains(
    provider: &mut dyn provider::Provider,
    provider_id: ProviderId,
    mut cache: Option<&mut Cache>,
    family: AddressFamily,
    address: std::net::IpAddr,
    domains: &[String],
    ttl: Option<u32>,
    line: Option<&str>,
    extra: &std::collections::BTreeMap<String, serde_json::Value>,
    logger: &Logger,
    cancelled: &(dyn Fn() -> bool + Sync),
) -> UpdateOutcome {
    let mut result = UpdateOutcome::default();
    let address = address.to_string();
    for domain in domains {
        if cancelled() {
            result.cancelled = true;
            break;
        }
        let domain = domain.to_ascii_lowercase();
        if cache
            .as_deref()
            .and_then(|cache| cache.get(provider_id, &domain, family.record_type()))
            == Some(address.as_str())
        {
            logger.info(
                "cache",
                format!(
                    "{}[{}] is unchanged at {}",
                    domain,
                    family.record_type(),
                    address
                ),
            );
            result.records.push(UpdatedRecord {
                domain,
                record_type: family.record_type(),
                address: address.clone(),
                changed: false,
            });
            continue;
        }
        let request = RecordRequest {
            domain: &domain,
            address: &address,
            record_type: family.record_type(),
            ttl,
            line,
            extra,
        };
        match provider.set_record(&request) {
            Ok(()) => {
                logger.info(
                    "ddns",
                    format!(
                        "updated {}[{}] to {}",
                        domain,
                        family.record_type(),
                        address
                    ),
                );
                result.records.push(UpdatedRecord {
                    domain: domain.clone(),
                    record_type: family.record_type(),
                    address: address.clone(),
                    changed: true,
                });
                if let Some(cache) = cache.as_deref_mut() {
                    cache.set(provider_id, &domain, family.record_type(), &address);
                }
            }
            Err(error) => {
                let message = masked_error(logger, &error);
                logger.error(
                    "ddns",
                    format!(
                        "failed to update {}[{}]: {message}",
                        domain,
                        family.record_type()
                    ),
                );
                result
                    .failures
                    .push(format!("{}[{}]: {message}", domain, family.record_type()));
            }
        }
    }
    result
}

fn masked_error(logger: &Logger, error: &impl std::fmt::Display) -> String {
    logger.mask(&error.to_string())
}

fn provider_secrets(provider: ProviderId, id: &str, token: &str) -> Vec<String> {
    let mut secrets = vec![id.to_owned(), token.to_owned()];
    if provider == ProviderId::Callback
        && let Ok(value) = serde_json::from_str::<serde_json::Value>(token)
    {
        collect_scalar_secrets(&value, &mut secrets);
    }
    secrets
}

fn collect_scalar_secrets(value: &serde_json::Value, secrets: &mut Vec<String>) {
    match value {
        serde_json::Value::String(value) => secrets.push(value.clone()),
        serde_json::Value::Number(value) => secrets.push(value.to_string()),
        serde_json::Value::Bool(value) => secrets.push(value.to_string()),
        serde_json::Value::Array(values) => {
            for value in values {
                collect_scalar_secrets(value, secrets);
            }
        }
        serde_json::Value::Object(values) => {
            for value in values.values() {
                collect_scalar_secrets(value, secrets);
            }
        }
        serde_json::Value::Null => {}
    }
}

fn bootstrap_level(
    cli: &std::collections::BTreeMap<String, serde_json::Value>,
    environment: &std::collections::BTreeMap<String, serde_json::Value>,
) -> Result<Level> {
    let value = cli
        .get("log_level")
        .or_else(|| environment.get("log_level"))
        .and_then(serde_json::Value::as_str)
        .unwrap_or("INFO");
    Level::parse(value)
}

fn bootstrap_secrets(
    cli: &std::collections::BTreeMap<String, serde_json::Value>,
    environment: &std::collections::BTreeMap<String, serde_json::Value>,
) -> Vec<String> {
    cli.get("token")
        .or_else(|| environment.get("token"))
        .and_then(serde_json::Value::as_str)
        .map(ToOwned::to_owned)
        .into_iter()
        .collect()
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::net::{IpAddr, Ipv4Addr};
    use std::path::Path;

    use crate::error::{Error, Result};
    use crate::ip::AddressFamily;
    use crate::logging::{Level, Logger};
    use crate::provider::{Provider, ProviderId, RecordRequest};

    use super::{provider_secrets, update_domains};

    struct PartialProvider {
        calls: Vec<String>,
    }

    impl Provider for PartialProvider {
        fn set_record(&mut self, request: &RecordRequest<'_>) -> Result<()> {
            self.calls.push(request.domain.to_owned());
            if request.domain.starts_with("fail") {
                Err(Error::Provider("expected secret-token failure".to_owned()))
            } else {
                Ok(())
            }
        }
    }

    #[test]
    fn continues_after_domain_failure_and_reports_it() {
        let logger = Logger::new(
            Level::Critical,
            None::<&Path>,
            vec!["secret-token".to_owned()],
        )
        .unwrap();
        let mut provider = PartialProvider { calls: Vec::new() };
        let failures = update_domains(
            &mut provider,
            ProviderId::Debug,
            None,
            AddressFamily::V4,
            IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1)),
            &["fail.example.com".to_owned(), "ok.example.com".to_owned()],
            None,
            None,
            &BTreeMap::new(),
            &logger,
            &|| false,
        )
        .failures;
        assert_eq!(provider.calls, vec!["fail.example.com", "ok.example.com"]);
        assert_eq!(failures.len(), 1);
        assert!(failures[0].contains("fail.example.com"));
        assert!(!failures[0].contains("secret-token"));
    }

    #[test]
    fn masks_both_provider_ids_and_tokens() {
        for provider in [ProviderId::Dnspod, ProviderId::Dnscom] {
            let logger = Logger::stderr(Level::Debug, provider_secrets(provider, "ID123", "TK123"));
            assert_eq!(logger.mask("id=ID123 token=TK123"), "id=*** token=***");
        }
    }

    #[test]
    fn callback_nested_scalar_values_are_registered_as_secrets() {
        let secrets = provider_secrets(
            ProviderId::Callback,
            "https://callback.example/update",
            r#"{"api_key":"callback-secret","nested":{"account":12345}}"#,
        );
        assert!(secrets.contains(&"callback-secret".to_owned()));
        assert!(secrets.contains(&"12345".to_owned()));
    }
}

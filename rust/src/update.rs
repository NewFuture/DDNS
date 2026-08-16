use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use crate::cache::Cache;
use crate::cli::{self, Command};
use crate::config::{self, AddressRules, Bootstrap};
use crate::error::{Error, Result};
use crate::http::{HttpClient, HttpRequest, UreqClient, redact_url};
use crate::ip::{self, AddressFamily};
use crate::logging::{Level, Logger};
use crate::provider::{self, RecordRequest};

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
    let bootstrap_client = UreqClient::new(bootstrap_logger.clone());
    let fetch = |url: &str| -> Result<String> {
        let response = bootstrap_client.execute(&HttpRequest::get(
            url,
            bootstrap.tls.clone(),
            bootstrap.proxies.clone(),
        ))?;
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
    let mut failures = Vec::new();

    for (index, config) in configs.iter().enumerate() {
        let logger = Logger::new(
            config.log.level,
            config.log.file.as_deref(),
            vec![config.token.clone()],
        )?;
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
        logger.info(
            "ddns",
            format!(
                "running configuration {}/{} with provider {}",
                index + 1,
                configs.len(),
                config.provider
            ),
        );
        let client: Arc<dyn HttpClient> = Arc::new(UreqClient::new(logger.clone()));
        let mut provider = match provider::build(config, Arc::clone(&client), logger.clone()) {
            Ok(provider) => provider,
            Err(error) => {
                logger.error("ddns", error.to_string());
                failures.push(format!("configuration {}: {error}", index + 1));
                continue;
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
                logger.error("cache", error.to_string());
                failures.push(format!("configuration {} cache: {error}", index + 1));
                Cache::disabled(logger.clone())
            }
        };

        for (family, rules, domains) in [
            (AddressFamily::V4, &config.index4, &config.ipv4),
            (AddressFamily::V6, &config.index6, &config.ipv6),
        ] {
            if domains.is_empty() || matches!(rules, AddressRules::Disabled) {
                continue;
            }
            let address = match ip::resolve(family, rules, &config.tls, client.as_ref(), &logger) {
                Ok(Some(address)) => address,
                Ok(None) => continue,
                Err(error) => {
                    logger.error("ip", error.to_string());
                    failures.push(format!(
                        "configuration {} {} discovery: {error}",
                        index + 1,
                        family.record_type()
                    ));
                    continue;
                }
            };
            failures.extend(
                update_domains(
                    provider.as_mut(),
                    &mut cache,
                    family,
                    address,
                    domains,
                    config.ttl,
                    config.line.as_deref(),
                    &config.extra,
                    &logger,
                )
                .into_iter()
                .map(|failure| format!("configuration {} {failure}", index + 1)),
            );
        }

        if let Err(error) = cache.sync() {
            logger.error("cache", error.to_string());
            failures.push(format!("configuration {} cache sync: {error}", index + 1));
        }
    }

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

#[allow(clippy::too_many_arguments)]
fn update_domains(
    provider: &mut dyn provider::Provider,
    cache: &mut Cache,
    family: AddressFamily,
    address: std::net::IpAddr,
    domains: &[String],
    ttl: Option<u32>,
    line: Option<&str>,
    extra: &std::collections::BTreeMap<String, serde_json::Value>,
    logger: &Logger,
) -> Vec<String> {
    let mut failures = Vec::new();
    let provider_name = provider.name();
    let address = address.to_string();
    for domain in domains {
        let domain = domain.to_ascii_lowercase();
        if cache.get(provider_name, &domain, family.record_type()) == Some(address.as_str()) {
            logger.info(
                "cache",
                format!(
                    "{}[{}] is unchanged at {}",
                    domain,
                    family.record_type(),
                    address
                ),
            );
            continue;
        }
        let request = RecordRequest {
            domain: domain.clone(),
            address: address.clone(),
            record_type: family.record_type().to_owned(),
            ttl,
            line: line.map(ToOwned::to_owned),
            extra: extra.clone(),
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
                cache.set(provider_name, &domain, family.record_type(), &address);
            }
            Err(error) => {
                logger.error(
                    "ddns",
                    format!(
                        "failed to update {}[{}]: {error}",
                        domain,
                        family.record_type()
                    ),
                );
                failures.push(format!("{}[{}]: {error}", domain, family.record_type()));
            }
        }
    }
    failures
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

    use crate::cache::Cache;
    use crate::error::{Error, Result};
    use crate::ip::AddressFamily;
    use crate::logging::{Level, Logger};
    use crate::provider::{Provider, RecordRequest};

    use super::update_domains;

    struct PartialProvider {
        calls: Vec<String>,
    }

    impl Provider for PartialProvider {
        fn name(&self) -> &'static str {
            "partial"
        }

        fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
            self.calls.push(request.domain.clone());
            if request.domain.starts_with("fail") {
                Err(Error::Provider("expected failure".to_owned()))
            } else {
                Ok(())
            }
        }
    }

    #[test]
    fn continues_after_domain_failure_and_reports_it() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let mut cache = Cache::disabled(logger.clone());
        let mut provider = PartialProvider { calls: Vec::new() };
        let failures = update_domains(
            &mut provider,
            &mut cache,
            AddressFamily::V4,
            IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1)),
            &["fail.example.com".to_owned(), "ok.example.com".to_owned()],
            None,
            None,
            &BTreeMap::new(),
            &logger,
        );
        assert_eq!(provider.calls, vec!["fail.example.com", "ok.example.com"]);
        assert_eq!(failures.len(), 1);
        assert!(failures[0].contains("fail.example.com"));
    }
}

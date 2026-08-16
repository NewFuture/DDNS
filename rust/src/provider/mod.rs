mod alidns;
pub mod base;
mod cloudflare;
mod debug;
mod dnspod;

use std::collections::BTreeMap;
use std::sync::Arc;

use crate::config::Config;
use crate::error::{Error, Result};
use crate::http::HttpClient;
use crate::logging::Logger;

pub use base::{Provider, RecordRequest};

pub fn build(
    config: &Config,
    client: Arc<dyn HttpClient>,
    logger: Logger,
) -> Result<Box<dyn Provider>> {
    let context = base::ProviderContext {
        id: config.id.clone(),
        token: config.token.clone(),
        endpoint: config.endpoint.clone().unwrap_or_else(|| {
            match config.provider.as_str() {
                "cloudflare" => "https://api.cloudflare.com",
                "alidns" => "https://alidns.aliyuncs.com",
                "dnspod" => "https://dnsapi.cn",
                _ => "",
            }
            .to_owned()
        }),
        proxies: config.proxies.clone(),
        tls: config.tls.clone(),
        client,
        logger,
    };
    match config.provider.as_str() {
        "debug" => Ok(Box::new(debug::DebugProvider)),
        "cloudflare" => Ok(Box::new(cloudflare::CloudflareProvider::new(context)?)),
        "alidns" => Ok(Box::new(alidns::AlidnsProvider::new(context)?)),
        "dnspod" => Ok(Box::new(dnspod::DnspodProvider::new(context)?)),
        provider => Err(Error::Unsupported(format!(
            "provider `{provider}` is not supported by the Rust MVP"
        ))),
    }
}

pub(crate) fn empty_zone_cache() -> BTreeMap<String, String> {
    BTreeMap::new()
}

mod alidns;
mod aliesa;
pub mod base;
mod cloudflare;
mod cloudns;
mod debug;
mod dnscom;
mod dnspod;
mod huaweidns;
mod namesilo;
mod simple;
mod tencentcloud;

use std::sync::Arc;

use crate::config::{Config, canonical_provider};
use crate::error::{Error, Result};
use crate::http::HttpClient;
use crate::logging::Logger;

pub use base::{Provider, RecordRequest};

pub fn build(
    config: &Config,
    client: Arc<dyn HttpClient>,
    logger: Logger,
) -> Result<Box<dyn Provider>> {
    let provider = canonical_provider(&config.provider).ok_or_else(|| {
        Error::Unsupported(format!(
            "provider `{}` is not supported by the Rust MVP",
            config.provider
        ))
    })?;
    let context = base::ProviderContext {
        id: config.id.clone(),
        token: config.token.clone(),
        endpoint: config
            .endpoint
            .clone()
            .unwrap_or_else(|| default_endpoint(provider).to_owned()),
        proxies: config.proxies.clone(),
        tls: config.tls.clone(),
        client,
        logger,
    };
    match provider {
        "debug" => Ok(Box::new(debug::DebugProvider)),
        "cloudflare" => Ok(Box::new(cloudflare::CloudflareProvider::new(context)?)),
        "alidns" => Ok(Box::new(alidns::AlidnsProvider::new(context)?)),
        "dnspod" => Ok(Box::new(dnspod::DnspodProvider::new(context)?)),
        "dnspod_com" => Ok(Box::new(dnspod::DnspodProvider::global(context)?)),
        "tencentcloud" => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "tencentcloud",
            "dnspod",
            "2021-03-23",
            false,
        )?)),
        "edgeone" => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "edgeone",
            "teo",
            "2022-09-01",
            false,
        )?)),
        "edgeone_dns" => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "edgeone_dns",
            "teo",
            "2022-09-01",
            true,
        )?)),
        "cloudns" => Ok(Box::new(cloudns::CloudnsProvider::new(context)?)),
        "aliesa" => Ok(Box::new(aliesa::AliesaProvider::new(context)?)),
        "dnscom" => Ok(Box::new(dnscom::DnscomProvider::new(context)?)),
        "he" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::He,
            "he",
        )?)),
        "huaweidns" => Ok(Box::new(huaweidns::HuaweiDnsProvider::new(context)?)),
        "namesilo" => Ok(Box::new(namesilo::NamesiloProvider::new(context)?)),
        "noip" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::NoIp,
            "noip",
        )?)),
        "callback" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::Callback,
            "callback",
        )?)),
        "west" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::West,
            "west",
        )?)),
        _ => Err(Error::Unsupported(format!(
            "provider `{}` is not supported by the Rust MVP",
            config.provider
        ))),
    }
}

fn default_endpoint(provider: &str) -> &'static str {
    match provider {
        "cloudflare" => "https://api.cloudflare.com",
        "alidns" => "https://alidns.aliyuncs.com",
        "dnspod" => "https://dnsapi.cn",
        "dnspod_com" => "https://api.dnspod.com",
        "tencentcloud" => "https://dnspod.tencentcloudapi.com",
        "edgeone" | "edgeone_dns" => "https://teo.tencentcloudapi.com",
        "cloudns" => "https://api.cloudns.net",
        "aliesa" => "https://esa.cn-hangzhou.aliyuncs.com",
        "dnscom" => "https://www.51dns.com",
        "he" => "https://dyn.dns.he.net",
        "huaweidns" => "https://dns.myhuaweicloud.com",
        "namesilo" => "https://www.namesilo.com",
        "noip" => "https://dynupdate.no-ip.com",
        "west" => "https://api.west.cn/API/v2/domain/dns/",
        _ => "",
    }
}

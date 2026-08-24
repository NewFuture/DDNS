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
                "dnspod" | "dnspod_cn" => "https://dnsapi.cn",
                "dnspod_com" | "dnspod_global" => "https://api.dnspod.com",
                "tencentcloud" | "tencent" | "qcloud" => "https://dnspod.tencentcloudapi.com",
                "edgeone" | "edgeone_acc" | "teo_acc" | "teo" | "edgeone_dns" | "teo_dns"
                | "edgeone_noacc" => "https://teo.tencentcloudapi.com",
                "cloudns" => "https://api.cloudns.net",
                "aliesa" | "esa" => "https://esa.cn-hangzhou.aliyuncs.com",
                "dnscom" | "51dns" | "dns_com" => "https://www.51dns.com",
                "he" | "he_net" => "https://dyn.dns.he.net",
                "huaweidns" | "huawei" | "huaweicloud" => "https://dns.myhuaweicloud.com",
                "namesilo" | "namesilo_com" => "https://www.namesilo.com",
                "noip" | "no-ip" | "noip_com" => "https://dynupdate.no-ip.com",
                "west" | "west_cn" | "35cn" => "https://api.west.cn/API/v2/domain/dns/",
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
        "debug" | "print" => Ok(Box::new(debug::DebugProvider)),
        "cloudflare" => Ok(Box::new(cloudflare::CloudflareProvider::new(context)?)),
        "alidns" | "aliyun" => Ok(Box::new(alidns::AlidnsProvider::new(context)?)),
        "dnspod" | "dnspod_cn" => Ok(Box::new(dnspod::DnspodProvider::new(context)?)),
        "dnspod_com" | "dnspod_global" => Ok(Box::new(dnspod::DnspodProvider::global(context)?)),
        "tencentcloud" | "tencent" | "qcloud" => {
            Ok(Box::new(tencentcloud::TencentCloudProvider::new(
                context,
                "tencentcloud",
                "dnspod",
                "2021-03-23",
                false,
            )?))
        }
        "edgeone" | "edgeone_acc" | "teo_acc" | "teo" => {
            Ok(Box::new(tencentcloud::TencentCloudProvider::new(
                context,
                "edgeone",
                "teo",
                "2022-09-01",
                false,
            )?))
        }
        "edgeone_dns" | "teo_dns" | "edgeone_noacc" => {
            Ok(Box::new(tencentcloud::TencentCloudProvider::new(
                context,
                "edgeone_dns",
                "teo",
                "2022-09-01",
                true,
            )?))
        }
        "cloudns" => Ok(Box::new(cloudns::CloudnsProvider::new(context)?)),
        "aliesa" | "esa" => Ok(Box::new(aliesa::AliesaProvider::new(context)?)),
        "dnscom" | "51dns" | "dns_com" => Ok(Box::new(dnscom::DnscomProvider::new(context)?)),
        "he" | "he_net" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::He,
            "he",
        )?)),
        "huaweidns" | "huawei" | "huaweicloud" => {
            Ok(Box::new(huaweidns::HuaweiDnsProvider::new(context)?))
        }
        "namesilo" | "namesilo_com" => Ok(Box::new(namesilo::NamesiloProvider::new(context)?)),
        "noip" | "no-ip" | "noip_com" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::NoIp,
            "noip",
        )?)),
        "callback" | "webhook" | "http" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::Callback,
            "callback",
        )?)),
        "west" | "west_cn" | "35cn" => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::West,
            "west",
        )?)),
        provider => Err(Error::Unsupported(format!(
            "provider `{provider}` is not supported by the Rust MVP"
        ))),
    }
}

pub(crate) fn empty_zone_cache() -> BTreeMap<String, String> {
    BTreeMap::new()
}

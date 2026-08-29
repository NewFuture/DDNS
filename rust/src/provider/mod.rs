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

use std::fmt::{self, Display, Formatter};
use std::str::FromStr;

use crate::config::Config;
use crate::error::{Error, Result};
use crate::http::HttpClient;
use crate::logging::Logger;

pub use base::{Provider, RecordRequest};

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum ProviderId {
    Debug,
    Cloudflare,
    Alidns,
    Dnspod,
    DnspodCom,
    TencentCloud,
    EdgeOne,
    EdgeOneDns,
    Cloudns,
    Aliesa,
    Dnscom,
    He,
    HuaweiDns,
    Namesilo,
    Noip,
    Callback,
    West,
}

impl ProviderId {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Debug => "debug",
            Self::Cloudflare => "cloudflare",
            Self::Alidns => "alidns",
            Self::Dnspod => "dnspod",
            Self::DnspodCom => "dnspod_com",
            Self::TencentCloud => "tencentcloud",
            Self::EdgeOne => "edgeone",
            Self::EdgeOneDns => "edgeone_dns",
            Self::Cloudns => "cloudns",
            Self::Aliesa => "aliesa",
            Self::Dnscom => "dnscom",
            Self::He => "he",
            Self::HuaweiDns => "huaweidns",
            Self::Namesilo => "namesilo",
            Self::Noip => "noip",
            Self::Callback => "callback",
            Self::West => "west",
        }
    }

    const fn default_endpoint(self) -> &'static str {
        match self {
            Self::Debug | Self::Callback => "",
            Self::Cloudflare => "https://api.cloudflare.com",
            Self::Alidns => "https://alidns.aliyuncs.com",
            Self::Dnspod => "https://dnsapi.cn",
            Self::DnspodCom => "https://api.dnspod.com",
            Self::TencentCloud => "https://dnspod.tencentcloudapi.com",
            Self::EdgeOne | Self::EdgeOneDns => "https://teo.tencentcloudapi.com",
            Self::Cloudns => "https://api.cloudns.net",
            Self::Aliesa => "https://esa.cn-hangzhou.aliyuncs.com",
            Self::Dnscom => "https://www.51dns.com",
            Self::He => "https://dyn.dns.he.net",
            Self::HuaweiDns => "https://dns.myhuaweicloud.com",
            Self::Namesilo => "https://www.namesilo.com",
            Self::Noip => "https://dynupdate.no-ip.com",
            Self::West => "https://api.west.cn/API/v2/domain/dns/",
        }
    }
}

impl Display for ProviderId {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}

impl FromStr for ProviderId {
    type Err = Error;

    fn from_str(provider: &str) -> Result<Self> {
        match provider.to_ascii_lowercase().as_str() {
            "debug" | "print" => Ok(Self::Debug),
            "cloudflare" => Ok(Self::Cloudflare),
            "alidns" | "aliyun" => Ok(Self::Alidns),
            "dnspod" | "dnspod_cn" => Ok(Self::Dnspod),
            "dnspod_com" | "dnspod_global" => Ok(Self::DnspodCom),
            "tencentcloud" | "tencent" | "qcloud" => Ok(Self::TencentCloud),
            "edgeone" | "edgeone_acc" | "teo_acc" | "teo" => Ok(Self::EdgeOne),
            "edgeone_dns" | "teo_dns" | "edgeone_noacc" => Ok(Self::EdgeOneDns),
            "cloudns" => Ok(Self::Cloudns),
            "aliesa" | "esa" => Ok(Self::Aliesa),
            "dnscom" | "51dns" | "dns_com" => Ok(Self::Dnscom),
            "he" | "he_net" => Ok(Self::He),
            "huaweidns" | "huawei" | "huaweicloud" => Ok(Self::HuaweiDns),
            "namesilo" | "namesilo_com" => Ok(Self::Namesilo),
            "noip" | "no-ip" | "noip_com" => Ok(Self::Noip),
            "callback" | "webhook" | "http" => Ok(Self::Callback),
            "west" | "west_cn" | "35cn" => Ok(Self::West),
            _ => Err(Error::Unsupported(format!(
                "provider `{provider}` is not supported by the Rust MVP"
            ))),
        }
    }
}

pub fn build<'a>(
    config: &Config,
    client: &'a dyn HttpClient,
    logger: Logger,
) -> Result<Box<dyn Provider + 'a>> {
    let provider = config.provider;
    let context = base::ProviderContext {
        id: config.id.clone(),
        token: config.token.clone(),
        endpoint: config
            .endpoint
            .clone()
            .unwrap_or_else(|| provider.default_endpoint().to_owned()),
        proxies: config.proxies.clone(),
        client,
        logger,
    };
    match provider {
        ProviderId::Debug => Ok(Box::new(debug::DebugProvider)),
        ProviderId::Cloudflare => Ok(Box::new(cloudflare::CloudflareProvider::new(context)?)),
        ProviderId::Alidns => Ok(Box::new(alidns::AlidnsProvider::new(context)?)),
        ProviderId::Dnspod => Ok(Box::new(dnspod::DnspodProvider::new(context)?)),
        ProviderId::DnspodCom => Ok(Box::new(dnspod::DnspodProvider::global(context)?)),
        ProviderId::TencentCloud => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "dnspod",
            "2021-03-23",
            false,
        )?)),
        ProviderId::EdgeOne => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "teo",
            "2022-09-01",
            false,
        )?)),
        ProviderId::EdgeOneDns => Ok(Box::new(tencentcloud::TencentCloudProvider::new(
            context,
            "teo",
            "2022-09-01",
            true,
        )?)),
        ProviderId::Cloudns => Ok(Box::new(cloudns::CloudnsProvider::new(context)?)),
        ProviderId::Aliesa => Ok(Box::new(aliesa::AliesaProvider::new(context)?)),
        ProviderId::Dnscom => Ok(Box::new(dnscom::DnscomProvider::new(context)?)),
        ProviderId::He => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::He,
        )?)),
        ProviderId::HuaweiDns => Ok(Box::new(huaweidns::HuaweiDnsProvider::new(context)?)),
        ProviderId::Namesilo => Ok(Box::new(namesilo::NamesiloProvider::new(context)?)),
        ProviderId::Noip => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::NoIp,
        )?)),
        ProviderId::Callback => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::Callback,
        )?)),
        ProviderId::West => Ok(Box::new(simple::SimpleProvider::new(
            context,
            simple::SimpleKind::West,
        )?)),
    }
}

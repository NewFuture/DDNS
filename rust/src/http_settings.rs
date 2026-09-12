use std::collections::BTreeMap;
use std::net::IpAddr;

use serde_json::{Map, Value};
use ureq::http::uri::Authority;

use crate::error::{Error, Result};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HttpSettings {
    pub host: String,
    pub port: u16,
    pub token: Option<String>,
    pub origins: Vec<String>,
}

impl HttpSettings {
    pub fn resolve(
        cli: &BTreeMap<String, Value>,
        document: &Value,
        environment: &BTreeMap<String, Value>,
    ) -> Result<Self> {
        let mut merged = Map::new();
        for key in ["host", "port", "token", "origins"] {
            if let Some(value) = environment.get(&format!("http_{key}")) {
                merged.insert(key.to_owned(), value.clone());
            }
        }
        if let Some(http) = document.get("http") {
            let http = http
                .as_object()
                .ok_or_else(|| invalid("http must be an object"))?;
            if http.get("origins").is_some_and(|value| !value.is_array()) {
                return Err(invalid("HTTP origins must be an array"));
            }
            merged.extend(http.clone());
        }
        merged.extend(cli.iter().map(|(key, value)| (key.clone(), value.clone())));
        Self::from_value(&Value::Object(merged), true)
    }

    pub fn from_value(value: &Value, enforce_bind_auth: bool) -> Result<Self> {
        let value = value
            .as_object()
            .ok_or_else(|| invalid("http must be an object"))?;
        if value
            .keys()
            .any(|key| !["host", "port", "token", "origins"].contains(&key.as_str()))
        {
            return Err(invalid("Unsupported HTTP setting"));
        }
        let raw_host = match value.get("host") {
            None => "127.0.0.1",
            Some(value) => value
                .as_str()
                .ok_or_else(|| invalid("HTTP host must be a string"))?,
        };
        let raw_host = raw_host.trim();
        let host = if raw_host.starts_with('[') && raw_host.ends_with(']') {
            &raw_host[1..raw_host.len() - 1]
        } else {
            raw_host
        };
        if host.is_empty()
            || !host.is_ascii()
            || host
                .bytes()
                .any(|byte| byte.is_ascii_whitespace() || byte.is_ascii_control())
            || host.contains(['/', '\\', '[', ']', '@', '?', '#'])
            || (host.contains(':') && host.parse::<std::net::Ipv6Addr>().is_err())
        {
            return Err(invalid("HTTP host must be an unambiguous bind address"));
        }
        let port = match value.get("port") {
            None => 9876,
            Some(Value::String(port)) => port
                .parse::<u16>()
                .map_err(|_| invalid("HTTP port must be an integer from 0 to 65535"))?,
            Some(value) => value
                .as_u64()
                .and_then(|port| u16::try_from(port).ok())
                .ok_or_else(|| invalid("HTTP port must be an integer from 0 to 65535"))?,
        };
        let token = match value.get("token") {
            None | Some(Value::Null) => None,
            Some(Value::String(token))
                if !token.is_empty() && token.bytes().all(|byte| (0x21..=0x7e).contains(&byte)) =>
            {
                Some(token.clone())
            }
            _ => {
                return Err(invalid(
                    "HTTP token must contain non-empty visible ASCII characters or be null",
                ));
            }
        };
        if enforce_bind_auth && !is_loopback_host(host) && token.is_none() {
            return Err(invalid(
                "A non-empty HTTP token is required for non-loopback listeners",
            ));
        }
        let entries = match value.get("origins") {
            None => Vec::new(),
            Some(Value::String(value)) => value
                .split([',', ';'])
                .filter(|item| !item.trim().is_empty())
                .map(|item| Value::String(item.trim().to_owned()))
                .collect(),
            Some(Value::Array(values)) => values.clone(),
            _ => return Err(invalid("HTTP origins must be an array")),
        };
        let mut origins = Vec::new();
        for entry in entries {
            let origin = normalize_origin(
                entry
                    .as_str()
                    .ok_or_else(|| invalid("HTTP origins must contain strings"))?,
            )?;
            if !origins.contains(&origin) {
                origins.push(origin);
            }
        }
        Ok(Self {
            host: host.to_owned(),
            port,
            token,
            origins,
        })
    }
}

fn invalid(message: &str) -> Error {
    Error::Config(message.to_owned())
}

pub fn is_loopback_host(host: &str) -> bool {
    let host = host
        .strip_prefix('[')
        .and_then(|host| host.strip_suffix(']'))
        .unwrap_or(host);
    host.eq_ignore_ascii_case("localhost")
        || host
            .parse::<IpAddr>()
            .is_ok_and(|address| address.is_loopback())
}

fn authority(value: &str) -> Result<Authority> {
    if value.is_empty()
        || !value.is_ascii()
        || value.contains(['@', '/', '\\', '?', '#'])
        || value
            .bytes()
            .any(|byte| byte.is_ascii_control() || byte.is_ascii_whitespace())
    {
        return Err(invalid("Invalid HTTP authority"));
    }
    let authority = value
        .parse::<Authority>()
        .map_err(|_| invalid("Invalid HTTP authority"))?;
    let host = authority.host();
    let suffix = value
        .strip_prefix(host)
        .ok_or_else(|| invalid("Invalid HTTP authority"))?;
    if host.is_empty()
        || (!suffix.is_empty()
            && !suffix.strip_prefix(':').is_some_and(|port| {
                !port.is_empty()
                    && port.bytes().all(|byte| byte.is_ascii_digit())
                    && port.parse::<u16>().is_ok()
            }))
    {
        return Err(invalid("Invalid HTTP authority"));
    }
    Ok(authority)
}

pub fn host_header_is_loopback(host: &str) -> bool {
    authority(host).is_ok_and(|authority| is_loopback_host(authority.host()))
}

pub fn normalize_origin(origin: &str) -> Result<String> {
    let origin = origin.trim();
    if origin
        .bytes()
        .any(|byte| byte.is_ascii_whitespace() || byte.is_ascii_control())
        || origin.contains(['?', '#', '\\'])
    {
        return Err(invalid("HTTP origin must be an exact http(s) origin"));
    }
    let (scheme, host) = origin
        .split_once("://")
        .ok_or_else(|| invalid("HTTP origin must be an exact http(s) origin"))?;
    let scheme = scheme.to_ascii_lowercase();
    if scheme != "http" && scheme != "https" {
        return Err(invalid("HTTP origin must be an exact http(s) origin"));
    }
    let host = host.strip_suffix('/').unwrap_or(host);
    let authority = authority(host)?;
    let port = authority.port_u16();
    let default_port = if scheme == "http" { 80 } else { 443 };
    let suffix = port
        .filter(|port| *port != default_port)
        .map(|port| format!(":{port}"))
        .unwrap_or_default();
    Ok(format!(
        "{scheme}://{}{suffix}",
        authority.host().to_ascii_lowercase()
    ))
}

pub fn token_matches(supplied: Option<&str>, expected: Option<&str>) -> bool {
    let Some(expected) = expected else {
        return true;
    };
    let Some(supplied) = supplied else {
        return false;
    };
    let mut difference = supplied.len() ^ expected.len();
    for index in 0..supplied.len().max(expected.len()) {
        difference |= usize::from(
            supplied.as_bytes().get(index).copied().unwrap_or_default()
                ^ expected.as_bytes().get(index).copied().unwrap_or_default(),
        );
    }
    difference == 0
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn rejects_unsafe_and_ambiguous_listener_settings() {
        for value in [
            json!({"host":"0.0.0.0"}),
            json!({"host":"[127.0.0.1"}),
            json!({"host":"127.0.0.1:80"}),
            json!({"port":true}),
            json!({"port":1.5}),
            json!({"port":65536}),
            json!({"token":""}),
            json!({"token":"a b"}),
            json!({"token":"secret\n"}),
            json!({"token":42}),
            json!({"origins":["*"]}),
        ] {
            assert!(HttpSettings::from_value(&value, true).is_err(), "{value}");
        }
        assert!(HttpSettings::from_value(&json!({"host":"0.0.0.0","token":"x"}), true).is_ok());
        assert!(HttpSettings::from_value(&json!({"host":"::1","port":0}), true).is_ok());
    }

    #[test]
    fn resolves_sparse_settings_in_priority_order() {
        let environment = BTreeMap::from([
            ("http_host".to_owned(), json!("0.0.0.0")),
            ("http_token".to_owned(), json!("env-token")),
            ("http_port".to_owned(), json!("1234")),
        ]);
        let settings = HttpSettings::resolve(
            &BTreeMap::from([("port".to_owned(), json!(0))]),
            &json!({"http":{"host":"127.0.0.1"}}),
            &environment,
        )
        .unwrap();
        assert_eq!(settings.host, "127.0.0.1");
        assert_eq!(settings.port, 0);
        assert_eq!(settings.token.as_deref(), Some("env-token"));
        assert!(
            HttpSettings::resolve(&BTreeMap::new(), &json!({"http":null}), &environment).is_err()
        );
    }

    #[test]
    fn validates_origins_and_loopback_hosts_without_dns_resolution() {
        assert_eq!(
            normalize_origin("HTTPS://CLIENT.example:443/").unwrap(),
            "https://client.example"
        );
        assert_eq!(
            normalize_origin("http://[::1]:123/").unwrap(),
            "http://[::1]:123"
        );
        for origin in [
            "http://a/path",
            "http://user@a",
            "http://a?",
            "http://a#",
            "http://a:99999",
            "http://a\\b",
            "http://a//",
        ] {
            assert!(normalize_origin(origin).is_err(), "{origin}");
        }
        for host in ["localhost:9876", "127.0.0.2", "[::1]:9876"] {
            assert!(host_header_is_loopback(host), "{host}");
        }
        for host in [
            "127.0.0.1.evil",
            "127.0.0.1@evil",
            "127.0.0.1/path",
            "127.0.0.1:99999",
            "127.1",
            "2130706433",
            "evil",
        ] {
            assert!(!host_header_is_loopback(host), "{host}");
        }
    }

    #[test]
    fn checks_full_tokens() {
        assert!(token_matches(None, None));
        assert!(!token_matches(None, Some("secret")));
        assert!(!token_matches(Some("secre"), Some("secret")));
        assert!(!token_matches(Some("Secret"), Some("secret")));
        assert!(token_matches(Some("secret"), Some("secret")));
    }
}

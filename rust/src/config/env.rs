use std::collections::BTreeMap;
use std::ffi::OsString;

use serde_json::Value;

use super::legacy;

pub fn load() -> BTreeMap<String, Value> {
    load_from_os(std::env::vars_os())
}

pub fn load_from<I>(variables: I) -> BTreeMap<String, Value>
where
    I: IntoIterator<Item = (String, String)>,
{
    load_from_os(
        variables
            .into_iter()
            .map(|(name, value)| (OsString::from(name), OsString::from(value))),
    )
}

fn load_from_os<I>(variables: I) -> BTreeMap<String, Value>
where
    I: IntoIterator<Item = (OsString, OsString)>,
{
    let mut values = BTreeMap::new();
    for (name, raw_value) in variables {
        let Some(name) = name.to_str() else {
            continue;
        };
        let lower = name.to_ascii_lowercase();
        let key = if lower == "pythonhttpsverify" {
            if values.contains_key("ssl") {
                continue;
            }
            "ssl".to_owned()
        } else if let Some(key) = lower.strip_prefix("ddns_") {
            key.replace('.', "_")
        } else {
            continue;
        };
        let Some(raw_value) = raw_value.to_str() else {
            continue;
        };
        values.insert(key, parse_value(raw_value));
    }
    values
}

fn parse_value(raw: &str) -> Value {
    let trimmed = raw.trim();
    if trimmed.starts_with('[')
        && trimmed.ends_with(']')
        && let Ok(value) = legacy::parse(trimmed)
    {
        return value;
    }
    Value::String(trimmed.to_owned())
}

#[cfg(test)]
mod tests {
    use super::load_from;
    #[cfg(unix)]
    use super::load_from_os;

    #[test]
    fn loads_ddns_values_and_python_arrays() {
        let values = load_from([
            ("DDNS_DNS".to_owned(), "cloudflare".to_owned()),
            (
                "DDNS_IPV4".to_owned(),
                "['a.example.com', 'b.example.com']".to_owned(),
            ),
            ("IGNORED".to_owned(), "value".to_owned()),
        ]);
        assert_eq!(values["dns"], "cloudflare");
        assert_eq!(
            values["ipv4"],
            serde_json::json!(["a.example.com", "b.example.com"])
        );
        assert!(!values.contains_key("ignored"));
    }

    #[cfg(unix)]
    #[test]
    fn ignores_non_unicode_environment_entries() {
        use std::os::unix::ffi::OsStringExt;

        let values = load_from_os([
            (
                std::ffi::OsString::from_vec(b"UNRELATED_\xff".to_vec()),
                std::ffi::OsString::from("ignored"),
            ),
            (
                std::ffi::OsString::from("UNRELATED"),
                std::ffi::OsString::from_vec(b"\xff".to_vec()),
            ),
            (
                std::ffi::OsString::from("DDNS_TOKEN"),
                std::ffi::OsString::from_vec(b"\xff".to_vec()),
            ),
            (
                std::ffi::OsString::from("DDNS_DNS"),
                std::ffi::OsString::from("debug"),
            ),
        ]);
        assert_eq!(values.get("dns"), Some(&serde_json::json!("debug")));
        assert!(!values.contains_key("token"));
    }
}

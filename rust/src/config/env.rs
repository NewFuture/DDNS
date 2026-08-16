use std::collections::BTreeMap;

use serde_json::Value;

use super::legacy;

pub fn load() -> BTreeMap<String, Value> {
    load_from(std::env::vars())
}

pub fn load_from<I>(variables: I) -> BTreeMap<String, Value>
where
    I: IntoIterator<Item = (String, String)>,
{
    let mut values = BTreeMap::new();
    for (name, raw_value) in variables {
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
        values.insert(key, parse_value(&raw_value));
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
}

use std::collections::BTreeMap;

use serde_json::Value;

use crate::error::{Error, Result};

pub fn expand_document(document: Value) -> Result<Vec<BTreeMap<String, Value>>> {
    match document {
        Value::Object(object) => expand_object(object.into_iter().collect()),
        Value::Array(items) => {
            let mut result = Vec::new();
            for item in items {
                let Value::Object(object) = item else {
                    return Err(Error::Config(
                        "root configuration arrays must contain objects".to_owned(),
                    ));
                };
                result.extend(expand_object(object.into_iter().collect())?);
            }
            Ok(result)
        }
        _ => Err(Error::Config(
            "configuration root must be an object or array".to_owned(),
        )),
    }
}

fn expand_object(mut object: BTreeMap<String, Value>) -> Result<Vec<BTreeMap<String, Value>>> {
    let Some(providers) = object.remove("providers") else {
        return Ok(vec![flatten(object)]);
    };
    if object.contains_key("dns") {
        return Err(Error::Config(
            "`providers` and `dns` cannot be used together".to_owned(),
        ));
    }
    if object.contains_key("ipv4") || object.contains_key("ipv6") {
        return Err(Error::Config(
            "global `ipv4` and `ipv6` are not allowed with `providers`".to_owned(),
        ));
    }
    let Value::Array(providers) = providers else {
        return Err(Error::Config("`providers` must be an array".to_owned()));
    };
    let global = flatten(object);
    let mut result = Vec::with_capacity(providers.len());
    for (index, provider) in providers.into_iter().enumerate() {
        let Value::Object(provider) = provider else {
            return Err(Error::Config(format!(
                "providers[{index}] must be an object"
            )));
        };
        let mut provider = provider.into_iter().collect::<BTreeMap<_, _>>();
        let name = provider
            .remove("provider")
            .and_then(|value| value.as_str().map(ToOwned::to_owned))
            .ok_or_else(|| {
                Error::Config(format!("providers[{index}].provider must be a string"))
            })?;
        let mut expanded = global.clone();
        expanded.extend(flatten(provider));
        expanded.insert("dns".to_owned(), Value::String(name));
        result.push(expanded);
    }
    Ok(result)
}

fn flatten(object: BTreeMap<String, Value>) -> BTreeMap<String, Value> {
    let mut flattened = BTreeMap::new();
    for (key, value) in object {
        if key == "http" {
            continue;
        }
        if matches!(key.as_str(), "extra" | "token") {
            flattened.insert(key, value);
        } else if let Value::Object(nested) = value {
            for (nested_key, nested_value) in nested {
                flattened.insert(format!("{key}_{nested_key}"), nested_value);
            }
        } else {
            flattened.insert(key, value);
        }
    }
    flattened
}

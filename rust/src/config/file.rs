use std::fs;
use std::path::{Path, PathBuf};

use serde_json::Value;

use crate::error::{Error, Result};
use crate::http::redact_url;

use super::legacy;

pub const DEFAULT_CONFIG_PATHS: &[&str] = &[
    "config.json",
    "~/.ddns/config.json",
    "~/.ddns.json",
    "/etc/ddns/config.json",
    "/etc/ddns.json",
];

pub fn load(path: &str, fetch: &dyn Fn(&str) -> Result<String>) -> Result<Value> {
    let display_path = redact_url(path);
    let content = if path.contains("://") {
        fetch(path)?
    } else {
        fs::read_to_string(expand_home(path)).map_err(|error| {
            Error::Config(format!(
                "failed to read configuration `{display_path}`: {error}"
            ))
        })?
    };
    parse(&content).map_err(|error| {
        Error::Config(format!(
            "failed to parse configuration `{display_path}`: {error}"
        ))
    })
}

pub fn parse(content: &str) -> Result<Value> {
    let without_comments = remove_comments(content);
    match serde_json::from_str(&without_comments) {
        Ok(value) => Ok(value),
        Err(json_error) => legacy::parse(&without_comments).map_err(|legacy_error| {
            Error::Config(format!(
                "JSON parser: {json_error}; Python literal parser: {legacy_error}"
            ))
        }),
    }
}

pub fn existing_default() -> Option<String> {
    DEFAULT_CONFIG_PATHS.iter().find_map(|path| {
        let expanded = expand_home(path);
        expanded.is_file().then(|| expanded.display().to_string())
    })
}

pub fn expand_home(path: &str) -> PathBuf {
    if path == "~" || path.starts_with("~/") || path.starts_with("~\\") {
        let home = std::env::var_os("HOME").or_else(|| std::env::var_os("USERPROFILE"));
        if let Some(home) = home {
            let suffix = path.trim_start_matches('~').trim_start_matches(['/', '\\']);
            return Path::new(&home).join(suffix);
        }
    }
    PathBuf::from(path)
}

pub fn remove_comments(content: &str) -> String {
    let mut output = String::with_capacity(content.len());
    let mut characters = content.chars().peekable();
    let mut quote = None;
    let mut escaped = false;

    while let Some(character) = characters.next() {
        if let Some(active_quote) = quote {
            output.push(character);
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == active_quote {
                quote = None;
            }
            continue;
        }

        if matches!(character, '"' | '\'') {
            quote = Some(character);
            output.push(character);
            continue;
        }

        let line_comment =
            character == '#' || (character == '/' && characters.peek().copied() == Some('/'));
        if line_comment {
            if character == '/' {
                characters.next();
            }
            let mut ended_with_newline = false;
            for comment_character in characters.by_ref() {
                if comment_character == '\n' {
                    ended_with_newline = true;
                    break;
                }
            }
            while output.ends_with(' ') || output.ends_with('\t') {
                output.pop();
            }
            if ended_with_newline {
                output.push('\n');
            }
            continue;
        }
        output.push(character);
    }
    output
}

#[cfg(test)]
mod tests {
    use super::{parse, remove_comments};

    #[test]
    fn preserves_comment_markers_inside_strings() {
        let content = r#"{"url":"https://example.com/#value"} // comment
"#;
        assert_eq!(
            remove_comments(content),
            "{\"url\":\"https://example.com/#value\"}\n"
        );
    }

    #[test]
    fn parses_jsonc_and_python_literals() {
        assert_eq!(
            parse("{'dns': 'alidns', 'enabled': True,} // legacy").unwrap(),
            serde_json::json!({"dns": "alidns", "enabled": true})
        );
    }
}

use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::{cmp::Ordering, fmt};

use time::OffsetDateTime;
use time::format_description::well_known::Rfc3339;

use crate::error::{Error, Result};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Level {
    NotSet,
    Debug,
    Info,
    Warning,
    Error,
    Critical,
    Custom(i32),
}

impl Level {
    pub fn parse(value: &str) -> Result<Self> {
        match value.to_ascii_uppercase().as_str() {
            "NOTSET" => Ok(Self::NotSet),
            "DEBUG" => Ok(Self::Debug),
            "INFO" => Ok(Self::Info),
            "WARNING" | "WARN" => Ok(Self::Warning),
            "ERROR" => Ok(Self::Error),
            "CRITICAL" | "FATAL" => Ok(Self::Critical),
            _ => value
                .parse::<i32>()
                .map(Self::from_value)
                .map_err(|_| Error::Config(format!("invalid log level: {value}"))),
        }
    }

    const fn from_value(value: i32) -> Self {
        match value {
            0 => Self::NotSet,
            10 => Self::Debug,
            20 => Self::Info,
            30 => Self::Warning,
            40 => Self::Error,
            50 => Self::Critical,
            value => Self::Custom(value),
        }
    }

    const fn value(self) -> i32 {
        match self {
            Self::NotSet => 0,
            Self::Debug => 10,
            Self::Info => 20,
            Self::Warning => 30,
            Self::Error => 40,
            Self::Critical => 50,
            Self::Custom(value) => value,
        }
    }
}

impl Ord for Level {
    fn cmp(&self, other: &Self) -> Ordering {
        self.value().cmp(&other.value())
    }
}

impl PartialOrd for Level {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl fmt::Display for Level {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotSet => formatter.write_str("NOTSET"),
            Self::Debug => formatter.write_str("DEBUG"),
            Self::Info => formatter.write_str("INFO"),
            Self::Warning => formatter.write_str("WARNING"),
            Self::Error => formatter.write_str("ERROR"),
            Self::Critical => formatter.write_str("CRITICAL"),
            Self::Custom(value) => value.fmt(formatter),
        }
    }
}

enum Destination {
    Stderr,
    File(File),
}

#[derive(Clone)]
pub struct Logger {
    level: Level,
    destination: Arc<Mutex<Destination>>,
    secrets: Arc<Vec<String>>,
}

impl Logger {
    pub fn new(level: Level, file: Option<&Path>, secrets: Vec<String>) -> Result<Self> {
        let destination = if let Some(path) = file {
            if let Some(parent) = path
                .parent()
                .filter(|parent| !parent.as_os_str().is_empty())
            {
                std::fs::create_dir_all(parent)?;
            }
            Destination::File(OpenOptions::new().create(true).append(true).open(path)?)
        } else {
            Destination::Stderr
        };
        Ok(Self {
            level,
            destination: Arc::new(Mutex::new(destination)),
            secrets: Arc::new(normalize_secrets(secrets)),
        })
    }

    pub fn with_secrets(&self, secrets: Vec<String>) -> Self {
        Self {
            level: self.level,
            destination: Arc::clone(&self.destination),
            secrets: Arc::new(normalize_secrets(secrets)),
        }
    }

    pub fn debug(&self, target: &str, message: impl AsRef<str>) {
        self.write(Level::Debug, target, message.as_ref());
    }

    pub fn info(&self, target: &str, message: impl AsRef<str>) {
        self.write(Level::Info, target, message.as_ref());
    }

    pub fn warning(&self, target: &str, message: impl AsRef<str>) {
        self.write(Level::Warning, target, message.as_ref());
    }

    pub fn error(&self, target: &str, message: impl AsRef<str>) {
        self.write(Level::Error, target, message.as_ref());
    }

    pub fn critical(&self, target: &str, message: impl AsRef<str>) {
        self.write(Level::Critical, target, message.as_ref());
    }

    pub fn mask(&self, value: &str) -> String {
        self.secrets
            .iter()
            .fold(value.to_owned(), |masked, secret| {
                let replacement = if secret.chars().count() > 4 {
                    let first = secret.chars().take(2).collect::<String>();
                    let last = secret
                        .chars()
                        .rev()
                        .take(2)
                        .collect::<String>()
                        .chars()
                        .rev()
                        .collect::<String>();
                    format!("{first}***{last}")
                } else {
                    "***".to_owned()
                };
                let encoded = crate::http::percent_encode(secret);
                masked
                    .replace(secret, &replacement)
                    .replace(&encoded, &replacement)
            })
    }

    fn write(&self, level: Level, target: &str, message: &str) {
        if level < self.level {
            return;
        }
        let timestamp = OffsetDateTime::now_utc()
            .format(&Rfc3339)
            .unwrap_or_else(|_| "unknown-time".to_owned());
        let line = format!("{timestamp} {} [{target}]: {}\n", level, self.mask(message));
        let Ok(mut destination) = self.destination.lock() else {
            let _ = io::stderr().write_all(line.as_bytes());
            return;
        };
        match &mut *destination {
            Destination::Stderr => {
                let _ = io::stderr().write_all(line.as_bytes());
            }
            Destination::File(file) => {
                if let Err(error) = file.write_all(line.as_bytes()).and_then(|()| file.flush()) {
                    let _ = writeln!(io::stderr(), "ddns-rs: failed to write log: {error}");
                }
            }
        }
    }
}

fn normalize_secrets(secrets: Vec<String>) -> Vec<String> {
    let mut secrets = secrets
        .into_iter()
        .filter(|secret| !secret.is_empty())
        .collect::<Vec<_>>();
    secrets.sort_by(|left, right| right.len().cmp(&left.len()).then_with(|| left.cmp(right)));
    secrets.dedup();
    secrets
}

#[cfg(test)]
mod tests {
    use super::{Level, Logger};

    #[test]
    fn parses_python_compatible_log_levels() {
        assert_eq!(Level::parse("NOTSET").unwrap(), Level::NotSet);
        assert_eq!(Level::parse("FATAL").unwrap(), Level::Critical);
        assert_eq!(Level::parse("10").unwrap(), Level::Debug);
        assert_eq!(Level::parse("25").unwrap(), Level::Custom(25));
        assert!(Level::Info < Level::Custom(25));
        assert!(Level::Warning > Level::Custom(25));
    }

    #[test]
    fn masks_raw_and_percent_encoded_secrets() {
        let path =
            std::env::temp_dir().join(format!("ddns-rs-log-test-{}.log", std::process::id()));
        let _ = std::fs::remove_file(&path);
        {
            let logger = Logger::new(
                Level::Debug,
                Some(&path),
                vec!["account-id".to_owned(), "secret/token".to_owned()],
            )
            .unwrap();
            logger.error(
                "test",
                "id=account-id raw=secret/token encoded=secret%2Ftoken",
            );
        }
        let content = std::fs::read_to_string(&path).unwrap();
        assert!(!content.contains("account-id"));
        assert!(!content.contains("secret/token"));
        assert!(!content.contains("secret%2Ftoken"));
        assert!(content.contains("se***en"));
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn masks_overlapping_credentials_longest_first() {
        let logger = Logger::new(
            Level::Debug,
            None,
            vec![
                "account-id".to_owned(),
                "account-id-secret/token".to_owned(),
            ],
        )
        .unwrap();
        let masked = logger.mask("account-id-secret/token account-id");
        assert!(!masked.contains("secret/token"));
        assert!(!masked.contains("account-id"));
    }
}

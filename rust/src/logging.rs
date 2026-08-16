use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::path::Path;
use std::sync::{Arc, Mutex};

use time::OffsetDateTime;
use time::format_description::well_known::Rfc3339;

use crate::error::{Error, Result};

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum Level {
    Debug,
    Info,
    Warning,
    Error,
    Critical,
}

impl Level {
    pub fn parse(value: &str) -> Result<Self> {
        match value.to_ascii_uppercase().as_str() {
            "DEBUG" => Ok(Self::Debug),
            "INFO" => Ok(Self::Info),
            "WARNING" | "WARN" => Ok(Self::Warning),
            "ERROR" => Ok(Self::Error),
            "CRITICAL" => Ok(Self::Critical),
            _ => Err(Error::Config(format!("invalid log level: {value}"))),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Debug => "DEBUG",
            Self::Info => "INFO",
            Self::Warning => "WARNING",
            Self::Error => "ERROR",
            Self::Critical => "CRITICAL",
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
            secrets: Arc::new(
                secrets
                    .into_iter()
                    .filter(|secret| !secret.is_empty())
                    .collect(),
            ),
        })
    }

    pub fn with_secrets(&self, secrets: Vec<String>) -> Self {
        Self {
            level: self.level,
            destination: Arc::clone(&self.destination),
            secrets: Arc::new(
                secrets
                    .into_iter()
                    .filter(|secret| !secret.is_empty())
                    .collect(),
            ),
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
        let line = format!(
            "{timestamp} {} [{target}]: {}\n",
            level.as_str(),
            self.mask(message)
        );
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

#[cfg(test)]
mod tests {
    use super::{Level, Logger};

    #[test]
    fn masks_raw_and_percent_encoded_secrets() {
        let path =
            std::env::temp_dir().join(format!("ddns-rs-log-test-{}.log", std::process::id()));
        let _ = std::fs::remove_file(&path);
        {
            let logger =
                Logger::new(Level::Debug, Some(&path), vec!["secret/token".to_owned()]).unwrap();
            logger.error("test", "raw=secret/token encoded=secret%2Ftoken");
        }
        let content = std::fs::read_to_string(&path).unwrap();
        assert!(!content.contains("secret/token"));
        assert!(!content.contains("secret%2Ftoken"));
        assert!(content.contains("se***en"));
        let _ = std::fs::remove_file(path);
    }
}

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::config::CacheSetting;
use crate::error::{Error, Result};
use crate::logging::Logger;
use crate::signature::sha256_hex;

const CACHE_VERSION: u32 = 1;

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CacheEntry {
    address: String,
    updated_at: u64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CacheFile {
    version: u32,
    records: BTreeMap<String, CacheEntry>,
}

pub struct Cache {
    path: Option<PathBuf>,
    records: BTreeMap<String, CacheEntry>,
    changed: bool,
    logger: Logger,
}

impl Cache {
    pub fn open(
        setting: &CacheSetting,
        identity: &Value,
        max_age: u64,
        logger: Logger,
    ) -> Result<Self> {
        let path = match setting {
            CacheSetting::Disabled => None,
            CacheSetting::Default => {
                let serialized = serde_json::to_vec(identity)?;
                Some(std::env::temp_dir().join(format!("ddns-rs.{}.cache", sha256_hex(serialized))))
            }
            CacheSetting::Path(path) => Some(path.clone()),
        };
        let mut cache = Self {
            path,
            records: BTreeMap::new(),
            changed: false,
            logger,
        };
        cache.load(max_age)?;
        Ok(cache)
    }

    pub fn disabled(logger: Logger) -> Self {
        Self {
            path: None,
            records: BTreeMap::new(),
            changed: false,
            logger,
        }
    }

    pub fn get(&self, provider: &str, domain: &str, record_type: &str) -> Option<&str> {
        self.records
            .get(&cache_key(provider, domain, record_type))
            .map(|entry| entry.address.as_str())
    }

    pub fn set(&mut self, provider: &str, domain: &str, record_type: &str, address: &str) {
        let key = cache_key(provider, domain, record_type);
        if self
            .records
            .get(&key)
            .is_some_and(|entry| entry.address == address)
        {
            return;
        }
        self.records.insert(
            key,
            CacheEntry {
                address: address.to_owned(),
                updated_at: unix_time(),
            },
        );
        self.changed = true;
    }

    pub fn sync(&mut self) -> Result<()> {
        let Some(path) = &self.path else {
            return Ok(());
        };
        if !self.changed {
            return Ok(());
        }
        if let Some(parent) = path
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        {
            fs::create_dir_all(parent)?;
        }
        let serialized = serde_json::to_vec(&CacheFile {
            version: CACHE_VERSION,
            records: self.records.clone(),
        })?;
        let temporary = temporary_path(path);
        fs::write(&temporary, serialized)?;
        if let Err(error) = fs::rename(&temporary, path) {
            if path.exists() {
                fs::remove_file(path)?;
                fs::rename(&temporary, path)?;
            } else {
                return Err(error.into());
            }
        }
        self.changed = false;
        self.logger
            .debug("cache", format!("saved cache to {}", path.display()));
        Ok(())
    }

    fn load(&mut self, max_age: u64) -> Result<()> {
        let Some(path) = &self.path else {
            self.logger.debug("cache", "cache is disabled");
            return Ok(());
        };
        if !path.exists() {
            return Ok(());
        }
        let modified = fs::metadata(path)?.modified()?;
        let now = SystemTime::now();
        let stale = modified > now
            || now
                .duration_since(modified)
                .map_or(true, |age| age.as_secs() >= max_age);
        if stale {
            self.logger
                .info("cache", format!("cache {} is stale", path.display()));
            self.changed = true;
            return Ok(());
        }
        let content = match fs::read(path) {
            Ok(content) => content,
            Err(error) => {
                return Err(Error::Cache(format!(
                    "failed to read cache `{}`: {error}",
                    path.display()
                )));
            }
        };
        match serde_json::from_slice::<CacheFile>(&content) {
            Ok(file) if file.version == CACHE_VERSION => self.records = file.records,
            Ok(file) => {
                self.logger.warning(
                    "cache",
                    format!(
                        "ignoring unsupported cache version {} in {}",
                        file.version,
                        path.display()
                    ),
                );
                self.changed = true;
            }
            Err(error) => {
                self.logger.warning(
                    "cache",
                    format!("ignoring damaged cache {}: {error}", path.display()),
                );
                self.changed = true;
            }
        }
        Ok(())
    }
}

fn cache_key(provider: &str, domain: &str, record_type: &str) -> String {
    format!(
        "{}:{}:{}",
        provider.to_ascii_lowercase(),
        domain.to_ascii_lowercase(),
        record_type.to_ascii_uppercase()
    )
}

fn unix_time() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |duration| duration.as_secs())
}

fn temporary_path(path: &Path) -> PathBuf {
    let mut name = path
        .file_name()
        .map_or_else(|| "cache".into(), |name| name.to_os_string());
    name.push(format!(".{}.tmp", std::process::id()));
    path.with_file_name(name)
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use crate::config::CacheSetting;
    use crate::logging::{Level, Logger};

    use super::Cache;

    #[test]
    fn stores_only_successful_record_values() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let path = std::env::temp_dir().join(format!(
            "ddns-rs-cache-test-{}-{}.json",
            std::process::id(),
            super::unix_time()
        ));
        let mut cache = Cache::open(
            &CacheSetting::Path(path.clone()),
            &serde_json::json!({"test": true}),
            3600,
            logger.clone(),
        )
        .unwrap();
        cache.set("debug", "example.com", "A", "192.0.2.1");
        cache.sync().unwrap();

        let cache = Cache::open(
            &CacheSetting::Path(path.clone()),
            &serde_json::json!({"test": true}),
            3600,
            logger,
        )
        .unwrap();
        assert_eq!(cache.get("debug", "example.com", "A"), Some("192.0.2.1"));
        let _ = std::fs::remove_file(path);
    }
}

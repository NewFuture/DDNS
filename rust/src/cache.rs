use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::config::CacheSetting;
use crate::error::{Error, Result};
use crate::logging::Logger;
use crate::provider::ProviderId;
use crate::signature::sha256_hex;

const CACHE_VERSION: u32 = 3;
type CacheRecords = BTreeMap<String, String>;

#[derive(Deserialize, Serialize)]
struct CacheFile<T = CacheRecords> {
    version: u32,
    records: T,
}

pub struct Cache {
    path: PathBuf,
    namespace: String,
    records: CacheRecords,
    changed: bool,
    logger: Logger,
}

impl Cache {
    pub fn open(
        setting: &CacheSetting,
        identity: &Value,
        max_age: u64,
        logger: Logger,
    ) -> Result<Option<Self>> {
        let namespace = sha256_hex(serde_json::to_vec(identity)?);
        let path = match setting {
            CacheSetting::Disabled => {
                logger.debug("cache", "cache is disabled");
                return Ok(None);
            }
            CacheSetting::Default => {
                std::env::temp_dir().join(format!("ddns-rs.{namespace}.cache"))
            }
            CacheSetting::Path(path) => rust_cache_path(path),
        };
        let mut cache = Self {
            path,
            namespace,
            records: BTreeMap::new(),
            changed: false,
            logger,
        };
        cache.load(max_age)?;
        Ok(Some(cache))
    }

    pub fn get(&self, provider: ProviderId, domain: &str, record_type: &str) -> Option<&str> {
        self.records
            .get(&cache_key(&self.namespace, provider, domain, record_type))
            .map(String::as_str)
    }

    pub fn set(&mut self, provider: ProviderId, domain: &str, record_type: &str, address: &str) {
        let key = cache_key(&self.namespace, provider, domain, record_type);
        if self
            .records
            .get(&key)
            .is_some_and(|cached| cached == address)
        {
            return;
        }
        self.records.insert(key, address.to_owned());
        self.changed = true;
    }

    pub fn sync(&mut self) -> Result<()> {
        if !self.changed {
            return Ok(());
        }
        let path = &self.path;
        if let Some(parent) = path
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        {
            fs::create_dir_all(parent)?;
        }
        let serialized = serde_json::to_vec(&CacheFile {
            version: CACHE_VERSION,
            records: &self.records,
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
        let path = &self.path;
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

fn cache_key(namespace: &str, provider: ProviderId, domain: &str, record_type: &str) -> String {
    format!(
        "{}:{}:{}:{}",
        namespace,
        provider.as_str(),
        domain.to_ascii_lowercase(),
        record_type.to_ascii_uppercase()
    )
}

fn temporary_path(path: &Path) -> PathBuf {
    let mut name = path
        .file_name()
        .map_or_else(|| "cache".into(), |name| name.to_os_string());
    name.push(format!(".{}.tmp", std::process::id()));
    path.with_file_name(name)
}

fn rust_cache_path(path: &Path) -> PathBuf {
    let mut name = path
        .file_name()
        .map_or_else(|| "cache".into(), |name| name.to_os_string());
    name.push(".ddns-rs");
    path.with_file_name(name)
}

#[cfg(test)]
mod tests {
    use std::path::Path;
    use std::time::{SystemTime, UNIX_EPOCH};

    use crate::config::CacheSetting;
    use crate::logging::{Level, Logger};
    use crate::provider::ProviderId;

    use super::{Cache, rust_cache_path};

    fn unique_path(name: &str) -> std::path::PathBuf {
        let suffix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("{name}-{}-{suffix}.json", std::process::id()))
    }

    #[test]
    fn stores_only_successful_record_values() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let path = unique_path("ddns-rs-cache-test");
        let mut cache = Cache::open(
            &CacheSetting::Path(path.clone()),
            &serde_json::json!({"test": true}),
            3600,
            logger.clone(),
        )
        .unwrap()
        .unwrap();
        cache.set(ProviderId::Debug, "example.com", "A", "192.0.2.1");
        cache.sync().unwrap();

        let cache = Cache::open(
            &CacheSetting::Path(path.clone()),
            &serde_json::json!({"test": true}),
            3600,
            logger,
        )
        .unwrap()
        .unwrap();
        assert_eq!(
            cache.get(ProviderId::Debug, "example.com", "A"),
            Some("192.0.2.1")
        );
        let _ = std::fs::remove_file(rust_cache_path(&path));
    }

    #[test]
    fn namespaces_shared_custom_cache_by_configuration_identity() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let path = unique_path("ddns-rs-shared-cache-test");
        let setting = CacheSetting::Path(path.clone());

        let mut first = Cache::open(
            &setting,
            &serde_json::json!({"account": "first", "line": "default"}),
            3600,
            logger.clone(),
        )
        .unwrap()
        .unwrap();
        first.set(ProviderId::Dnspod, "example.com", "A", "192.0.2.10");
        first.sync().unwrap();

        let mut second = Cache::open(
            &setting,
            &serde_json::json!({"account": "second", "line": "telecom"}),
            3600,
            logger.clone(),
        )
        .unwrap()
        .unwrap();
        assert_eq!(second.get(ProviderId::Dnspod, "example.com", "A"), None);
        second.set(ProviderId::Dnspod, "example.com", "A", "192.0.2.10");
        second.sync().unwrap();

        let first = Cache::open(
            &setting,
            &serde_json::json!({"account": "first", "line": "default"}),
            3600,
            logger,
        )
        .unwrap()
        .unwrap();
        assert_eq!(
            first.get(ProviderId::Dnspod, "example.com", "A"),
            Some("192.0.2.10")
        );
        let _ = std::fs::remove_file(rust_cache_path(&path));
    }

    #[test]
    fn preserves_python_cache_at_shared_custom_path() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let path = unique_path("ddns-python-cache-test").with_extension("json.ddns-rs");
        let python_content = r#"{"example.com:A":"192.0.2.1"}"#;
        std::fs::write(&path, python_content).unwrap();

        let mut cache = Cache::open(
            &CacheSetting::Path(path.clone()),
            &serde_json::json!({"client": "rust"}),
            3600,
            logger,
        )
        .unwrap()
        .unwrap();
        cache.set(ProviderId::Debug, "example.com", "A", "192.0.2.2");
        cache.sync().unwrap();

        assert_eq!(std::fs::read_to_string(&path).unwrap(), python_content);
        assert!(rust_cache_path(&path).is_file());
        let _ = std::fs::remove_file(&path);
        let _ = std::fs::remove_file(rust_cache_path(&path));
    }
}

mod scheduler;
mod storage;
mod validation;

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::{SystemTime, UNIX_EPOCH};

use serde_json::{Value, json};

use crate::cache::Cache;
use crate::config::{self, Config};
use crate::logging::{Level, Logger};
use crate::signature::sha256_hex;
use crate::update;

use scheduler::Schedule;
pub use scheduler::SchedulerHandle;
use validation::{MODEL, invalid};

#[derive(Debug, Clone)]
pub struct DashboardError {
    pub status: u16,
    pub code: &'static str,
    pub message: String,
}
impl fmt::Display for DashboardError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.message)
    }
}
impl std::error::Error for DashboardError {}
pub type Result<T> = std::result::Result<T, DashboardError>;

pub(super) fn operation_error(_error: impl fmt::Display) -> DashboardError {
    // Paths, parser errors, and provider errors can contain credentials.
    DashboardError {
        status: 500,
        code: "operation_failed",
        message: "The dashboard operation could not be completed.".to_owned(),
    }
}

pub(super) fn now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}

#[derive(Default)]
struct State {
    identity: String,
    last_sync: Option<f64>,
    failed: BTreeSet<usize>,
    successful: BTreeSet<usize>,
    cancelled: bool,
    records: BTreeMap<(usize, String, String), (String, f64)>,
    activities: Vec<Value>,
}
impl State {
    fn activity(&mut self, source: &str, message: &str, error: bool) {
        let source = match source {
            "web" | "mcp" | "scheduler" | "config" => source,
            _ => "manual",
        };
        self.activities.insert(0, json!({"level":if error {"WARN"} else {"INFO"}, "source":source, "message":message, "detail":"", "timestamp":now()}));
        self.activities.truncate(50);
    }
}

pub struct DashboardService {
    path: PathBuf,
    state: Mutex<State>,
    schedule: Arc<Schedule>,
}

impl DashboardService {
    pub fn new(config_path: Option<PathBuf>, interval: u16) -> Result<Self> {
        validation::interval(interval)?;
        let path = config_path.unwrap_or_else(|| {
            config::file::existing_default()
                .map(PathBuf::from)
                .unwrap_or_else(|| PathBuf::from("config.json"))
        });
        if path.to_string_lossy().contains("://") {
            return Err(invalid("dashboard configuration must be a local file"));
        }
        let path = config::file::expand_home(&path.to_string_lossy());
        let path = if path.is_absolute() {
            path
        } else {
            std::env::current_dir().map_err(operation_error)?.join(path)
        };
        let service = Self {
            path,
            state: Mutex::new(State::default()),
            schedule: Arc::new(Schedule::new(interval)),
        };
        Ok(service)
    }

    pub fn config_path(&self) -> &Path {
        &self.path
    }

    fn lock(&self) -> Result<MutexGuard<'_, State>> {
        self.state.lock().map_err(operation_error)
    }

    pub fn validate(&self, document: Value) -> Result<Value> {
        validation::validate(document, &config::env::load())
    }

    fn parse(&self, content: &str) -> Result<Value> {
        self.validate(config::file::parse(content).map_err(|_| {
            invalid("configuration is not valid JSON or a supported legacy literal")
        })?)
    }

    fn load_document(&self) -> Result<Value> {
        match fs::read_to_string(&self.path) {
            Ok(content) => self.parse(&content),
            Err(error) if error.kind() == io::ErrorKind::NotFound => self.validate(json!({})),
            Err(error) => Err(operation_error(error)),
        }
    }

    fn runtime(&self) -> Result<Vec<Config>> {
        config::from_document(self.load_document()?, &config::env::load())
            .map_err(|_| invalid("invalid runtime configuration"))
    }

    pub fn config_state(&self) -> Result<Value> {
        let _state = self.lock()?;
        self.config_state_locked()
    }

    fn config_state_locked(&self) -> Result<Value> {
        let mut state = json!({
            "config":{"$schema":MODEL["schema"]["url"], "providers":[]},
            "model": *MODEL, "path":self.path, "exists":self.path.exists(),
            "backup_available":storage::backup(&storage::target(&self.path)?).is_file(),
        });
        let content = match fs::read_to_string(&self.path) {
            Ok(content) => content,
            Err(error) if error.kind() == io::ErrorKind::NotFound => "{}".to_owned(),
            Err(error) => return Err(operation_error(error)),
        };
        match self.parse(&content) {
            Ok(document) => state["config"] = document,
            Err(error) => {
                state["validation_error"] = json!(error.message);
                state["raw"] = json!(content);
            }
        }
        Ok(state)
    }

    pub fn save(&self, document: Value) -> Result<Value> {
        let mut state = self.lock()?;
        let document = self.validate(document)?;
        let content = format!(
            "{}\n",
            serde_json::to_string_pretty(&document).map_err(operation_error)?
        );
        storage::write(&self.path, content.as_bytes())?;
        self.apply_interval(&document);
        *state = State::default();
        state.activity("config", "Configuration saved", false);
        self.config_state_locked()
    }

    pub fn restore_backup(&self) -> Result<Value> {
        let mut state = self.lock()?;
        let backup = storage::backup(&storage::target(&self.path)?);
        let content = fs::read_to_string(backup).map_err(|error| {
            if error.kind() == io::ErrorKind::NotFound {
                DashboardError {
                    status: 404,
                    code: "backup_not_found",
                    message: "No configuration backup is available.".to_owned(),
                }
            } else {
                operation_error(error)
            }
        })?;
        let document = self.parse(&content)?;
        storage::restore(&self.path, content.as_bytes())?;
        self.apply_interval(&document);
        *state = State::default();
        state.activity("config", "Configuration backup restored", false);
        self.config_state_locked()
    }

    fn apply_interval(&self, document: &Value) {
        if let Some(interval) = document.get("interval").and_then(Value::as_u64) {
            self.schedule.configure(None, interval as u16);
        }
    }

    pub fn dashboard(&self) -> Result<Value> {
        let mut state = self.lock()?;
        self.dashboard_locked(&mut state)
    }

    fn dashboard_locked(&self, state: &mut State) -> Result<Value> {
        let mut result = json!({"state":"unconfigured", "message":"Add at least one domain to synchronize", "config_path":self.path,
            "last_sync":null, "addresses":[], "providers":[], "records":[], "activities":state.activities, "scheduler":self.schedule.status()});
        let configs = match self.runtime() {
            Ok(configs) => configs,
            Err(_) => {
                result["state"] = json!("error");
                result["message"] =
                    json!("Configuration needs repair; open the configuration API for details");
                return Ok(result);
            }
        };
        ensure_identity(state, &configs)?;
        let mut providers = Vec::new();
        let mut records = Vec::new();
        let mut addresses = BTreeSet::new();
        let mut configured = 0;
        let mut last_sync = state.last_sync;
        for (index, config) in configs.iter().enumerate() {
            let cache = Cache::open(
                &config.cache,
                &config.cache_identity(),
                config.cache_max_age,
                Logger::stderr(Level::Critical, Vec::new()),
            )
            .ok()
            .flatten();
            let cached_time = cache
                .as_ref()
                .and_then(Cache::modified)
                .and_then(|modified| modified.duration_since(UNIX_EPOCH).ok())
                .map(|duration| duration.as_secs_f64());
            let mut cached = false;
            for (domains, record_type) in [(&config.ipv4, "A"), (&config.ipv6, "AAAA")] {
                configured += domains.len();
                for domain in domains {
                    let domain = domain.to_ascii_lowercase();
                    let memory =
                        state
                            .records
                            .get(&(index, domain.clone(), record_type.to_owned()));
                    let address = memory.map(|record| record.0.as_str()).or_else(|| {
                        cache
                            .as_ref()
                            .and_then(|cache| cache.get(config.provider, &domain, record_type))
                    });
                    if let Some(address) =
                        address.and_then(|address| address.parse::<std::net::IpAddr>().ok())
                    {
                        if (record_type == "A") != address.is_ipv4() {
                            continue;
                        }
                        let address = address.to_string();
                        cached = true;
                        let updated = memory.map(|record| record.1).or(cached_time);
                        if let Some(updated) = updated {
                            last_sync =
                                Some(last_sync.map_or(updated, |previous| previous.max(updated)));
                        }
                        records.push(json!({"domain":domain,"type":record_type,"value":address,"provider":config.provider.as_str(),"provider_index":index,"updated":updated}));
                        addresses
                            .insert((if record_type == "A" { "IPv4" } else { "IPv6" }, address));
                    }
                }
            }
            let label = MODEL["providers"]
                .as_array()
                .and_then(|providers| {
                    providers
                        .iter()
                        .find(|p| p["id"] == config.provider.as_str())
                })
                .and_then(|p| p["name"].as_str())
                .unwrap_or(config.provider.as_str());
            providers.push(json!({"id":config.provider.as_str(),"index":index,"label":label,"records":config.ipv4.len()+config.ipv6.len(),"status":if state.failed.contains(&index) {"error"} else if cached || state.successful.contains(&index) {"synced"} else {"configured"}}));
        }
        let (status, message) = if configured == 0 {
            ("unconfigured", "Add at least one domain to synchronize")
        } else if !state.failed.is_empty() {
            ("error", "Some providers failed to synchronize")
        } else if state.cancelled {
            ("error", "Synchronization cancelled")
        } else if !records.is_empty() || state.last_sync.is_some() {
            ("synced", "Synchronization data available")
        } else {
            ("ready", "Configuration ready for synchronization")
        };
        records.sort_by_key(|record| {
            (
                record["domain"].as_str().unwrap_or("").to_owned(),
                record["type"].as_str().unwrap_or("").to_owned(),
                record["provider_index"].as_u64(),
            )
        });
        result["state"] = json!(status);
        result["message"] = json!(message);
        result["last_sync"] = json!(last_sync);
        result["providers"] = json!(providers);
        result["records"] = json!(records);
        result["addresses"] = json!(
            addresses
                .into_iter()
                .map(|(family, value)| json!({"family":family,"value":value}))
                .collect::<Vec<_>>()
        );
        Ok(result)
    }

    pub fn sync(&self, source: &str, cancelled: &(dyn Fn() -> bool + Sync)) -> Result<Value> {
        let mut state = self.lock()?;
        let configs = self.runtime()?;
        if !configs
            .iter()
            .any(|config| !config.ipv4.is_empty() || !config.ipv6.is_empty())
        {
            return Err(invalid("add at least one domain before synchronization"));
        }
        ensure_identity(&mut state, &configs)?;
        state.failed.clear();
        state.successful.clear();
        state.cancelled = false;
        for (index, config) in configs.iter().enumerate() {
            if config.ipv4.is_empty() && config.ipv6.is_empty() {
                continue;
            }
            let outcome = update::update_config(config, cancelled);
            let timestamp = now();
            for record in outcome.records {
                state.records.insert(
                    (index, record.domain, record.record_type.to_owned()),
                    (record.address, timestamp),
                );
            }
            if !outcome.failures.is_empty() {
                state.failed.insert(index);
            }
            if outcome.cancelled || cancelled() {
                state.cancelled = true;
                state.activity(source, "Synchronization cancelled", true);
                return Err(DashboardError {
                    status: 409,
                    code: "cancelled",
                    message: "Synchronization cancelled.".to_owned(),
                });
            }
            if outcome.failures.is_empty() {
                state.successful.insert(index);
            }
        }
        if !state.failed.is_empty() {
            state.activity(source, "Some providers failed to synchronize", true);
            return Err(DashboardError {
                status: 500,
                code: "operation_failed",
                message:
                    "Synchronization failed for one or more providers; inspect provider status."
                        .to_owned(),
            });
        }
        state.last_sync = Some(now());
        state.activity(source, "Synchronization completed", false);
        self.dashboard_locked(&mut state)
    }

    pub fn configure_scheduler(
        &self,
        action: &str,
        scheduler_name: &str,
        interval: u16,
    ) -> Result<Value> {
        let _state = self.lock()?;
        validation::interval(interval)?;
        if !matches!(scheduler_name, "web" | "auto") {
            return Err(invalid("only the in-process web scheduler is supported"));
        }
        let enabled = match action {
            "enable" | "install" => Some(true), "disable" | "uninstall" => Some(false), "configure" => None,
            "takeover" => return Err(DashboardError { status:501, code:"unsupported", message:"External scheduler inspection and takeover are not supported. Disable external tasks separately before enabling in-process scheduling.".to_owned() }),
            _ => return Err(invalid("unsupported scheduler action")),
        };
        self.schedule.configure(enabled, interval);
        Ok(self.schedule.status())
    }

    pub fn start_scheduler(self: &Arc<Self>) -> SchedulerHandle {
        scheduler::start(self)
    }
}

fn ensure_identity(state: &mut State, configs: &[Config]) -> Result<()> {
    let identities = configs
        .iter()
        .map(Config::cache_identity)
        .collect::<Vec<_>>();
    let identity = sha256_hex(serde_json::to_vec(&identities).map_err(operation_error)?);
    if state.identity != identity {
        let activities = std::mem::take(&mut state.activities);
        *state = State {
            identity,
            activities,
            ..State::default()
        };
    }
    Ok(())
}

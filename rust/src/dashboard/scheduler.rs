use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Condvar, Mutex, MutexGuard};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use serde_json::{Value, json};

use super::{DashboardService, now};

struct ScheduleState {
    enabled: bool,
    active: bool,
    running: bool,
    interval: u16,
    next: Option<Instant>,
    last_run: Option<f64>,
    last_error: Option<String>,
}

pub(super) struct Schedule {
    state: Mutex<ScheduleState>,
    changed: Condvar,
    stopping: AtomicBool,
}
impl Schedule {
    pub(super) fn new(interval: u16) -> Self {
        Self {
            state: Mutex::new(ScheduleState {
                enabled: true,
                active: false,
                running: false,
                interval,
                next: None,
                last_run: None,
                last_error: None,
            }),
            changed: Condvar::new(),
            stopping: AtomicBool::new(false),
        }
    }
    fn lock(&self) -> MutexGuard<'_, ScheduleState> {
        self.state.lock().unwrap_or_else(|error| error.into_inner())
    }
    pub(super) fn configure(&self, enabled: Option<bool>, interval: u16) {
        let mut state = self.lock();
        if let Some(enabled) = enabled {
            state.enabled = enabled;
        }
        state.interval = interval;
        rearm(&mut state);
        self.changed.notify_all();
    }
    pub(super) fn status(&self) -> Value {
        let state = self.lock();
        json!({"scheduler":"web", "installed":true,"active":state.active,"enabled":state.enabled,"running":state.running,
            "interval":state.interval,"next_run":state.next.map(|next| now()+next.saturating_duration_since(Instant::now()).as_secs_f64()),
            "last_run":state.last_run,"last_error":state.last_error,"blocked_reason":null,
            "external":{"supported":false,"state":"unknown","message":"External scheduled tasks must be managed separately"}})
    }
}

fn rearm(state: &mut ScheduleState) {
    state.next = (state.enabled && state.active)
        .then(|| Instant::now() + Duration::from_secs(u64::from(state.interval) * 60));
}

pub struct SchedulerHandle {
    schedule: Arc<Schedule>,
    thread: Option<JoinHandle<()>>,
}
impl SchedulerHandle {
    pub fn stop(&mut self) {
        if let Some(thread) = self.thread.take() {
            {
                let _state = self.schedule.lock();
                self.schedule.stopping.store(true, Ordering::Release);
                self.schedule.changed.notify_all();
            }
            let _ = thread.join();
        }
    }
}
impl Drop for SchedulerHandle {
    fn drop(&mut self) {
        self.stop();
    }
}

pub(super) fn start(service: &Arc<DashboardService>) -> SchedulerHandle {
    let schedule = service.schedule.clone();
    let mut state = schedule.lock();
    if state.active {
        return SchedulerHandle {
            schedule: schedule.clone(),
            thread: None,
        };
    }
    schedule.stopping.store(false, Ordering::Release);
    state.active = true;
    state.last_error = None;
    rearm(&mut state);
    let service = service.clone();
    let spawned = thread::Builder::new()
        .name("ddns-web-scheduler".to_owned())
        .spawn(move || run(service));
    let thread = match spawned {
        Ok(thread) => Some(thread),
        Err(_) => {
            state.active = false;
            state.next = None;
            state.last_error = Some("Cannot start scheduler thread".to_owned());
            None
        }
    };
    drop(state);
    SchedulerHandle { schedule, thread }
}

fn run(service: Arc<DashboardService>) {
    let schedule = &service.schedule;
    loop {
        let mut state = schedule.lock();
        loop {
            if schedule.stopping.load(Ordering::Acquire) {
                state.active = false;
                state.running = false;
                state.next = None;
                return;
            }
            if !state.enabled {
                state.next = None;
                state = schedule
                    .changed
                    .wait(state)
                    .unwrap_or_else(|error| error.into_inner());
                continue;
            }
            if state.next.is_none() {
                rearm(&mut state);
            }
            let delay = state
                .next
                .expect("enabled scheduler deadline")
                .saturating_duration_since(Instant::now());
            if delay.is_zero() {
                break;
            }
            state = schedule
                .changed
                .wait_timeout(state, delay)
                .unwrap_or_else(|error| error.into_inner())
                .0;
        }
        state.running = true;
        state.next = None;
        drop(state);
        // Never acquire the service mutation lock while holding the scheduler lock.
        let result = service.sync("scheduler", &|| schedule.stopping.load(Ordering::Acquire));
        let mut state = schedule.lock();
        state.running = false;
        state.last_run = Some(now());
        state.last_error = result.err().map(|error| error.message);
        rearm(&mut state);
    }
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::sync::Arc;
    use std::thread;
    use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

    use serde_json::json;

    use super::super::DashboardService;

    #[test]
    fn scheduled_sync_uses_real_updater_and_duplicate_start_does_not_stop_owner() {
        let directory = std::env::temp_dir().join(format!(
            "ddns-scheduler-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&directory).unwrap();
        let service =
            Arc::new(DashboardService::new(Some(directory.join("config.json")), 1).unwrap());
        service.save(json!({"dns":"debug","cache":false,"log":{"level":"CRITICAL"},"ipv4":["scheduled.example.com"],"index4":["shell:echo 192.0.2.7"],"index6":false})).unwrap();
        let mut handle = service.start_scheduler();
        drop(service.start_scheduler());
        {
            let mut state = service.schedule.lock();
            assert!(state.active);
            state.next = Some(Instant::now());
            service.schedule.changed.notify_all();
        }
        let deadline = Instant::now() + Duration::from_secs(5);
        while service.schedule.status()["last_run"].is_null() && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        let status = service.dashboard().unwrap();
        handle.stop();
        assert_eq!(status["state"], "synced");
        assert_eq!(status["records"][0]["value"], "192.0.2.7");
        assert_eq!(service.schedule.status()["active"], false);
        assert!(service.schedule.status()["next_run"].is_null());
        drop(service);
        fs::remove_dir_all(directory).unwrap();
    }
}

use std::collections::BTreeMap;
use std::ffi::OsString;
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Arc;
use std::sync::atomic::AtomicBool;

use serde_json::{Value, json};

use crate::config;
use crate::dashboard::DashboardService;
use crate::error::{Error, Result};
use crate::http_server::HttpServer;
use crate::http_settings::HttpSettings;

const WEB_HELP: &str = "Usage: ddns-rs web [-c FILE] [OPTIONS]\n\nServe the embedded dashboard and /mcp endpoint.\n  -c, --config FILE       One local configuration file\n      --host HOST         Bind address (default: 127.0.0.1)\n      --port PORT         Listener port (default: 9876; 0 selects an unused port)\n      --http-token TOKEN  Shared HTTP bearer token; required outside loopback\n      --http-origin URL   Allowed MCP browser origin (repeatable)\n      --interval MINUTES  Web sync interval, 1..1440 (default: 5)\n      --open              Open the dashboard in a browser\n  -h, --help              Show this help\n";
const MCP_HELP: &str = "Usage: ddns-rs mcp [-c FILE] [OPTIONS]\n\nServe DDNS status and synchronization tools.\n  -c, --config FILE       One local configuration file\n      --transport MODE    stdio (default) or http\n      --host HOST         HTTP bind address (default: 127.0.0.1)\n      --port PORT         HTTP port (default: 9876; 0 selects an unused port)\n      --http-token TOKEN  Shared HTTP bearer token; required outside loopback\n      --http-origin URL   Allowed MCP browser origin (repeatable)\n  -h, --help              Show this help\n";

#[derive(Debug)]
pub struct ServerOptions {
    web: bool,
    http: bool,
    config_path: Option<PathBuf>,
    settings: BTreeMap<String, Value>,
    interval: Option<u16>,
    open: bool,
    help: bool,
}

pub fn parse(arguments: &[OsString]) -> Result<Option<ServerOptions>> {
    let args: Vec<&str> = match arguments
        .iter()
        .map(|arg| arg.to_str())
        .collect::<Option<Vec<_>>>()
    {
        Some(args) => args,
        None => return Ok(None),
    };
    let mode = args.get(1).copied();
    let explicit = matches!(mode, Some("web" | "mcp"));
    if !explicit
        && args.iter().any(|arg| {
            matches!(*arg, "--help" | "-h" | "--version" | "-v" | "--new-config")
                || arg.starts_with("--new-config=")
        })
    {
        return Ok(None);
    }
    let interval_flag = args
        .iter()
        .any(|arg| *arg == "--interval" || arg.starts_with("--interval="));
    let environment = config::env::load();
    if !explicit && !interval_flag && !has_config_interval(arguments, &environment)? {
        return Ok(None);
    }
    let web = mode != Some("mcp");
    let mut options = ServerOptions {
        web,
        http: web,
        config_path: None,
        settings: BTreeMap::new(),
        interval: None,
        open: false,
        help: false,
    };
    let mut index = if explicit { 2 } else { 1 };
    let mut paths = Vec::new();
    while index < args.len() {
        let (name, inline) = args[index]
            .split_once('=')
            .map_or((args[index], None), |(name, value)| (name, Some(value)));
        index += 1;
        match name {
            "-h" | "--help" if inline.is_none() => {
                options.help = true;
                return Ok(Some(options));
            }
            "--open" if web && inline.is_none() => options.open = true,
            "-c" | "--config" => paths.push(value(&args, &mut index, inline, name)?.to_owned()),
            "--host" | "--port" | "--http-token" | "--http_token" => {
                let key = match name {
                    "--host" => "host",
                    "--port" => "port",
                    _ => "token",
                };
                options.settings.insert(
                    key.to_owned(),
                    json!(value(&args, &mut index, inline, name)?),
                );
            }
            "--http-origin" | "--http_origins" => {
                let origin = value(&args, &mut index, inline, name)?;
                options
                    .settings
                    .entry("origins".to_owned())
                    .or_insert_with(|| json!([]))
                    .as_array_mut()
                    .expect("origin array")
                    .push(json!(origin));
            }
            "--interval" if web => {
                options.interval = Some(parse_interval(value(&args, &mut index, inline, name)?)?)
            }
            "--transport" if !web => {
                options.http = match value(&args, &mut index, inline, name)? {
                    "stdio" => false,
                    "http" => true,
                    _ => {
                        return Err(Error::Usage(
                            "MCP transport must be stdio or http".to_owned(),
                        ));
                    }
                }
            }
            _ => {
                return Err(Error::Usage(format!(
                    "unsupported {} option: {name}",
                    if web { "web" } else { "mcp" }
                )));
            }
        }
    }
    if !options.http && !options.settings.is_empty() {
        return Err(Error::Usage(
            "MCP HTTP options require --transport http".to_owned(),
        ));
    }
    if paths.is_empty()
        && let Some(value) = environment.get("config")
    {
        paths = config::value_list(Some(value), false)?;
    }
    if paths.len() > 1 {
        return Err(Error::Usage(
            "Web and MCP require exactly one local configuration file".to_owned(),
        ));
    }
    if let Some(path) = paths.first() {
        if path.is_empty() || path.contains("://") {
            return Err(Error::Usage(
                "Web and MCP only support a local configuration file".to_owned(),
            ));
        }
        options.config_path = Some(config::file::expand_home(path));
    } else {
        options.config_path = config::file::existing_default().map(PathBuf::from);
    }
    Ok(Some(options))
}

fn value<'a>(
    args: &[&'a str],
    index: &mut usize,
    inline: Option<&'a str>,
    name: &str,
) -> Result<&'a str> {
    if let Some(value) = inline {
        return Ok(value);
    }
    let value = args
        .get(*index)
        .copied()
        .filter(|value| !value.starts_with('-'))
        .ok_or_else(|| Error::Usage(format!("{name} requires a value")))?;
    *index += 1;
    Ok(value)
}

fn parse_interval(value: &str) -> Result<u16> {
    value
        .parse::<u16>()
        .ok()
        .filter(|value| (1..=1440).contains(value))
        .ok_or_else(|| {
            Error::Usage("interval must be an integer between 1 and 1440 minutes".to_owned())
        })
}

fn has_config_interval(
    arguments: &[OsString],
    environment: &BTreeMap<String, Value>,
) -> Result<bool> {
    let mut selected = None;
    let mut arguments = arguments.iter().skip(1).peekable();
    while let Some(argument) = arguments.next() {
        let Some(argument) = argument.to_str() else {
            continue;
        };
        if matches!(argument, "-c" | "--config") {
            let paths = selected.get_or_insert_with(Vec::new);
            while arguments
                .peek()
                .is_some_and(|value| !value.to_string_lossy().starts_with('-'))
            {
                paths.push(
                    arguments
                        .next()
                        .expect("peeked argument")
                        .to_string_lossy()
                        .into_owned(),
                );
            }
        } else if let Some(path) = argument.strip_prefix("--config=") {
            selected.get_or_insert_with(Vec::new).push(path.to_owned());
        }
    }
    let paths = if let Some(paths) = selected {
        paths
    } else if let Some(value) = environment.get("config") {
        config::value_list(Some(value), false)?
    } else {
        config::file::existing_default().into_iter().collect()
    };
    Ok(paths
        .iter()
        .filter(|path| !path.contains("://"))
        .any(|path| {
            std::fs::read_to_string(config::file::expand_home(path))
                .ok()
                .and_then(|content| config::file::parse(&content).ok())
                .is_some_and(|document| {
                    document
                        .get("interval")
                        .is_some_and(|value| !value.is_null())
                })
        }))
}

pub fn run(options: ServerOptions) -> Result<()> {
    if options.help {
        print!("{}", if options.web { WEB_HELP } else { MCP_HELP });
        return Ok(());
    }
    let document = options
        .config_path
        .as_ref()
        .and_then(|path| std::fs::read_to_string(path).ok())
        .and_then(|content| config::file::parse(&content).ok())
        .unwrap_or_else(|| json!({}));
    let interval = if let Some(interval) = options.interval {
        interval
    } else if options.web
        && let Some(value) = document.get("interval")
    {
        value
            .as_u64()
            .and_then(|value| u16::try_from(value).ok())
            .filter(|value| (1..=1440).contains(value))
            .ok_or_else(|| {
                Error::Config("interval must be an integer between 1 and 1440 minutes".to_owned())
            })?
    } else {
        5
    };
    let service = Arc::new(
        DashboardService::new(options.config_path, interval)
            .map_err(|error| Error::Config(error.to_string()))?,
    );
    if !options.http {
        return crate::mcp::serve_stdio(service);
    }
    let settings = HttpSettings::resolve(&options.settings, &document, &config::env::load())?;
    let server = HttpServer::bind(Arc::clone(&service), settings, options.web)?;
    let url = server.launch_url()?;
    let _scheduler = options.web.then(|| service.start_scheduler());
    println!(
        "DDNS {}: {url}",
        if options.web { "dashboard" } else { "MCP HTTP" }
    );
    std::io::stdout().flush()?;
    if options.open && open_browser(&url).is_err() {
        eprintln!("Unable to open a browser automatically; use the printed dashboard URL.");
    }
    server.serve(&AtomicBool::new(false))
}

fn open_browser(url: &str) -> Result<()> {
    #[cfg(target_os = "windows")]
    let mut command = {
        let mut command = Command::new("rundll32.exe");
        command.arg("url.dll,FileProtocolHandler");
        command
    };
    #[cfg(target_os = "macos")]
    let mut command = Command::new("open");
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    let mut command = Command::new("xdg-open");
    let mut child = command.arg(url).spawn()?;
    std::thread::spawn(move || {
        let _ = child.wait();
    });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(values: &[&str]) -> Vec<OsString> {
        values.iter().map(OsString::from).collect()
    }

    #[test]
    fn parses_server_modes_and_rejects_ignored_options() {
        let web = parse(&args(&["ddns-rs", "web", "--port", "0", "--interval=7"]))
            .unwrap()
            .unwrap();
        assert!(web.web && web.http);
        assert_eq!(web.interval, Some(7));
        let mcp = parse(&args(&[
            "ddns-rs",
            "mcp",
            "--transport=http",
            "--http-origin",
            "https://example.com",
        ]))
        .unwrap()
        .unwrap();
        assert!(!mcp.web && mcp.http);
        for arguments in [
            vec!["ddns-rs", "mcp", "--host", "127.0.0.1"],
            vec!["ddns-rs", "web", "-c", "a", "-c", "b"],
            vec!["ddns-rs", "web", "-c", "https://example.com/config"],
            vec!["ddns-rs", "web", "--token", "secret"],
            vec!["ddns-rs", "web", "--interval", "0"],
            vec!["ddns-rs", "web", "--interval", "1.5"],
            vec!["ddns-rs", "mcp", "--transport", "other"],
        ] {
            assert!(parse(&args(&arguments)).is_err(), "{arguments:?}");
        }
    }
}

#![forbid(unsafe_code)]

pub mod cache;
pub mod cli;
pub mod config;
pub mod dashboard;
pub mod error;
pub mod http;
pub mod http_server;
pub mod http_settings;
pub mod ip;
pub mod logging;
pub mod mcp;
mod mcp_http;
pub mod provider;
mod server_command;
pub mod signature;
pub mod update;

use std::ffi::OsString;

use error::Result;

pub fn run_from<I, S>(arguments: I) -> Result<()>
where
    I: IntoIterator<Item = S>,
    S: Into<OsString> + Clone,
{
    let arguments: Vec<OsString> = arguments.into_iter().map(Into::into).collect();
    if let Some(options) = server_command::parse(&arguments)? {
        return server_command::run(options);
    }
    update::run(arguments)
}

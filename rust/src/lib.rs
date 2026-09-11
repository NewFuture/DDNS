#![forbid(unsafe_code)]

pub mod cache;
pub mod cli;
pub mod config;
pub mod error;
pub mod http;
pub mod ip;
pub mod logging;
pub mod provider;
pub mod signature;
pub mod update;

use std::ffi::OsString;

use error::Result;

pub fn run_from<I, S>(arguments: I) -> Result<()>
where
    I: IntoIterator<Item = S>,
    S: Into<OsString> + Clone,
{
    update::run(arguments)
}

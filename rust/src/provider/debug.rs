use crate::error::Result;

use super::base::{Provider, RecordRequest};

pub struct DebugProvider;

impl Provider for DebugProvider {
    fn name(&self) -> &'static str {
        "debug"
    }

    fn set_record(&mut self, request: &RecordRequest) -> Result<()> {
        let label = match request.record_type.as_str() {
            "A" => "IPv4",
            "AAAA" => "IPv6",
            value => value,
        };
        println!("[{label}] {}", request.address);
        Ok(())
    }
}

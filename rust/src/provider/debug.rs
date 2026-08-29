use crate::error::Result;

use super::base::{Provider, RecordRequest};

pub struct DebugProvider;

impl Provider for DebugProvider {
    fn set_record(&mut self, request: &RecordRequest<'_>) -> Result<()> {
        let label = match request.record_type {
            "A" => "IPv4",
            "AAAA" => "IPv6",
            value => value,
        };
        println!("[{label}] {}", request.address);
        Ok(())
    }
}

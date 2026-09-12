use std::io::Read;
use std::sync::Arc;

use base64::Engine as _;
use base64::engine::general_purpose::STANDARD as BASE64;
use serde_json::{Value, json};

use crate::dashboard::DashboardService;
use crate::http_server::{Request, Response};
use crate::http_settings::{HttpSettings, host_header_is_loopback, token_matches};
use crate::mcp::{
    CLIENT_CAPABILITIES_KEY, McpServer, PROTOCOL_VERSION, PROTOCOL_VERSION_KEY, error_response,
};

pub(crate) fn handle(
    request: &Request,
    reader: &mut impl Read,
    settings: &HttpSettings,
    service: Arc<DashboardService>,
) -> Response {
    if request.method == "OPTIONS" {
        let Some(origin) = request
            .origin()
            .filter(|origin| settings.origins.contains(origin))
        else {
            return Response::error(403, "invalid_origin", "HTTP request origin is not allowed.");
        };
        return Response::empty(204)
            .header("Access-Control-Allow-Origin", &origin)
            .header("Access-Control-Allow-Methods", "POST, OPTIONS")
            .header(
                "Access-Control-Allow-Headers",
                "Authorization, Content-Type, MCP-Protocol-Version, Mcp-Method, Mcp-Name",
            )
            .header("Access-Control-Max-Age", "600")
            .header("Vary", "Origin");
    }
    let response = if !request.origin_allowed(settings, true) {
        Response::error(403, "invalid_origin", "HTTP request origin is not allowed.")
    } else if request.method != "POST" {
        Response::error(405, "method_not_allowed", "MCP HTTP only accepts POST.")
            .header("Allow", "POST, OPTIONS")
    } else if settings.token.is_none()
        && !host_header_is_loopback(request.header("host").unwrap_or_default())
    {
        Response::error(
            421,
            "invalid_host",
            "Unauthenticated HTTP only accepts loopback hosts.",
        )
    } else if !token_matches(request.token(false), settings.token.as_deref()) {
        Response::error(401, "invalid_token", "HTTP bearer token is invalid.")
            .header("WWW-Authenticate", "Bearer realm=\"ddns-mcp\"")
    } else {
        post(request, reader, service)
    };
    if let Some(origin) = request
        .origin()
        .filter(|origin| settings.origins.contains(origin))
    {
        response
            .header("Access-Control-Allow-Origin", &origin)
            .header("Vary", "Origin")
    } else {
        response
    }
}

fn post(request: &Request, reader: &mut impl Read, service: Arc<DashboardService>) -> Response {
    if !request
        .header("content-type")
        .unwrap_or_default()
        .split(';')
        .next()
        .unwrap_or_default()
        .trim()
        .eq_ignore_ascii_case("application/json")
    {
        return Response::error(
            415,
            "unsupported_media_type",
            "Content-Type must be application/json.",
        );
    }
    if !["application/json", "text/event-stream"]
        .iter()
        .all(|media| accepts(request.header("accept").unwrap_or_default(), media))
    {
        return Response::error(
            406,
            "not_acceptable",
            "Accept must include application/json and text/event-stream.",
        );
    }
    let message = match request.read_json(reader, true) {
        Ok(value) => value,
        Err(response) => return response,
    };
    if let Err(response) = validate_envelope(request, &message) {
        return response;
    }
    let response = McpServer::new(service, true).handle_message(message, &|| false);
    match response {
        None => Response::empty(202),
        Some(response) => {
            let status = match response.pointer("/error/code").and_then(Value::as_i64) {
                Some(-32022) => 400,
                Some(-32601) => 404,
                _ => 200,
            };
            Response::json(status, response)
        }
    }
}

fn valid_id(value: Option<&Value>) -> Value {
    value
        .filter(|value| value.is_string() || value.is_i64() || value.is_u64())
        .cloned()
        .unwrap_or(Value::Null)
}

fn validate_envelope(request: &Request, message: &Value) -> std::result::Result<(), Response> {
    let id = valid_id(message.get("id"));
    if message.get("jsonrpc").and_then(Value::as_str) != Some("2.0")
        || !message.get("method").is_some_and(Value::is_string)
        || (message.get("id").is_some() && id.is_null())
    {
        return Err(Response::json(
            400,
            error_response(id, -32600, "Invalid Request"),
        ));
    }
    if message
        .get("params")
        .is_some_and(|params| !params.is_object())
    {
        return Err(Response::json(
            400,
            error_response(id, -32602, "Invalid params"),
        ));
    }
    let mismatch = |detail: &str| Response::json(400, error_response(id.clone(), -32020, detail));
    for name in ["MCP-Protocol-Version", "Mcp-Method", "Mcp-Name"] {
        if request.header_count(name) > 1 {
            return Err(mismatch("MCP routing headers must not be repeated."));
        }
    }
    let meta = message.get("params").and_then(|params| params.get("_meta"));
    let body_version = meta
        .and_then(|meta| meta.get(PROTOCOL_VERSION_KEY))
        .and_then(Value::as_str);
    if request.header("MCP-Protocol-Version").is_none()
        || request.header("MCP-Protocol-Version") != body_version
    {
        return Err(mismatch(
            "MCP-Protocol-Version does not match request metadata.",
        ));
    }
    if body_version != Some(PROTOCOL_VERSION) {
        let mut response = error_response(id, -32022, "Unsupported protocol version");
        response["error"]["data"] =
            json!({"supported":[PROTOCOL_VERSION],"requested":body_version});
        return Err(Response::json(400, response));
    }
    let method = message.get("method").and_then(Value::as_str);
    if request.header("Mcp-Method").is_none() || request.header("Mcp-Method") != method {
        return Err(mismatch("Mcp-Method does not match the JSON-RPC method."));
    }
    if !meta
        .and_then(|meta| meta.get(CLIENT_CAPABILITIES_KEY))
        .is_some_and(Value::is_object)
    {
        return Err(Response::json(
            400,
            error_response(id, -32602, "Client capabilities metadata is required."),
        ));
    }
    if let Some(field) = match method {
        Some("tools/call" | "prompts/get") => Some("name"),
        Some("resources/read") => Some("uri"),
        _ => None,
    } {
        let header = request.header("Mcp-Name").and_then(decode_name);
        let body = message
            .get("params")
            .and_then(|params| params.get(field))
            .and_then(Value::as_str);
        if header.as_deref().is_none_or(str::is_empty) || header.as_deref() != body {
            return Err(mismatch("Mcp-Name does not match the named request."));
        }
    }
    Ok(())
}

fn accepts(header: &str, media: &str) -> bool {
    header.split(',').any(|entry| {
        let mut parts = entry.split(';').map(str::trim);
        if !parts
            .next()
            .is_some_and(|value| value.eq_ignore_ascii_case(media))
        {
            return false;
        }
        let mut quality = 1.0_f64;
        for part in parts {
            if let Some((name, value)) = part.split_once('=')
                && name.trim().eq_ignore_ascii_case("q")
            {
                let Ok(value) = value.trim().parse::<f64>() else {
                    return false;
                };
                if !value.is_finite() || !(0.0..=1.0).contains(&value) {
                    return false;
                }
                quality = value;
            }
        }
        quality > 0.0
    })
}

fn decode_name(value: &str) -> Option<String> {
    let value = value.trim_matches([' ', '\t']);
    if let Some(encoded) = value
        .strip_prefix("=?base64?")
        .and_then(|value| value.strip_suffix("?="))
    {
        return String::from_utf8(BASE64.decode(encoded).ok()?).ok();
    }
    value
        .bytes()
        .all(|byte| (0x20..=0x7e).contains(&byte))
        .then(|| value.to_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn negotiates_only_positive_finite_quality_values() {
        assert!(accepts(
            "application/json, text/event-stream",
            "application/json"
        ));
        for header in [
            "application/json;q=0",
            "application/json;q=NaN",
            "application/json;q=inf",
            "application/json;q=1.1",
            "application/json;q=invalid",
            "*/*",
        ] {
            assert!(!accepts(header, "application/json"), "{header}");
        }
    }

    #[test]
    fn decodes_named_request_header() {
        assert_eq!(
            decode_name(" get_ddns_status\t").as_deref(),
            Some("get_ddns_status")
        );
        assert_eq!(
            decode_name("=?base64?Z2V0X2RkbnNfc3RhdHVz?=").as_deref(),
            Some("get_ddns_status")
        );
        assert!(decode_name("=?base64?bad?=").is_none());
        assert!(decode_name("bad\nname").is_none());
    }
}

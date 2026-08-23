---
title: DDNS MCP Server
description: Connect DDNS status and synchronization tools to MCP clients over stdio or Streamable HTTP
---

# MCP Server

DDNS provides a standard-library-only MCP server so clients such as GitHub Copilot can inspect local cached status or run one complete DDNS synchronization after user approval. Provider credentials are never returned in protocol arguments or results.

Configuration path precedence is `-c/--config` > `DDNS_CONFIG` > the conventional local config paths. MCP mode accepts exactly one local file; remote URLs and multiple `-c` values are rejected.

## stdio (default)

```bash
ddns mcp -c /etc/ddns/config.json
```

stdio mode opens no network listener. stdout is reserved for one JSON-RPC message per line, while runtime logs go to stderr.

Add the server directly to GitHub Copilot CLI:

```bash
copilot mcp add ddns -- ddns mcp -c /etc/ddns/config.json
```

Alternatively, add the following to an MCP client configuration:

```json
{
  "mcpServers": {
    "ddns": {
      "command": "ddns",
      "args": ["mcp", "-c", "/etc/ddns/config.json"]
    }
  }
}
```

Escape Windows path backslashes as `\\` in JSON, or replace `command` with the absolute path to the `ddns` executable.

## Streamable HTTP

Start a standalone HTTP MCP server:

```bash
ddns mcp -c /etc/ddns/config.json --transport http
```

The default endpoint is `http://127.0.0.1:9876/mcp`. The [Web console](cli.md#web-console-and-in-process-scheduling) also exposes `/mcp` on its listener.

Standalone mode and Web share these options:

| Option | Description |
|--------|-------------|
| `--host` | Bind host; defaults to `127.0.0.1` and accepts a LAN address or `0.0.0.0` / `::` |
| `--port` | Listener port, default `9876`; use `0` to let the OS select one |
| `--http-token` | Shared Web API and HTTP MCP token; visible ASCII without spaces |
| `--http-origin ORIGIN` | Exact HTTP(S) origin allowed to access `/mcp`; repeatable |

Listener precedence is command line > root JSON [`http`](json.md#http) > `DDNS_HTTP_*` [environment variables](env.md#web-and-http-mcp) > `127.0.0.1:9876`.

When loopback has no token, the Web APIs (including full configuration and provider credentials) and `/mcp` are unauthenticated. A non-loopback or wildcard listener requires a non-empty token. MCP clients send it as `Authorization: Bearer <token>`.

DDNS does not provide TLS. Put LAN listeners behind a trusted HTTPS reverse proxy that preserves `Authorization`, `Host`, and `Origin`. Browser access through a TLS-terminating proxy must list the exact public HTTPS origin in `http.origins` or `--http-origin`, even when the public page appears same-origin; native MCP clients may omit `Origin`.

HTTP supports MCP `2026-07-28` only. Each message is a separate POST to `/mcp` using `Content-Type: application/json` with `MCP-Protocol-Version` and `Mcp-Method`; tool calls also require `Mcp-Name`. `Accept` must list both `application/json` and `text/event-stream`.

This tools-only implementation returns plain JSON and does not provide SSE, sessions, legacy HTTP, resources, prompts, or subscriptions.

## Available tools

| Tool | Arguments | Behavior |
|------|-----------|----------|
| `get_ddns_status` | None | Read local configuration, cached addresses and records, provider summaries, and the latest sync time; it does not query providers live |
| `update_dns_records` | None | Resolve current addresses using the configuration, synchronize every configured record once, and return the resulting status |

`update_dns_records` changes external DNS state, so clients should retain user confirmation before invoking it. The tool accepts no domain, address, provider, or credential arguments, preventing a model from bypassing the local configuration to write arbitrary records.

## Protocol and runtime limits

- stdio supports MCP `2026-07-28` and the `2025-11-25` `initialize` lifecycle.
- HTTP supports MCP `2026-07-28` only.
- When a stdio client cancels an update, the server stops before subsequent IP rules, domain records, or providers.
- HTTP provides no SSE cancellation; work may continue after a client disconnects.
- A provider API request already sent cannot be rolled back.
- Status comes from the local cache. With caching disabled, a later request in another process cannot reconstruct previous sync history, although the update call still returns its own result.
- Do not let multiple Web, MCP, or system-task processes update the same configuration concurrently.

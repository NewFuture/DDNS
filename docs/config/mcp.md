---
title: DDNS MCP 服务
description: 使用 stdio 或 Streamable HTTP 将 DDNS 状态查询和同步工具接入 MCP 客户端
---

# MCP 服务

DDNS 提供仅使用 Python 标准库的 MCP 服务，让 GitHub Copilot 等客户端查询本地缓存状态，或在人工确认后执行一次完整的 DDNS 同步。服务不会在协议参数或结果中返回 DNS 服务商凭据。

配置路径优先级为 `-c/--config` > `DDNS_CONFIG` > 默认本地配置路径。MCP 模式只接受一份本地配置文件，不支持远程 URL 或多个 `-c`。

## stdio（默认）

```bash
ddns mcp -c /etc/ddns/config.json
```

stdio 模式不监听网络。stdout 专用于每行一条 JSON-RPC 消息，运行日志只写入 stderr。

在 GitHub Copilot CLI 中可以直接添加：

```bash
copilot mcp add ddns -- ddns mcp -c /etc/ddns/config.json
```

也可以在支持 MCP 的客户端配置中添加：

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

Windows JSON 路径中的反斜杠需要写成 `\\`，也可以将 `command` 替换为 `ddns` 可执行文件的绝对路径。

## Streamable HTTP

独立启动 HTTP MCP：

```bash
ddns mcp -c /etc/ddns/config.json --transport http
```

默认 endpoint 为 `http://127.0.0.1:9876/mcp`。运行 [Web 控制台](cli.md#web-控制台与内置调度) 时，同一监听地址也会自动提供 `/mcp`。

独立模式与 Web 共用以下参数：

| 参数 | 描述 |
|------|------|
| `--host` | 监听地址；默认 `127.0.0.1`，支持具体局域网地址及 `0.0.0.0` / `::` |
| `--port` | 监听端口，默认 `9876`；设为 `0` 时由系统分配 |
| `--http-token` | Web API 与 HTTP MCP 共享的 token；仅允许无空格的可见 ASCII 字符 |
| `--http-origin ORIGIN` | 允许浏览器访问 `/mcp` 的精确 HTTP(S) origin；可重复 |

监听配置优先级为命令行 > JSON 顶层 [`http`](json.md#http) > `DDNS_HTTP_*` [环境变量](env.md#web-与-http-mcp) > `127.0.0.1:9876`。

回环地址未配置 token 时，Web API（包括完整配置和服务商凭据）与 `/mcp` 均免认证；非回环或通配监听必须配置非空 token。MCP 客户端通过 `Authorization: Bearer <token>` 发送凭据。

DDNS 不提供 TLS。局域网监听必须置于受信 HTTPS 反向代理之后，并保留 `Authorization`、`Host` 和 `Origin`。浏览器通过 TLS 终止代理访问 `/mcp` 时，即使公网页面看起来同源，也必须把精确的公网 HTTPS origin 配置到 `http.origins` 或 `--http-origin`；原生 MCP 客户端可不发送 `Origin`。

HTTP transport 仅支持 MCP `2026-07-28`。每个请求单独 POST 到 `/mcp`，必须使用 `Content-Type: application/json` 并携带 `MCP-Protocol-Version`、`Mcp-Method`，调用工具时还需 `Mcp-Name`；`Accept` 必须同时包含 `application/json` 和 `text/event-stream`。

当前 tools-only 实现返回普通 JSON，不提供 SSE、sessions、legacy HTTP、resources、prompts 或 subscriptions。

## 可用工具

| 工具 | 参数 | 行为 |
|------|------|------|
| `get_ddns_status` | 无 | 读取本地配置、缓存地址、缓存记录、服务商摘要和最近同步时间，不实时查询 DNS 服务商 |
| `update_dns_records` | 无 | 使用配置中的当前 IP 规则，对所有已配置记录执行一次完整同步，并返回同步后的状态 |

`update_dns_records` 会修改外部 DNS 状态，客户端应在调用前保留人工确认。工具不接受域名、IP、服务商或凭据参数，避免模型绕过本地配置写入任意记录。

## 协议和运行限制

- stdio 支持 MCP `2026-07-28`，并兼容 `2025-11-25` `initialize` 生命周期。
- HTTP 仅支持 MCP `2026-07-28`。
- stdio 客户端取消更新时，服务会在 IP 获取规则、域名记录及 DNS 服务商之间停止后续处理。
- HTTP 不提供 SSE 取消；客户端断开后同步可能继续完成。
- 已经发送给 DNS 服务商的 API 请求无法撤销。
- 状态来自本地缓存；关闭缓存后，另一进程中的后续状态请求无法还原此前的同步历史，但更新调用本身仍会返回本次结果。
- 不要让多个 Web、MCP 或系统任务进程同时更新同一份配置。

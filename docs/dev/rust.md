# Rust 客户端开发

`ddns-rs` 是与 Python `ddns` 并行维护的实验性实现。MVP 只负责单次同步，不替换现有命令、安装方式或发布资产。

## 当前支持

| 能力 | 状态 |
| --- | --- |
| Cloudflare、AliDNS、DNSPod、Debug | 已支持 |
| IPv4/IPv6 与全部现有 IP 规则 | 已支持 |
| CLI、`DDNS_*`、本地/远程/多配置、v4.1 `providers` | 已支持 |
| JSON 注释与受限 Python 数据字面量 | 已支持 |
| 缓存、代理回退、重试、TLS 与自定义 CA | 已支持 |
| `task`、Web、MCP、其他 Provider、Docker | 计划中 |

## 构建与运行

使用当前 stable Rust：

```bash
cargo build --manifest-path rust/Cargo.toml --release --locked
rust/target/release/ddns-rs --help
rust/target/release/ddns-rs -c config.json
```

Windows 产物为 `rust\target\release\ddns-rs.exe`。

## 架构

- `cli.rs`：兼容参数、别名和列表规则，不依赖 CLI 框架。
- `config/`：环境变量、JSONC、受限 Python 字面量、v4.1 展平和优先级合并。
- `http.rs`：基于 `ureq`/rustls 的同步传输、代理、重试、TLS 和脱敏。
- `ip.rs`：IPv4/IPv6 地址发现与规则回退。
- `cache.rs`：独立于 Python 的版本化缓存和原子写入。
- `provider/`：公共 CRUD 编排及首批 Provider。
- `update.rs`：逐配置、地址族和域名执行，继续后续项并汇总失败。

生产代码不使用 unsafe，不引入异步运行时、通用错误框架或 mock 框架。Provider 测试通过注入 HTTP 客户端完成，集成测试只访问本机 fixture。

## 验证

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

CI 还会在 Linux x64/arm64、Windows x64、macOS x64/arm64 构建并冒烟测试二进制。

## 安全边界

- `ssl=auto` 会在确认属于证书校验错误时警告并重试一次不校验证书的连接；生产环境优先使用 `ssl=true`。
- 远程配置中的 `cmd:` 与 `shell:` 会执行本机命令，只能加载可信 URL。
- Python 字面量解析器只接受字典、列表/元组、字符串、数字、`True`、`False` 和 `None`，不会执行表达式。
- 日志会遮蔽 token 及其百分号编码形式；缓存不保存凭据。

## 后续顺序

1. 迁移 Callback、No-IP、HE 等简单 Provider。
2. 迁移其余 CRUD Provider 和共享签名算法。
3. 迁移 systemd、cron、launchd、schtasks。
4. 迁移 Web 控制台与 MCP。
5. 增加 Rust Docker、安装脚本和正式 Release；达到完整等价并稳定运行后再讨论改名为 `ddns`。

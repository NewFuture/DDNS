# Rust 客户端开发

`ddns-rs` 是与 Python `ddns` 并行维护的实验性实现。MVP 只负责单次同步，
不替换稳定的 Python `ddns` 命令或默认安装方式。

## 当前支持

| 能力 | 状态 |
| --- | --- |
| 全部 Python DNS Provider 及其兼容别名（Cloudflare、AliDNS/ESA、DNSPod、EdgeOne、ClouDNS、DNS.COM、HE.net、华为云、NameSilo、No-IP、Callback、West.cn、Debug） | 已支持 |
| IPv4/IPv6 与全部现有 IP 规则类型 | 已支持；`regex:` 使用 Rust 语法 |
| CLI、`DDNS_*`、本地/远程/多配置、v4.1 `providers` | 已支持 |
| JSON 注释与受限 Python 数据字面量 | 已支持 |
| 缓存、代理回退、重试、TLS 与自定义 CA | 已支持 |
| Linux amd64/arm64 Docker 镜像 | 标签发布工作流推送到 `ghcr.io/newfuture/ddns-rs`；仅运行 `ddns-rs`，无内置调度 |
| Linux x64/arm64、macOS x64/arm64、Windows x64 Release 资产 | 标签发布工作流生成 `ddns-rs-*`，每个资产附带 `.sha256` |
| `task`、Web、MCP | 计划中 |

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
- `provider/`：公共 CRUD 编排及全部 DNS Provider。
- `update.rs`：逐配置、地址族和域名执行，继续后续项并汇总失败。

生产代码不使用 unsafe，不引入异步运行时、通用错误框架或 mock 框架。Provider 测试通过注入 HTTP 客户端完成，集成测试只访问本机 fixture。

## 验证

```bash
cargo fmt --manifest-path rust/Cargo.toml --check
cargo clippy --manifest-path rust/Cargo.toml --locked --all-targets --all-features -- -D warnings
cargo test --manifest-path rust/Cargo.toml --locked
```

CI 还会在 Linux x64/arm64、Windows x64、macOS x64/arm64 构建、测试并打包
二进制；Linux x64/arm64 还会构建和离线冒烟测试 Docker 镜像。

## 安全边界

- `ssl=auto` 会在确认属于证书校验错误时警告并重试一次不校验证书的连接；生产环境优先使用 `ssl=true`。
- 远程配置中的 `cmd:` 与 `shell:` 会执行本机命令，只能加载可信 URL。
- `regex:` 使用 Rust `regex` 语法，不支持 Python 环视和反向引用；不兼容模式会返回明确错误。
- 复用配置中的自定义 `cache` 路径时，Rust 写入同级 `<path>.ddns-rs`，不会覆盖 Python 缓存。
- Python 字面量解析器只接受字典、列表/元组、字符串、数字、`True`、`False` 和 `None`，不会执行表达式。
- 日志会遮蔽 token 及其百分号编码形式；缓存不保存凭据。

## 后续顺序

1. 迁移 systemd、cron、launchd、schtasks。
2. 迁移 Web 控制台与 MCP。
3. 达到完整等价并稳定运行后再讨论改名为 `ddns`。

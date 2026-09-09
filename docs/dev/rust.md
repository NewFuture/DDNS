# Rust V5 客户端开发

`ddns-rs` 是 DDNS 下一主版本 V5 的 Rust 实现，集成分支为 `v5`。
Python 版本继续在 `master` / `v4` 维护；Rust 功能 PR 应以 `v5` 为目标。
当前开发版本为 `5.0.0-alpha1`，只负责单次同步，尚未发布，也不替换稳定的
Python `ddns` 命令或默认安装方式。

## 当前支持

| 能力 | 状态 |
| --- | --- |
| 全部 Python DNS Provider 及其兼容别名（Cloudflare、AliDNS/ESA、DNSPod、EdgeOne、ClouDNS、DNS.COM、HE.net、华为云、NameSilo、No-IP、Callback、West.cn、Debug） | 已支持 |
| IPv4/IPv6 与全部现有 IP 规则类型 | 已支持；`regex:` 使用 Rust 语法 |
| CLI、`DDNS_*`、本地/远程/多配置、v4.1 `providers` | 已支持 |
| JSON 注释与受限 Python 数据字面量 | 已支持 |
| 缓存、代理回退、重试、TLS 与自定义 CA | 已支持 |
| Linux amd64/arm64 Docker 镜像 | 构建和离线冒烟测试；准备流程保存 OCI 工件，不推送公共镜像，无内置调度 |
| Linux x64/arm64、macOS x64/arm64、Windows x64 二进制 | 准备流程保存 `ddns-rs-*` 与 `.sha256` Actions 工件；Linux 使用静态 musl 目标 |
| `task`、Web、MCP | 计划中 |

## V5 分支与发布准备

保留 `rust/` 布局、`ddns-rs` 命令及现有配置兼容边界，暂不删除 Python 实现。
`rust/Cargo.toml` 与 `rust/Cargo.lock` 的版本必须一致。`v5` 上的版本文件或
准备工作流发生变更时，`Prepare Rust V5` 自动构建，无需创建标签。它也接受
`v5` 分支上的手动准备，或与 Cargo 版本一致的规范 `v5.*` 标签，并生成经过
校验的原生工件和双架构 OCI 工件；不会创建 Release、上传发布资产或推送镜像。
V5 文档构建也不会部署覆盖稳定站点；本分支保留的 Python 发布入口拒绝 `v5.*`，
不改动稳定分支的发布配置。

当前没有可安装的 V5 发布版本，应使用源码或 CI 工件。在首次创建公开 V5 标签前，
还需隔离安装器和下载服务的 Python/Rust 版本选择，并单独确认 Rust 发布流程；
暂不要使用仓库级 `latest` / `beta` 下载作为 V5 安装入口。

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

兼容性处理限制在 CLI 与配置加载边界；进入核心后，Provider 使用
`ProviderId` 枚举，别名只解析一次。Provider 通过 trait object 做运行时分发，
借用同步 HTTP 客户端；单次更新请求借用域名、地址和 Provider 扩展配置，避免
为每个域名复制整份配置。Provider 特有的 `extra` 仍保留动态 JSON 值，因为其
字段由各 DNS API 定义。

Cloudflare 和腾讯云查询用 `Result<Option<_>>` 区分记录不存在与请求失败；只有正常空列表或已知的
查询未命中错误码才允许继续查找或创建。Cloudflare 和腾讯云写入响应必须包含
有效的结果标识，畸形响应不会被当作成功写入缓存。腾讯云的 DNSPod、EdgeOne
加速和 EdgeOne DNS 模式由枚举确定服务与 API 版本，避免自由组合字符串和布尔状态。

DNSPod 中国版和国际版在标准写入参数之后合并 `extra`，保留其覆盖优先级。
IP 文本提取使用标准库 `IpAddr` 校验完整地址，支持 `IP:2001:db8::1`、
`address:192.0.2.1` 等紧凑文本标签；无效 IPv6 不会被截断成可用片段。

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
- 诊断中的 URL 会隐藏用户信息、非根路径、查询值与片段，避免 Callback 或远程配置的路径凭据泄漏；实际发送的 URL 不变。

## 后续顺序

1. 迁移 systemd、cron、launchd、schtasks。
2. 迁移 Web 控制台与 MCP。
3. 达到完整等价并稳定运行后再讨论改名为 `ddns`。

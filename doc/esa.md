# ESA 代理脚本 / ESA Proxy Script

[English](#english) | [中文](#中文)

---

## 中文

### 简介

`esa.js` 是一个用于边缘计算平台（如 Cloudflare Workers）的 GitHub Release 代理脚本。它可以自动代理 DDNS 项目的二进制文件下载请求到 GitHub Releases，并实现智能缓存策略。

### 功能特性

- 🚀 **版本化发布代理**: 将 `/releases/{version}/{binary}` 请求代理到 GitHub Releases
- 📦 **最新版本代理**: 将 `/latest/{binary}` 请求代理到 GitHub Releases 最新版本
- ⚡ **智能缓存**:
  - 版本化发布：无限 TTL（不可变内容）
  - 最新版本：12 小时缓存
- 🔍 **缓存状态透明**: 通过 `X-Cache` 和 `X-Cache-Type` 响应头查看缓存状态

### 使用方法

#### 1. 部署到 Cloudflare Workers

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 选择 **Workers & Pages** → **Create application** → **Create Worker**
3. 将 `esa.js` 的内容复制到编辑器中
4. 点击 **Save and Deploy**
5. 配置路由规则（可选）：
   - 进入你的域名设置
   - 添加 Worker 路由：`your-domain.com/releases/*` 和 `your-domain.com/latest/*`

#### 2. 使用示例

部署完成后，您可以通过以下 URL 格式访问：

```bash
# 版本化发布（永久缓存）
https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
https://your-domain.com/releases/v4.1.2/ddns-glibc-linux_amd64

# 最新版本（12 小时缓存）
https://your-domain.com/latest/ddns-windows-x64.exe
https://your-domain.com/latest/ddns-mac-arm64
```

#### 3. URL 映射规则

| 请求路径 | GitHub URL | 缓存策略 |
|---------|-----------|---------|
| `/releases/v4.1.3-beta1/ddns.exe` | `https://github.com/NewFuture/DDNS/releases/download/v4.1.3-beta1/ddns.exe` | 无限 TTL |
| `/latest/ddns-linux-x64` | `https://github.com/NewFuture/DDNS/releases/latest/download/ddns-linux-x64` | 12 小时 |

### 响应头说明

脚本会在响应中添加以下自定义头：

- `X-Cache`: 缓存状态（`HIT` 或 `MISS`）
- `X-Cache-Type`: 缓存类型（`versioned` 或 `latest`）
- `X-Cache-Time`: 缓存时间戳（仅限 `latest`）
- `X-GitHub-URL`: 原始 GitHub URL
- `Age`: 缓存年龄（秒，仅限 `latest` 缓存命中）

### 配置说明

如果需要修改代理的仓库，请编辑脚本中的 `GITHUB_REPO` 常量：

```javascript
const GITHUB_REPO = 'NewFuture/DDNS';  // 修改为你的仓库
```

### 技术细节

- **缓存键**: 使用 GitHub URL 作为缓存键，确保不同版本和文件分别缓存
- **版本化缓存**: 使用 `Cache-Control: public, max-age=31536000, immutable` 实现永久缓存
- **最新版本缓存**: 使用 `Cache-Control: public, max-age=43200`（12 小时）
- **缓存验证**: 通过 `X-Cache-Time` 头实现精确的缓存时效控制

---

## English

### Introduction

`esa.js` is a GitHub Release proxy script for edge computing platforms (such as Cloudflare Workers). It automatically proxies DDNS project binary download requests to GitHub Releases with intelligent caching strategies.

### Features

- 🚀 **Versioned Release Proxy**: Proxy `/releases/{version}/{binary}` requests to GitHub Releases
- 📦 **Latest Release Proxy**: Proxy `/latest/{binary}` requests to latest GitHub Release
- ⚡ **Smart Caching**:
  - Versioned releases: Infinite TTL (immutable content)
  - Latest version: 12-hour cache
- 🔍 **Cache Transparency**: View cache status via `X-Cache` and `X-Cache-Type` response headers

### Usage

#### 1. Deploy to Cloudflare Workers

1. Login to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select **Workers & Pages** → **Create application** → **Create Worker**
3. Copy the contents of `esa.js` into the editor
4. Click **Save and Deploy**
5. Configure route patterns (optional):
   - Go to your domain settings
   - Add Worker routes: `your-domain.com/releases/*` and `your-domain.com/latest/*`

#### 2. Usage Examples

After deployment, you can access via these URL formats:

```bash
# Versioned releases (permanent cache)
https://your-domain.com/releases/v4.1.3-beta1/ddns-windows-x64.exe
https://your-domain.com/releases/v4.1.2/ddns-glibc-linux_amd64

# Latest version (12-hour cache)
https://your-domain.com/latest/ddns-windows-x64.exe
https://your-domain.com/latest/ddns-mac-arm64
```

#### 3. URL Mapping Rules

| Request Path | GitHub URL | Cache Policy |
|-------------|-----------|-------------|
| `/releases/v4.1.3-beta1/ddns.exe` | `https://github.com/NewFuture/DDNS/releases/download/v4.1.3-beta1/ddns.exe` | Infinite TTL |
| `/latest/ddns-linux-x64` | `https://github.com/NewFuture/DDNS/releases/latest/download/ddns-linux-x64` | 12 hours |

### Response Headers

The script adds the following custom headers to responses:

- `X-Cache`: Cache status (`HIT` or `MISS`)
- `X-Cache-Type`: Cache type (`versioned` or `latest`)
- `X-Cache-Time`: Cache timestamp (for `latest` only)
- `X-GitHub-URL`: Original GitHub URL
- `Age`: Cache age in seconds (for `latest` cache hits only)

### Configuration

To proxy a different repository, edit the `GITHUB_REPO` constant in the script:

```javascript
const GITHUB_REPO = 'NewFuture/DDNS';  // Change to your repository
```

### Technical Details

- **Cache Key**: Uses GitHub URL as cache key to ensure separate caching for different versions and files
- **Versioned Cache**: Uses `Cache-Control: public, max-age=31536000, immutable` for permanent caching
- **Latest Cache**: Uses `Cache-Control: public, max-age=43200` (12 hours)
- **Cache Validation**: Implements precise cache expiration control via `X-Cache-Time` header

### Compatibility

This script is designed for:
- ✅ Cloudflare Workers
- ✅ Compatible edge computing platforms supporting Service Worker API
- ✅ Platforms with Cache API support

### Performance

- **Cold start**: ~50-100ms (first request)
- **Cache hit**: <10ms (subsequent requests)
- **Cache miss**: Depends on GitHub API response time + caching overhead (~200-500ms)

### Troubleshooting

**Q: Getting 404 errors?**
- Verify the version tag exists in GitHub Releases
- Check the binary filename matches exactly (case-sensitive)

**Q: Cache not working?**
- Check if your edge platform supports Cache API
- Verify `event.waitUntil()` is supported

**Q: Latest release not updating?**
- Wait for the 12-hour cache TTL to expire
- Or purge the cache manually in your platform dashboard

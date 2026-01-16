# 使用阿里云 ESA Pages 和边缘函数部署文档

本文档介绍如何使用阿里云边缘安全加速（ESA）的 Pages 服务和边缘函数（Edge Function）来构建和部署 DDNS 文档站点。

## 概述

阿里云 ESA Pages 是类似于 Cloudflare Pages、Vercel 的静态站点托管服务，提供：

- **静态网站托管**：自动构建和部署 VitePress 文档
- **边缘函数**：在边缘节点运行 JavaScript 代码，处理动态请求
- **全球加速**：通过全球边缘节点加速内容分发
- **自动 HTTPS**：免费 SSL/TLS 证书
- **自定义域名**：支持绑定自定义域名

## 前提条件

1. **阿里云账号**：需要拥有阿里云账号并开通 ESA 服务
   - 注册地址：<https://www.aliyun.com/>
   - ESA 控制台：<https://esa.console.aliyun.com/>
   - 免费试用：<https://tianchi.aliyun.com/specials/promotion/freetier/esa>

2. **GitHub 仓库**：DDNS 项目需要托管在 GitHub 上
   - 项目地址：<https://github.com/NewFuture/DDNS>

3. **域名（可选）**：如需使用自定义域名，需要将域名接入 ESA

## 部署步骤

### 第一步：创建 ESA Pages 项目

1. 登录 [阿里云 ESA 控制台](https://esa.console.aliyun.com/)

2. 在左侧导航栏选择 **"Pages"**

3. 点击 **"创建项目"** 按钮

4. 配置项目基本信息：
   - **项目名称**：`ddns-docs`（可自定义）
   - **连接 GitHub**：授权 ESA 访问您的 GitHub 账号
   - **选择仓库**：`NewFuture/DDNS`
   - **选择分支**：`master`（或您的部署分支）

### 第二步：配置构建设置

在项目构建配置中，ESA Pages 会自动检测并读取 `docs/esa.jsonc` 文件中的配置。

项目中已包含 `docs/esa.jsonc` 配置文件：

```jsonc
{
  "name": "ddns",
  "entry": "esa.js",                    // 边缘函数入口文件
  "installCommand": "npm install",       // 安装依赖命令
  "buildCommand": "npm run build",       // 构建命令
  "assets": {
    "directory": ".vitepress/dist",     // 静态资源目录
    "notFoundStrategy": "404Page"       // 404 页面策略
  }
}
```

**配置说明**：

| 配置项 | 说明 | 值 |
|--------|------|-----|
| `name` | 项目名称 | `ddns` |
| `entry` | 边缘函数入口文件 | `esa.js`（可选，用于高级功能） |
| `installCommand` | 安装依赖命令 | `npm install` |
| `buildCommand` | 构建命令 | `npm run build` |
| `assets.directory` | 构建输出目录 | `.vitepress/dist` |
| `assets.notFoundStrategy` | 404 处理策略 | `404Page` |

::: tip
ESA Pages 会自动检测并应用 `esa.jsonc` 配置，无需手动配置构建参数。
:::

### 第三步：部署边缘函数（可选）

DDNS 项目包含一个边缘函数 `docs/esa.js`，用于实现以下功能：

1. **Release 代理**：统一格式代理 GitHub Releases 文件
   - 支持 `/releases/latest/`、`/releases/beta/`、`/releases/v4.1.3/` 等路径
   - 自动缓存和流式传输

2. **URL 重定向**：处理旧版文档 URL 的重定向
   - `/doc/*` → `/` （301 重定向）
   - `/index.en.html` → `/en/` （301 重定向）
   - `/doc/*.en.html` → `/en/*.html` （301 重定向）

#### 边缘函数部署步骤

边缘函数会随 Pages 项目自动部署，但需要进行以下配置：

1. **创建 EdgeKV 命名空间**（用于缓存 beta 版本信息）：
   - 在 ESA 控制台选择 **"EdgeKV"**
   - 点击 **"创建命名空间"**
   - 命名空间名称：`ddns-releases`

2. **配置路由规则**：
   - 在 Pages 项目设置中，边缘函数会自动绑定
   - 确认路由规则包含 `/releases/*` 和其他需要处理的路径

3. **验证功能**：
   ```bash
   # 测试 release 代理
   curl -I https://your-domain.com/releases/latest/ddns-windows-x64.exe
   
   # 测试重定向
   curl -I https://your-domain.com/doc/install.html
   ```

::: warning
边缘函数使用了 EdgeKV 存储 beta 版本映射，需要确保 EdgeKV 命名空间 `ddns-releases` 已创建并且项目有访问权限。
:::

### 第四步：绑定自定义域名（可选）

1. 在 ESA 控制台的 **"站点"** 中添加您的域名

2. 按照提示完成域名验证（DNS 验证或文件验证）

3. 在 Pages 项目设置中绑定自定义域名：
   - 点击 **"自定义域名"**
   - 输入域名：`ddns.newfuture.cc`
   - 选择已接入的站点
   - 保存配置

4. 等待域名解析生效（通常几分钟内完成）

### 第五步：配置构建触发器

ESA Pages 支持以下触发方式：

1. **Git Push 触发**（推荐）：
   - 默认启用
   - 每次推送代码到配置的分支时自动构建

2. **手动触发**：
   - 在 Pages 项目页面点击 **"立即构建"**

3. **定时构建**（可选）：
   - 在项目设置中配置定时构建规则

## 构建和部署流程

### 构建流程

当代码推送到 GitHub 后，ESA Pages 会自动执行以下步骤：

```bash
# 1. 切换到文档目录
cd docs

# 2. 安装依赖（由 esa.jsonc 的 installCommand 配置）
npm install

# 3. 构建文档（由 esa.jsonc 的 buildCommand 配置）
npm run build
# 实际执行: vitepress build .

# 4. 部署静态文件（从 .vitepress/dist 目录）
```

### VitePress 构建说明

DDNS 文档使用 VitePress 2.0 构建，构建过程包括：

1. **预处理**：
   - 复制 `README.md` → `docs/index.md`
   - 复制 `README.en.md` → `docs/en/index.md`
   - 通过符号链接访问 `schema/` 目录

2. **构建静态站点**：
   - 编译 Markdown 为 HTML
   - 生成 sitemap.xml
   - 生成 llms.txt（AI 上下文文件）
   - 优化资源文件

3. **输出**：
   - 输出到 `docs/.vitepress/dist/` 目录
   - 包含所有静态资源（HTML、CSS、JS、图片等）

## 高级配置

### 环境变量

如果需要在构建过程中使用环境变量，可以在 Pages 项目设置中添加：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `NODE_VERSION` | Node.js 版本 | `24` |
| `TZ` | 时区设置 | `Asia/Shanghai` |

ESA Pages 默认使用 Node.js 24，与项目的 GitHub Actions 配置保持一致。

## 边缘函数详解

### Release 代理功能

边缘函数 `esa.js` 实现了统一的 Release 文件访问格式：

```
/releases/{version}/{binary_file}
```

**支持的版本标识**：

- `latest`：最新稳定版
  - 示例：`/releases/latest/ddns-windows-x64.exe`
  - 缓存策略：12 小时缓存
  - 实际指向 GitHub 的 latest release

- `beta`：最新测试版
  - 示例：`/releases/beta/ddns-glibc-linux_amd64`
  - 缓存策略：转换为具体版本后无限缓存
  - 通过 GitHub API 动态查询最新 prerelease

- 具体版本号：
  - 示例：`/releases/v4.1.3-beta1/ddns-mac-arm64`
  - 缓存策略：无限缓存（immutable）
  - 直接指向 GitHub 对应版本

**工作原理**：

```javascript
// 1. 解析请求路径
/releases/{version}/{binary_file}

// 2. 根据版本类型构建 GitHub URL
// latest: https://github.com/NewFuture/DDNS/releases/latest/download/{binary_file}
// beta: 查询 GitHub API 获取最新 prerelease 版本号，转换为具体版本
// v4.1.3: https://github.com/NewFuture/DDNS/releases/download/v4.1.3/{binary_file}

// 3. 从 GitHub 获取文件，设置缓存策略
// 4. 流式传输给客户端
```

### URL 重定向功能

边缘函数处理旧版文档 URL 的 301 重定向：

| 旧 URL | 新 URL | 说明 |
|--------|--------|------|
| `/index.en.html` | `/en/` | 英文主页重定向 |
| `/doc/install.en.html` | `/en/install.html` | 英文文档重定向 |
| `/doc/install.html` | `/install.html` | 中文文档重定向 |
| `/doc/providers/dnspod.html` | `/providers/dnspod.html` | 所有文档路径去除 `/doc/` 前缀 |

### EdgeKV 使用

边缘函数使用 EdgeKV 存储 beta 版本映射，避免频繁调用 GitHub API：

```javascript
// 存储结构
{
  "ddns-beta-version": "v4.1.3-beta1"  // 缓存 6 小时
}
```

**优势**：

- 减少 GitHub API 调用次数
- 降低 API 速率限制风险
- 提高响应速度

## 监控和日志

### 构建日志

1. 在 Pages 项目页面查看 **"部署历史"**
2. 点击任意部署记录查看详细构建日志
3. 日志包含：
   - 依赖安装输出
   - VitePress 构建输出
   - 死链检查结果
   - 部署状态

### 边缘函数日志

1. 在 ESA 控制台选择 **"边缘函数"**
2. 选择对应的函数
3. 查看 **"实时日志"** 或 **"历史日志"**
4. 日志包含：
   - 请求路径和参数
   - EdgeKV 操作
   - GitHub API 调用
   - 错误信息

## 成本和限额

### ESA Pages 配额

根据阿里云 ESA 的定价策略：

- **免费额度**（新用户试用）：
  - 每月 100GB 流量
  - 1000 万次请求
  - 10 万次边缘函数调用

- **超出部分**：
  - 流量：按量计费
  - 请求：按量计费
  - 边缘函数：按调用次数计费

::: tip
DDNS 文档站点通常不会超过免费额度，适合长期使用。
:::

### EdgeKV 配额

- **命名空间**：每个账号最多 10 个
- **存储空间**：每个命名空间最大 1GB
- **操作次数**：每月 1000 万次读写操作（免费额度）

## 与 GitHub Actions 对比

DDNS 项目同时支持 GitHub Actions 和 ESA Pages 两种部署方式：

| 特性 | GitHub Actions + Pages | ESA Pages + Function |
|------|----------------------|----------------------|
| **构建速度** | 中等（取决于 GitHub 资源） | 快速（专用构建资源） |
| **全球加速** | GitHub CDN（国内访问较慢） | ESA 全球节点（国内优化） |
| **自定义域名** | 支持（需 DNS 配置） | 支持（集成管理） |
| **边缘函数** | 不支持 | 支持 |
| **成本** | 免费 | 有免费额度，超出按量计费 |
| **配置复杂度** | 中等（需配置 workflow） | 简单（自动检测配置） |

**选择建议**：

- **国际用户**：推荐 GitHub Pages（全球访问速度均衡）
- **国内用户**：推荐 ESA Pages（国内访问速度快）
- **需要边缘函数**：使用 ESA Pages（支持动态功能）

## 参考资源

- [阿里云 ESA 产品文档](https://help.aliyun.com/product/122312.html)
- [阿里云 ESA Pages 文档](https://help.aliyun.com/zh/edge-security-acceleration/esa/user-guide/pages-service-overview)
- [阿里云 ESA 边缘函数文档](https://help.aliyun.com/zh/edge-security-acceleration/esa/user-guide/edge-functions-overview)
- [VitePress 官方文档](https://vitepress.dev/)
- [DDNS GitHub 仓库](https://github.com/NewFuture/DDNS)

## 总结

通过阿里云 ESA Pages 和边缘函数，您可以：

1. ✅ 自动构建和部署 VitePress 文档
2. ✅ 使用边缘函数实现高级功能（Release 代理、URL 重定向）
3. ✅ 享受全球加速和免费 HTTPS
4. ✅ 绑定自定义域名
5. ✅ 监控站点性能和流量

ESA Pages 提供了一个简单、高效、可靠的文档部署方案，特别适合面向国内用户的项目。

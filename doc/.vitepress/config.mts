import { defineConfig } from 'vitepress'
import * as fs from 'fs'
import * as path from 'path'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "DDNS Documentation",
  description: "自动更新 DNS 解析到本机 IP 地址",
  
  // 站点配置
  base: '/',
  lang: 'zh-CN',
  lastUpdated: true,
  cleanUrls: true,
  
  // 启用死链接检查
  ignoreDeadLinks: false,
  
  // 生成站点地图
  sitemap: {
    hostname: 'https://ddns.newfuture.cc'
  },
  
  // 构建完成后生成 llms.txt
  buildEnd: async (siteConfig) => {
    const distPath = path.join(siteConfig.outDir, 'llms.txt')
    const content = `# DDNS Documentation - AI/LLM Context

> This file provides structured documentation for AI language models and assistants.

## Project Overview

**Name:** DDNS - Dynamic DNS Client
**Repository:** https://github.com/NewFuture/DDNS
**Documentation:** https://ddns.newfuture.cc
**License:** MIT

## Description

DDNS is a Python-based dynamic DNS client that automatically updates DNS records to match your current IP address. It supports multiple DNS providers including DNSPod, Cloudflare, AliDNS, and many others. The project supports both IPv4 and IPv6, and can be run via command line, Docker, or as a system service.

## Key Features

- Automatic IP detection (IPv4/IPv6)
- Multiple DNS provider support (20+ providers)
- Multiple configuration methods (CLI, Environment Variables, JSON)
- Docker support with multi-architecture images
- Python 2.7+ and 3.x compatible
- Standard library only (no external dependencies)

## Main Documentation Sections

- Homepage: /
- Installation: /install
- Docker Guide: /docker
- Configuration:
  - CLI Arguments: /config/cli
  - Environment Variables: /config/env
  - JSON Configuration: /config/json
- DNS Providers: /providers/
- Development Guide: /dev/provider

## Usage Examples

### Docker:
\`\`\`bash
docker run -it --rm -e DNS=dnspod -e ID=your_id -e TOKEN=your_token newfuture/ddns
\`\`\`

### Command Line:
\`\`\`bash
python3 run.py --dns dnspod --id your_id --token your_token
\`\`\`

### pip Install:
\`\`\`bash
pip install ddns
ddns --dns dnspod --id your_id --token your_token
\`\`\`

## Supported DNS Providers

DNSPod, Cloudflare, AliDNS (Alibaba Cloud), Tencent Cloud, Huawei Cloud, GoDaddy, Namecheap, CloudXNS, HE.net, DynDNS, and many more.

## Technical Details

- **Language:** Python 2.7+ and 3.x
- **Dependencies:** Standard library only
- **Platform:** Cross-platform (Windows, Linux, macOS)
- **Docker:** Multi-architecture support (amd64, arm64, arm/v7)

## Links

- GitHub: https://github.com/NewFuture/DDNS
- Documentation: https://ddns.newfuture.cc
- Docker Hub: https://hub.docker.com/r/newfuture/ddns
- PyPI: https://pypi.org/project/ddns/

---
Generated: ${new Date().toISOString()}
`
    fs.writeFileSync(distPath, content, 'utf-8')
    console.log('✓ Generated llms.txt')
  },
  
  // 主题配置
  themeConfig: {
    // Logo
    logo: '/img/ddns.svg',
    siteTitle: 'DDNS',
    
    // 导航栏
    nav: [
      { text: '首页', link: '/' },
      { text: 'Docker', link: '/docker' },
      { text: '安装', link: '/install' },
      { 
        text: '配置方式',
        items: [
          { text: '命令行参数', link: '/config/cli' },
          { text: '环境变量', link: '/config/env' },
          { text: 'JSON配置', link: '/config/json' }
        ]
      },
      {
        text: 'DNS服务商',
        items: [
          { text: '概述', link: '/providers/' },
          { text: '阿里DNS', link: '/providers/alidns' },
          { text: 'DNSPod', link: '/providers/dnspod' },
          { text: 'Cloudflare', link: '/providers/cloudflare' }
        ]
      },
      {
        text: '开发文档',
        items: [
          { text: '配置文档', link: '/dev/config' },
          { text: 'Provider开发', link: '/dev/provider' }
        ]
      }
    ],

    // 侧边栏
    sidebar: {
      '/config/': [
        {
          text: '配置方式',
          items: [
            { text: '命令行参数', link: '/config/cli' },
            { text: '环境变量', link: '/config/env' },
            { text: 'JSON配置文件', link: '/config/json' }
          ]
        }
      ],
      '/providers/': [
        {
          text: 'DNS 服务商',
          items: [
            { text: '所有服务商', link: '/providers/index' },
            { text: '阿里DNS', link: '/providers/alidns' },
            { text: '阿里云ESA', link: '/providers/aliesa' },
            { text: '51DNS', link: '/providers/51dns' },
            { text: 'Cloudflare', link: '/providers/cloudflare' },
            { text: 'DNSPod', link: '/providers/dnspod' },
            { text: 'DNSPod国际版', link: '/providers/dnspod_com' },
            { text: '腾讯云DNS', link: '/providers/tencentcloud' },
            { text: '腾讯云EdgeOne', link: '/providers/edgeone' },
            { text: '华为云DNS', link: '/providers/huaweidns' },
            { text: 'HE.net', link: '/providers/he' },
            { text: 'NameSilo', link: '/providers/namesilo' },
            { text: 'No-IP', link: '/providers/noip' },
            { text: '回调API', link: '/providers/callback' },
            { text: '调试模式', link: '/providers/debug' }
          ]
        }
      ],
      '/dev/': [
        {
          text: '开发文档',
          items: [
            { text: '配置文档', link: '/dev/config' },
            { text: 'Provider开发指南', link: '/dev/provider' }
          ]
        }
      ]
    },

    // 编辑链接 - 修复 README.md -> index.html 的映射
    editLink: {
      pattern: ({ filePath }) => {
        // 特殊处理：index.md 实际对应 README.md
        if (filePath === 'index.md') {
          return 'https://github.com/NewFuture/DDNS/edit/master/README.md';
        }
        if (filePath === 'en/index.md') {
          return 'https://github.com/NewFuture/DDNS/edit/master/README.en.md';
        }
        // 其他文件：移除 en/ 前缀，添加 doc/ 前缀
        const cleanPath = filePath.replace(/^en\//, '');
        return `https://github.com/NewFuture/DDNS/edit/master/doc/${cleanPath}`;
      },
      text: '在 GitHub 上编辑此页'
    },

    // 最后更新时间
    lastUpdated: {
      text: '最后更新时间',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'short'
      }
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/NewFuture/DDNS' }
    ],

    // 页脚
    footer: {
      message: 'Released under the MIT License',
      copyright: `Copyright © 2016 ~ ${new Date().getFullYear()} NewFuture`
    },

    // 搜索
    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: '搜索文档',
                buttonAriaLabel: '搜索文档'
              },
              modal: {
                noResultsText: '无法找到相关结果',
                resetButtonTitle: '清除查询条件',
                footer: {
                  selectText: '选择',
                  navigateText: '切换'
                }
              }
            }
          }
        }
      }
    },

    // 大纲配置
    outline: {
      level: [2, 3],
      label: '页面导航'
    },

    // 文档页脚
    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    // 返回顶部
    returnToTopLabel: '返回顶部',
    
    // 侧边栏菜单标签
    sidebarMenuLabel: '菜单',
    
    // 深色模式开关标签
    darkModeSwitchLabel: '主题',
    
    // 浅色模式开关标题
    lightModeSwitchTitle: '切换到浅色模式',
    
    // 深色模式开关标题
    darkModeSwitchTitle: '切换到深色模式'
  },

  // Markdown 配置
  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    config: (md) => {
      // Transform code links like /ddns/provider/dnspod.py to GitHub links
      md.core.ruler.after('inline', 'transform-code-links', (state) => {
        const tokens = state.tokens;
        for (let i = 0; i < tokens.length; i++) {
          if (tokens[i].type === 'inline' && tokens[i].children) {
            const children = tokens[i].children;
            for (let j = 0; j < children.length; j++) {
              if (children[j].type === 'code_inline') {
                const content = children[j].content;
                // Match paths like /ddns/xxx.py or /ddns/xxx/yyy.py
                if (content.match(/^\/ddns\/[a-zA-Z0-9_/.-]+\.(py|md|json|sh|txt)$/)) {
                  // Convert to link token
                  const linkToken = new state.Token('link_open', 'a', 1);
                  linkToken.attrs = [['href', `https://github.com/NewFuture/DDNS/blob/master${content}`], ['target', '_blank']];
                  
                  const textToken = new state.Token('text', '', 0);
                  textToken.content = content;
                  
                  const closeLinkToken = new state.Token('link_close', 'a', -1);
                  
                  // Replace code token with link tokens
                  children.splice(j, 1, linkToken, textToken, closeLinkToken);
                  j += 2; // Skip the newly added tokens
                }
              }
            }
          }
        }
      });
    }
  },

  // 多语言支持
  locales: {
    root: {
      label: '简体中文',
      lang: 'zh-CN'
    },
    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/',
      themeConfig: {
        nav: [
          { text: 'Home', link: '/en/' },
          { text: 'Docker', link: '/en/docker' },
          { text: 'Install', link: '/en/install' },
          { 
            text: 'Configuration',
            items: [
              { text: 'CLI', link: '/en/config/cli' },
              { text: 'Environment', link: '/en/config/env' },
              { text: 'JSON Config', link: '/en/config/json' }
            ]
          },
          {
            text: 'DNS Providers',
            items: [
              { text: 'Overview', link: '/en/providers/' },
              { text: 'AliDNS', link: '/en/providers/alidns' },
              { text: 'DNSPod', link: '/en/providers/dnspod' },
              { text: 'Cloudflare', link: '/en/providers/cloudflare' }
            ]
          },
          {
            text: 'Development',
            items: [
              { text: 'Config Docs', link: '/en/dev/config' },
              { text: 'Provider Guide', link: '/en/dev/provider' }
            ]
          }
        ],
        sidebar: {
          '/en/config/': [
            {
              text: 'Configuration',
              items: [
                { text: 'CLI Parameters', link: '/en/config/cli' },
                { text: 'Environment Variables', link: '/en/config/env' },
                { text: 'JSON Configuration', link: '/en/config/json' }
              ]
            }
          ],
          '/en/providers/': [
            {
              text: 'DNS Providers',
              items: [
                { text: 'Overview', link: '/en/providers/' },
                { text: 'AliDNS', link: '/en/providers/alidns' },
                { text: 'Ali ESA', link: '/en/providers/aliesa' },
                { text: '51DNS', link: '/en/providers/51dns' },
                { text: 'Cloudflare', link: '/en/providers/cloudflare' },
                { text: 'DNSPod', link: '/en/providers/dnspod' },
                { text: 'DNSPod Global', link: '/en/providers/dnspod_com' },
                { text: 'Tencent Cloud DNS', link: '/en/providers/tencentcloud' },
                { text: 'Tencent Cloud EdgeOne', link: '/en/providers/edgeone' },
                { text: 'Huawei Cloud DNS', link: '/en/providers/huaweidns' },
                { text: 'HE.net', link: '/en/providers/he' },
                { text: 'NameSilo', link: '/en/providers/namesilo' },
                { text: 'No-IP', link: '/en/providers/noip' },
                { text: 'Callback API', link: '/en/providers/callback' },
                { text: 'Debug Mode', link: '/en/providers/debug' }
              ]
            }
          ],
          '/en/dev/': [
            {
              text: 'Development',
              items: [
                { text: 'Config Documentation', link: '/en/dev/config' },
                { text: 'Provider Development', link: '/en/dev/provider' }
              ]
            }
          ]
        },
        editLink: {
          pattern: ({ filePath }) => {
            // 特殊处理：index.md 实际对应 README.md
            if (filePath === 'index.md') {
              return 'https://github.com/NewFuture/DDNS/edit/master/README.md';
            }
            if (filePath === 'en/index.md') {
              return 'https://github.com/NewFuture/DDNS/edit/master/README.en.md';
            }
            // 其他文件：移除 en/ 前缀，添加 doc/ 前缀
            const cleanPath = filePath.replace(/^en\//, '');
            return `https://github.com/NewFuture/DDNS/edit/master/doc/${cleanPath}`;
          },
          text: 'Edit this page on GitHub'
        },
        lastUpdated: {
          text: 'Last updated',
          formatOptions: {
            dateStyle: 'short',
            timeStyle: 'short'
          }
        },
        footer: {
          message: 'Released under the MIT License',
          copyright: `Copyright © 2016 ~ ${new Date().getFullYear()} NewFuture`
        },
        outline: {
          label: 'On this page'
        },
        docFooter: {
          prev: 'Previous',
          next: 'Next'
        },
        returnToTopLabel: 'Return to top',
        sidebarMenuLabel: 'Menu',
        darkModeSwitchLabel: 'Appearance',
        lightModeSwitchTitle: 'Switch to light mode',
        darkModeSwitchTitle: 'Switch to dark mode'
      }
    }
  }
})

import { defineConfig } from 'vitepress'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '../..')
const configFieldModel = JSON.parse(
  fs.readFileSync(path.join(rootDir, 'ddns/config/field-model.json'), 'utf8')
)
const TERMINAL_CODE_LANGUAGES = new Set([
  'bash',
  'bat',
  'batch',
  'cmd',
  'console',
  'fish',
  'powershell',
  'ps1',
  'sh',
  'shell',
  'shellscript',
  'terminal',
  'zsh'
])

// Setup documentation structure before VitePress processes files
function setupDocs() {
  const docsDir = path.resolve(__dirname, '..')
  
  console.log('Setting up documentation structure...\n')
  
  // Process README files
  const processReadme = (sourcePath, targetPath, sourcePrefix, sitePrefix) => {
    if (!fs.existsSync(sourcePath)) return false
    
    const content = fs.readFileSync(sourcePath, 'utf8')
    const escapedPrefix = sourcePrefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const rawFileLink = new RegExp(
      `href="${escapedPrefix}([^"#]+?)\\.md(#[^"]*)?"`,
      'g'
    )
    const modifiedContent = content
      .replace(new RegExp(`\\(${escapedPrefix}`, 'g'), `(${sitePrefix}`)
      .replace(
        rawFileLink,
        (_match, relativePath, hash = '') =>
          `href="${sitePrefix}${relativePath}${hash}"`
      )
      .replace(new RegExp(`href="${escapedPrefix}`, 'g'), `href="${sitePrefix}`)
      .replace(/src="docs\/public\//g, 'src="/')
    
    const targetDir = path.dirname(targetPath)
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true })
    }
    
    fs.writeFileSync(targetPath, modifiedContent)
    return true
  }
  
  // Copy README.md as docs/index.md (Chinese)
  if (processReadme(
    path.join(rootDir, 'README.md'),
    path.join(docsDir, 'index.md'),
    'docs/',
    '/'
  )) {
    console.log('✓ Copied README.md to docs/index.md')
  }
  
  // Copy README.en.md as docs/en/index.md (English)
  if (processReadme(
    path.join(rootDir, 'README.en.md'),
    path.join(docsDir, 'en', 'index.md'),
    'docs/en/',
    '/en/'
  )) {
    console.log('✓ Copied README.en.md to docs/en/index.md')
  }
  
  // Note: schema/ and tests/ are available via symbolic links in docs/public/
  // No need to copy them as they're linked directly
  
  console.log('\nDocumentation structure setup complete!\n')
}

// Run setup before exporting config
setupDocs()

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
  
  // URL rewrites to handle /providers/index -> /providers/
  rewrites: {
    'providers/README.md': 'providers/index.md',
    'en/providers/README.md': 'en/providers/index.md'
  },
  
  // 生成站点地图
  sitemap: {
    hostname: 'https://ddns.newfuture.cc'
  },
  
  // 构建完成后生成 llms.txt (从模板文件) 并复制 markdown 文件
  buildEnd: async (siteConfig) => {
    const templatePath = path.resolve(__dirname, '../llms.txt')
    const distPath = path.join(siteConfig.outDir, 'llms.txt')
    
    // Read template and replace variables
    let content = fs.readFileSync(templatePath, 'utf-8')
    content = content.replace('{{DATE}}', new Date().toISOString().split('T')[0])
    
    fs.writeFileSync(distPath, content, 'utf-8')
    console.log('✓ Generated llms.txt from template')
    
    // 复制所有 markdown 文件到构建输出目录
    const docsDir = path.resolve(__dirname, '..')
    const outDir = siteConfig.outDir
    
    function copyMarkdownFiles(srcDir, destDir, relativePath = '') {
      const entries = fs.readdirSync(srcDir, { withFileTypes: true })
      
      for (const entry of entries) {
        const srcPath = path.join(srcDir, entry.name)
        const destPath = path.join(destDir, entry.name)
        const relPath = relativePath ? `${relativePath}/${entry.name}` : entry.name
        
        // 跳过特殊目录
        if (entry.isDirectory()) {
          if (entry.name === '.vitepress' || entry.name === 'node_modules' || entry.name === 'public') {
            continue
          }
          // 递归处理子目录
          if (!fs.existsSync(destPath)) {
            fs.mkdirSync(destPath, { recursive: true })
          }
          copyMarkdownFiles(srcPath, destPath, relPath)
        } else if (entry.isFile() && entry.name.endsWith('.md')) {
          // 复制 markdown 文件
          fs.copyFileSync(srcPath, destPath)
          console.log(`  ✓ Copied ${relPath}`)
        }
      }
    }
    
    console.log('\nCopying markdown files to build output...')
    copyMarkdownFiles(docsDir, outDir)
    console.log('✓ All markdown files copied\n')
  },
  
  // 主题配置
  themeConfig: {
    // Logo
    logo: '/img/ddns.svg',
    siteTitle: 'DDNS',
    
    // 导航栏
    nav: [
      {
        text: '开始使用',
        items: [
          { text: '选择安装方式', link: '/install' },
          { text: 'Docker 部署', link: '/docker' }
        ]
      },
      {
        text: '配置',
        items: [
          { text: '生成与校验', link: '/config/studio' },
          { text: 'JSON 配置', link: '/config/json' },
          { text: '命令行参数', link: '/config/cli' },
          { text: 'MCP 服务', link: '/config/mcp' },
          { text: '环境变量', link: '/config/env' }
        ]
      },
      {
        text: 'DNS 服务商',
        items: [
          { text: '所有服务商', link: '/providers/' },
          {
            text: '国内与云平台',
            items: [
              { text: '阿里云 DNS', link: '/providers/alidns' },
              { text: '阿里云 ESA', link: '/providers/aliesa' },
              { text: '51DNS', link: '/providers/51dns' },
              { text: 'DNSPod', link: '/providers/dnspod' },
              { text: '腾讯云 DNS', link: '/providers/tencentcloud' },
              { text: 'EdgeOne 加速', link: '/providers/edgeone' },
              { text: 'EdgeOne DNS', link: '/providers/edgeone_dns' },
              { text: '华为云 DNS', link: '/providers/huaweidns' },
              { text: '西部数码', link: '/providers/west' }
            ]
          },
          {
            text: '国际服务商',
            items: [
              { text: 'Cloudflare', link: '/providers/cloudflare' },
              { text: 'ClouDNS', link: '/providers/cloudns' },
              { text: 'DNSPod Global', link: '/providers/dnspod_com' },
              { text: 'HE.net', link: '/providers/he' },
              { text: 'NameSilo', link: '/providers/namesilo' },
              { text: 'No-IP', link: '/providers/noip' }
            ]
          },
          {
            text: '集成与调试',
            items: [
              { text: 'Callback API', link: '/providers/callback' },
              { text: 'Debug', link: '/providers/debug' }
            ]
          }
        ]
      },
      {
        text: '开发',
        items: [
          { text: '配置系统设计', link: '/dev/config' },
          { text: 'Provider 开发', link: '/dev/provider' },
          { text: 'Rust 客户端', link: '/dev/rust' },
          { text: 'ESA Pages 部署', link: '/esa-deploy' }
        ]
      }
    ],

    // 侧边栏
    sidebar: {
      '/config/': [
        {
          text: '配置方式',
          items: [
            { text: '配置生成与校验', link: '/config/studio' },
            { text: '命令行参数', link: '/config/cli' },
            { text: 'MCP 服务', link: '/config/mcp' },
            { text: '环境变量', link: '/config/env' },
            { text: 'JSON配置文件', link: '/config/json' }
          ]
        }
      ],
      '/providers/': [
        {
          text: '服务商概览',
          items: [
            { text: '所有服务商', link: '/providers/' }
          ]
        },
        {
          text: '国内与云平台',
          collapsed: true,
          items: [
            { text: '阿里DNS', link: '/providers/alidns' },
            { text: '阿里云ESA', link: '/providers/aliesa' },
            { text: '51DNS', link: '/providers/51dns' },
            { text: 'DNSPod', link: '/providers/dnspod' },
            { text: '腾讯云DNS', link: '/providers/tencentcloud' },
            { text: '腾讯云EdgeOne', link: '/providers/edgeone' },
            { text: '腾讯云EdgeOne DNS', link: '/providers/edgeone_dns' },
            { text: '华为云DNS', link: '/providers/huaweidns' },
            { text: '西部数码', link: '/providers/west' }
          ]
        },
        {
          text: '国际服务商',
          collapsed: true,
          items: [
            { text: 'Cloudflare', link: '/providers/cloudflare' },
            { text: 'ClouDNS', link: '/providers/cloudns' },
            { text: 'DNSPod国际版', link: '/providers/dnspod_com' },
            { text: 'HE.net', link: '/providers/he' },
            { text: 'NameSilo', link: '/providers/namesilo' },
            { text: 'No-IP', link: '/providers/noip' }
          ]
        },
        {
          text: '集成与验证',
          collapsed: true,
          items: [
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
            { text: 'Provider开发指南', link: '/dev/provider' },
            { text: 'Rust 客户端', link: '/dev/rust' }
          ]
        },
        {
          text: '部署文档',
          items: [
            { text: 'ESA Pages部署', link: '/esa-deploy' }
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
        // 其他文件：映射到 docs/ 目录
        return `https://github.com/NewFuture/DDNS/edit/master/docs/${filePath}`;
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
      // Command snippets are copied or executed as a unit, so line numbers add noise.
      md.core.ruler.after('inline', 'disable-terminal-line-numbers', (state) => {
        for (const token of state.tokens) {
          if (token.type !== 'fence') continue
          const language = token.info
            .trim()
            .match(/^([^\s:{]+)/)?.[1]
            ?.toLowerCase()
          if (
            language &&
            TERMINAL_CODE_LANGUAGES.has(language) &&
            !/:no-line-numbers\b/.test(token.info)
          ) {
            token.info = `${token.info.trimEnd()} :no-line-numbers`
          }
        }
      })

      // Transform link hrefs that point to code files to GitHub blob URLs
      md.core.ruler.after('inline', 'transform-code-links', (state) => {
        const tokens = state.tokens;
        for (let i = 0; i < tokens.length; i++) {
          if (tokens[i].type === 'inline' && tokens[i].children) {
            const children = tokens[i].children;
            for (let j = 0; j < children.length; j++) {
              if (children[j].type === 'link_open') {
                const attrs = children[j].attrs || [];
                for (let k = 0; k < attrs.length; k++) {
                  if (attrs[k][0] === 'href') {
                    const href = attrs[k][1];
                    if (href.match(/^\/(ddns|docker|tests)\/.+(py|json|sh|txt|Dockerfile)$/)) {
                      attrs[k][1] = `https://github.com/NewFuture/DDNS/blob/master${href}`;
                      // Add target="_blank" if not present
                      const hasTarget = attrs.some(attr => attr[0] === 'target');
                      if (!hasTarget) {
                        attrs.push(['target', '_blank']);
                      }
                    }
                  }
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
          {
            text: 'Get Started',
            items: [
              { text: 'Choose an Installation', link: '/en/install' },
              { text: 'Deploy with Docker', link: '/en/docker' }
            ]
          },
          {
            text: 'Configure',
            items: [
              { text: 'Build & Validate', link: '/en/config/studio' },
              { text: 'JSON Configuration', link: '/en/config/json' },
              { text: 'CLI', link: '/en/config/cli' },
              { text: 'MCP Server', link: '/en/config/mcp' },
              { text: 'Environment', link: '/en/config/env' }
            ]
          },
          {
            text: 'DNS Providers',
            items: [
              { text: 'Overview', link: '/en/providers/' },
              {
                text: 'China & Cloud',
                items: [
                  { text: 'AliDNS', link: '/en/providers/alidns' },
                  { text: 'Alibaba Cloud ESA', link: '/en/providers/aliesa' },
                  { text: '51DNS', link: '/en/providers/51dns' },
                  { text: 'DNSPod China', link: '/en/providers/dnspod' },
                  { text: 'Tencent Cloud DNS', link: '/en/providers/tencentcloud' },
                  { text: 'EdgeOne Acceleration', link: '/en/providers/edgeone' },
                  { text: 'EdgeOne DNS', link: '/en/providers/edgeone_dns' },
                  { text: 'Huawei Cloud DNS', link: '/en/providers/huaweidns' },
                  { text: 'West.cn', link: '/en/providers/west' }
                ]
              },
              {
                text: 'International',
                items: [
                  { text: 'Cloudflare', link: '/en/providers/cloudflare' },
                  { text: 'ClouDNS', link: '/en/providers/cloudns' },
                  { text: 'DNSPod Global', link: '/en/providers/dnspod_com' },
                  { text: 'HE.net', link: '/en/providers/he' },
                  { text: 'NameSilo', link: '/en/providers/namesilo' },
                  { text: 'No-IP', link: '/en/providers/noip' }
                ]
              },
              {
                text: 'Integrations & Testing',
                items: [
                  { text: 'Callback API', link: '/en/providers/callback' },
                  { text: 'Debug Provider', link: '/en/providers/debug' }
                ]
              }
            ]
          },
          {
            text: 'Development',
            items: [
              { text: 'Configuration Internals', link: '/en/dev/config' },
              { text: 'Provider Development', link: '/en/dev/provider' },
              { text: 'Rust Client', link: '/en/dev/rust' }
            ]
          }
        ],
        sidebar: {
          '/en/config/': [
            {
              text: 'Configuration',
              items: [
                { text: 'Build & Validate', link: '/en/config/studio' },
                { text: 'CLI Parameters', link: '/en/config/cli' },
                { text: 'MCP Server', link: '/en/config/mcp' },
                { text: 'Environment Variables', link: '/en/config/env' },
                { text: 'JSON Configuration', link: '/en/config/json' }
              ]
            }
          ],
          '/en/providers/': [
            {
              text: 'Provider Overview',
              items: [
                { text: 'All Providers', link: '/en/providers/' }
              ]
            },
            {
              text: 'China & Cloud Platforms',
              collapsed: true,
              items: [
                { text: 'AliDNS', link: '/en/providers/alidns' },
                { text: 'Ali ESA', link: '/en/providers/aliesa' },
                { text: '51DNS', link: '/en/providers/51dns' },
                { text: 'DNSPod', link: '/en/providers/dnspod' },
                { text: 'Tencent Cloud DNS', link: '/en/providers/tencentcloud' },
                { text: 'Tencent Cloud EdgeOne', link: '/en/providers/edgeone' },
                { text: 'Tencent Cloud EdgeOne DNS', link: '/en/providers/edgeone_dns' },
                { text: 'Huawei Cloud DNS', link: '/en/providers/huaweidns' },
                { text: 'West.cn', link: '/en/providers/west' }
              ]
            },
            {
              text: 'International Providers',
              collapsed: true,
              items: [
                { text: 'Cloudflare', link: '/en/providers/cloudflare' },
                { text: 'ClouDNS', link: '/en/providers/cloudns' },
                { text: 'DNSPod Global', link: '/en/providers/dnspod_com' },
                { text: 'HE.net', link: '/en/providers/he' },
                { text: 'NameSilo', link: '/en/providers/namesilo' },
                { text: 'No-IP', link: '/en/providers/noip' }
              ]
            },
            {
              text: 'Integrations & Testing',
              collapsed: true,
              items: [
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
                { text: 'Provider Development', link: '/en/dev/provider' },
                { text: 'Rust Client', link: '/en/dev/rust' }
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
            // 其他文件：映射到 docs/ 目录
            return `https://github.com/NewFuture/DDNS/edit/master/docs/${filePath}`;
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
  },

  // Vite configuration for handling symbolic links
  vite: {
    define: {
      __DDNS_FIELD_MODEL__: JSON.stringify(configFieldModel)
    },
    resolve: {
      preserveSymlinks: true
    }
  }
})

import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "DDNS Documentation",
  description: "自动更新 DNS 解析到本机 IP 地址",
  
  // 站点配置
  base: '/',
  lang: 'zh-CN',
  lastUpdated: true,
  cleanUrls: true,
  
  // 忽略死链接检查
  ignoreDeadLinks: true,
  
  // 主题配置
  themeConfig: {
    // Logo
    logo: '/doc/img/ddns.svg',
    siteTitle: 'DDNS',
    
    // 导航栏
    nav: [
      { text: '首页', link: '/' },
      { text: 'Docker', link: '/doc/docker' },
      { text: '安装', link: '/doc/install' },
      { 
        text: '配置方式',
        items: [
          { text: '命令行参数', link: '/doc/config/cli' },
          { text: '环境变量', link: '/doc/config/env' },
          { text: 'JSON配置', link: '/doc/config/json' }
        ]
      },
      {
        text: 'DNS服务商',
        items: [
          { text: '概述', link: '/doc/providers/README' },
          { text: '阿里DNS', link: '/doc/providers/alidns' },
          { text: 'DNSPod', link: '/doc/providers/dnspod' },
          { text: 'Cloudflare', link: '/doc/providers/cloudflare' }
        ]
      },
      {
        text: '开发文档',
        items: [
          { text: '配置文档', link: '/doc/dev/config' },
          { text: 'Provider开发', link: '/doc/dev/provider' }
        ]
      }
    ],

    // 侧边栏
    sidebar: {
      '/doc/config/': [
        {
          text: '配置方式',
          items: [
            { text: '命令行参数', link: '/doc/config/cli' },
            { text: '环境变量', link: '/doc/config/env' },
            { text: 'JSON配置文件', link: '/doc/config/json' }
          ]
        }
      ],
      '/doc/providers/': [
        {
          text: 'DNS 服务商',
          items: [
            { text: '概述', link: '/doc/providers/README' },
            { text: '阿里DNS', link: '/doc/providers/alidns' },
            { text: '阿里云ESA', link: '/doc/providers/aliesa' },
            { text: '51DNS', link: '/doc/providers/51dns' },
            { text: 'Cloudflare', link: '/doc/providers/cloudflare' },
            { text: 'DNSPod', link: '/doc/providers/dnspod' },
            { text: 'DNSPod国际版', link: '/doc/providers/dnspod_com' },
            { text: '腾讯云DNS', link: '/doc/providers/tencentcloud' },
            { text: '腾讯云EdgeOne', link: '/doc/providers/edgeone' },
            { text: '华为云DNS', link: '/doc/providers/huaweidns' },
            { text: 'HE.net', link: '/doc/providers/he' },
            { text: 'NameSilo', link: '/doc/providers/namesilo' },
            { text: 'No-IP', link: '/doc/providers/noip' },
            { text: '回调API', link: '/doc/providers/callback' },
            { text: '调试模式', link: '/doc/providers/debug' }
          ]
        }
      ],
      '/doc/dev/': [
        {
          text: '开发文档',
          items: [
            { text: '配置文档', link: '/doc/dev/config' },
            { text: 'Provider开发指南', link: '/doc/dev/provider' }
          ]
        }
      ]
    },

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/NewFuture/DDNS/edit/master/:path',
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
      copyright: 'Copyright © 2024 NewFuture'
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
          { text: 'Docker', link: '/en/doc/docker' },
          { text: 'Install', link: '/en/doc/install' },
          { 
            text: 'Configuration',
            items: [
              { text: 'CLI', link: '/en/doc/config/cli' },
              { text: 'Environment', link: '/en/doc/config/env' },
              { text: 'JSON Config', link: '/en/doc/config/json' }
            ]
          },
          {
            text: 'DNS Providers',
            items: [
              { text: 'Overview', link: '/en/doc/providers/README' },
              { text: 'AliDNS', link: '/en/doc/providers/alidns' },
              { text: 'DNSPod', link: '/en/doc/providers/dnspod' },
              { text: 'Cloudflare', link: '/en/doc/providers/cloudflare' }
            ]
          },
          {
            text: 'Development',
            items: [
              { text: 'Config Docs', link: '/en/doc/dev/config' },
              { text: 'Provider Guide', link: '/en/doc/dev/provider' }
            ]
          }
        ],
        sidebar: {
          '/en/doc/config/': [
            {
              text: 'Configuration',
              items: [
                { text: 'CLI Parameters', link: '/en/doc/config/cli' },
                { text: 'Environment Variables', link: '/en/doc/config/env' },
                { text: 'JSON Configuration', link: '/en/doc/config/json' }
              ]
            }
          ],
          '/en/doc/providers/': [
            {
              text: 'DNS Providers',
              items: [
                { text: 'Overview', link: '/en/doc/providers/README' },
                { text: 'AliDNS', link: '/en/doc/providers/alidns' },
                { text: 'Ali ESA', link: '/en/doc/providers/aliesa' },
                { text: '51DNS', link: '/en/doc/providers/51dns' },
                { text: 'Cloudflare', link: '/en/doc/providers/cloudflare' },
                { text: 'DNSPod', link: '/en/doc/providers/dnspod' },
                { text: 'DNSPod Global', link: '/en/doc/providers/dnspod_com' },
                { text: 'Tencent Cloud DNS', link: '/en/doc/providers/tencentcloud' },
                { text: 'Tencent Cloud EdgeOne', link: '/en/doc/providers/edgeone' },
                { text: 'Huawei Cloud DNS', link: '/en/doc/providers/huaweidns' },
                { text: 'HE.net', link: '/en/doc/providers/he' },
                { text: 'NameSilo', link: '/en/doc/providers/namesilo' },
                { text: 'No-IP', link: '/en/doc/providers/noip' },
                { text: 'Callback API', link: '/en/doc/providers/callback' },
                { text: 'Debug Mode', link: '/en/doc/providers/debug' }
              ]
            }
          ],
          '/en/doc/dev/': [
            {
              text: 'Development',
              items: [
                { text: 'Config Documentation', link: '/en/doc/dev/config' },
                { text: 'Provider Development', link: '/en/doc/dev/provider' }
              ]
            }
          ]
        },
        editLink: {
          pattern: 'https://github.com/NewFuture/DDNS/edit/master/:path',
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
          copyright: 'Copyright © 2024 NewFuture'
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

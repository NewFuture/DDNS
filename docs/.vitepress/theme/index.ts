import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

const EN_BASE = '/en/'
const INDEX_HTML = 'index.html'

export default {
  extends: DefaultTheme,
  enhanceApp({ siteData }) {
    if (typeof window === 'undefined') return

    const { pathname, search, hash } = window.location
    const cleanUrls = !!siteData?.value?.cleanUrls
    const enBase =
      (siteData?.value?.locales?.en?.link || EN_BASE).replace(/\/?$/, '/')

    let target: string | null = null

    if (pathname === '/index.en.html') {
      target = enBase
    } else if (pathname === '/doc/') {
      target = '/'
    } else {
      const enDoc = pathname.match(/^\/doc\/(.+)\.en\.html$/)
      if (enDoc) {
        target = `${enBase}${enDoc[1]}.html`
      } else if (pathname.startsWith('/doc/')) {
        target = `/${pathname.slice('/doc/'.length)}`
      }
    }

    if (!target) return

    if (cleanUrls) {
      if (target === '/index.html') {
        target = '/'
      } else if (target === `/en/${INDEX_HTML}`) {
        target = '/en/'
      } else if (target.endsWith(`/${INDEX_HTML}`)) {
        target = target.slice(0, -INDEX_HTML.length)
      } else if (target.endsWith('.html')) {
        target = target.slice(0, -'.html'.length)
      }
    }

    const resolved = new URL(target + search + hash, window.location.origin)
    if (resolved.href !== window.location.href) {
      window.location.replace(resolved.href)
    }
  }
} satisfies Theme

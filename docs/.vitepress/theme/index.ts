import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

const EN_BASE = '/en/'
const DOC_PREFIX = '/doc/'
const EN_HTML_SUFFIX = '.en.html'
const HTML_EXT = '.html'

export default {
  extends: DefaultTheme,
  enhanceApp({ siteData }) {
    if (typeof window === 'undefined') return

    const { pathname, search, hash } = window.location
    const cleanUrls = !!siteData?.value?.cleanUrls
    const enLink = siteData?.value?.locales?.en?.link || EN_BASE
    const enBase = enLink.endsWith('/') ? enLink : `${enLink}/`

    let target: string | null = null
    if (pathname === '/index.en.html') {
      target = enBase
    } else if (pathname.startsWith(DOC_PREFIX)) {
      const rest = pathname.slice(DOC_PREFIX.length)
      if (!rest) {
        target = '/'
      } else if (rest.endsWith(EN_HTML_SUFFIX)) {
        target = `${enBase}${rest.slice(0, -EN_HTML_SUFFIX.length)}`
      } else {
        target = `/${rest}`
      }
    }

    // Apply clean URLs inline with target resolution
    if (target && cleanUrls && target.endsWith(HTML_EXT)) {
      target = target.slice(0, -HTML_EXT.length) || '/'
    }

    const resolved = new URL(target + search + hash, window.location.origin)
    if (resolved.href !== window.location.href) {
      window.location.replace(resolved.href)
    }
  }
} satisfies Theme

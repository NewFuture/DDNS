import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

const DOC_PREFIX = '/doc/'
const EN_BASE_DEFAULT = '/en/'

function applyCleanUrls(pathname: string, cleanUrls: boolean): string {
  if (!cleanUrls) {
    return pathname
  }

  if (pathname === '/index.html') {
    return '/'
  }

  if (pathname === '/en/index.html') {
    return '/en/'
  }

  if (pathname.endsWith('/index.html')) {
    return pathname.slice(0, -'index.html'.length)
  }

  if (pathname.endsWith('.html')) {
    return pathname.slice(0, -'.html'.length)
  }

  return pathname
}

function resolveLegacyRedirect(location: Location, cleanUrls: boolean, enBase?: string): string | null {
  const pathname = location.pathname
  const search = location.search || ''
  const hash = location.hash || ''
  const localeBase = (enBase || EN_BASE_DEFAULT).endsWith('/') ? (enBase || EN_BASE_DEFAULT) : `${enBase || EN_BASE_DEFAULT}/`

  if (pathname === '/index.en.html') {
    const target = applyCleanUrls(localeBase, cleanUrls)
    return target + search + hash
  }

  if (pathname.startsWith(DOC_PREFIX)) {
    const legacyPath = pathname.slice(DOC_PREFIX.length)
    if (!legacyPath) {
      // Legacy /doc/ root should land on the homepage
      const target = applyCleanUrls('/', cleanUrls)
      return target + search + hash
    }

    if (legacyPath.endsWith('.en.html')) {
      const pagePath = legacyPath.slice(0, -'.en.html'.length)
      const target = applyCleanUrls(`${localeBase}${pagePath}.html`, cleanUrls)
      return target + search + hash
    }

    const target = applyCleanUrls(`/${legacyPath}`, cleanUrls)
    return target + search + hash
  }

  return null
}

export default {
  extends: DefaultTheme,
  enhanceApp({ siteData }) {
    if (typeof window === 'undefined') {
      return
    }

    const localeBase = siteData?.value?.locales?.en?.link || EN_BASE_DEFAULT
    const cleanUrls = siteData?.value?.cleanUrls ?? false
    const redirect = resolveLegacyRedirect(window.location, cleanUrls, localeBase)

    if (!redirect) {
      return
    }

    const currentUrl = window.location.href
    const targetUrl = new URL(redirect, window.location.origin).href

    if (targetUrl !== currentUrl) {
      window.location.replace(targetUrl)
    }
  }
} satisfies Theme

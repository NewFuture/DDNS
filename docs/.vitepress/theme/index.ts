import DefaultTheme from 'vitepress/theme'
import { onContentUpdated, useRoute } from 'vitepress'
import type { Theme } from 'vitepress'
import { defineComponent, h, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import ConfigStudio from './components/ConfigStudio.vue'
import { installHistoryPositionTracking } from './history-position'
import './config-studio.css'
import './docs-layout.css'

const EN_BASE = '/en/'
const DOC_PREFIX = '/doc/'
const EN_HTML_SUFFIX = '.en.html'
const HTML_EXT = '.html'

function normalizePagePath(pathname: string): string {
  const withoutIndex = pathname.replace(/\/index(?:\.html)?$/, '/')
  const withoutHtml = withoutIndex.replace(/\.html$/, '')
  return withoutHtml.length > 1 ? withoutHtml.replace(/\/$/, '') : '/'
}

function syncNavigationSemantics() {
  if (typeof document === 'undefined') return
  const isEnglish =
    document.documentElement.lang.toLowerCase().startsWith('en') ||
    window.location.pathname.startsWith(EN_BASE)
  document
    .querySelector<HTMLButtonElement>('.VPNavBarHamburger')
    ?.setAttribute('aria-label', isEnglish ? 'Mobile navigation' : '移动导航')
  const sidebarLabel = document.querySelector<HTMLElement>('#sidebar-aria-label')
  if (sidebarLabel) {
    sidebarLabel.textContent = isEnglish ? 'Sidebar navigation' : '侧边栏导航'
  }
  document
    .querySelectorAll<HTMLElement>('.VPSidebar .caret[role="button"]')
    .forEach((toggle) => {
      const group = toggle.closest<HTMLElement>('.VPSidebarItem')
      const groupName =
        group
          ?.querySelector<HTMLElement>(':scope > .item > .text')
          ?.textContent?.trim() || (isEnglish ? 'section' : '分组')
      const isCollapsed = group?.classList.contains('collapsed')
      toggle.setAttribute(
        'aria-label',
        isEnglish
          ? `${isCollapsed ? 'Expand' : 'Collapse'} ${groupName}`
          : `${isCollapsed ? '展开' : '收起'}${groupName}`,
      )
    })

  const currentPath = normalizePagePath(window.location.pathname)
  document
    .querySelectorAll<HTMLAnchorElement>(
      '.VPSidebar a[href], .VPNavBarMenu a[href], .VPNavScreen a[href]',
    )
    .forEach((link) => {
      link.removeAttribute('aria-current')
      const target = new URL(link.href, window.location.href)
      if (
        target.origin === window.location.origin &&
        normalizePagePath(target.pathname) === currentPath
      ) {
        link.setAttribute('aria-current', 'page')
      }
    })
}

const AccessibleLayout = defineComponent({
  name: 'AccessibleLayout',
  setup() {
    const route = useRoute()
    let observedSidebar: HTMLElement | null = null
    let sidebarObserver: MutationObserver | undefined

    const syncSidebarInteraction = () => {
      const sidebar = document.querySelector<HTMLElement>('.VPSidebar')
      if (!sidebar) return
      const isMobile = window.matchMedia('(max-width: 959px)').matches
      sidebar.inert = isMobile && !sidebar.classList.contains('open')
    }

    const syncSidebarState = () => {
      syncSidebarInteraction()
      syncNavigationSemantics()
    }

    const handleSidebarTriggerClick = (event: MouseEvent) => {
      if (!(event.target instanceof Element)) return
      const trigger = event.target.closest<HTMLButtonElement>('.VPLocalNav .menu')
      if (
        !trigger ||
        trigger.getAttribute('aria-expanded') === 'true' ||
        !window.matchMedia('(max-width: 959px)').matches
      ) {
        return
      }

      const sidebar = document.querySelector<HTMLElement>('.VPSidebar')
      if (!sidebar) return
      sidebar.inert = false
      window.requestAnimationFrame(() => {
        if (!sidebar.classList.contains('open') || sidebar.contains(document.activeElement)) return
        const focusTarget =
          sidebar.querySelector<HTMLElement>('#VPSidebarNav') ||
          sidebar.querySelector<HTMLElement>('a[href], button:not([disabled])')
        if (!focusTarget) return
        if (!focusTarget.hasAttribute('tabindex')) focusTarget.tabIndex = -1
        focusTarget.focus()
      })
    }

    const observeSidebarInteraction = () => {
      const sidebar = document.querySelector<HTMLElement>('.VPSidebar')
      if (sidebar === observedSidebar) {
        syncSidebarInteraction()
        return
      }
      sidebarObserver?.disconnect()
      observedSidebar = sidebar
      if (sidebar) {
        sidebarObserver = new MutationObserver(syncSidebarState)
        sidebarObserver.observe(sidebar, {
          attributes: true,
          attributeFilter: ['class'],
          subtree: true,
        })
      }
      syncSidebarInteraction()
    }

    const syncAfterRender = () =>
      nextTick(() => {
        syncNavigationSemantics()
        observeSidebarInteraction()
      })

    const handleNavigationEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' || event.defaultPrevented) return

      const hamburger = document.querySelector<HTMLButtonElement>(
        '.VPNavBarHamburger[aria-expanded="true"]',
      )
      if (hamburger) {
        event.preventDefault()
        hamburger.click()
        void nextTick(() => hamburger.focus())
        return
      }

      const sidebar = document.querySelector<HTMLElement>('.VPSidebar.open')
      const sidebarTrigger = document.querySelector<HTMLButtonElement>(
        '.VPLocalNav .menu[aria-expanded="true"]',
      )
      const backdrop = document.querySelector<HTMLElement>('.VPBackdrop')
      if (!sidebar || !sidebarTrigger || !backdrop) return
      event.preventDefault()
      backdrop.click()
      void nextTick(() => sidebarTrigger.focus())
    }

    onMounted(syncAfterRender)
    onMounted(() => {
      document.addEventListener('click', handleSidebarTriggerClick, true)
      window.addEventListener('resize', syncSidebarInteraction, { passive: true })
      window.addEventListener('keydown', handleNavigationEscape)
    })
    onContentUpdated(syncAfterRender)
    watch(() => route.path, syncAfterRender, { flush: 'post' })
    onBeforeUnmount(() => {
      sidebarObserver?.disconnect()
      document.removeEventListener('click', handleSidebarTriggerClick, true)
      window.removeEventListener('resize', syncSidebarInteraction)
      window.removeEventListener('keydown', handleNavigationEscape)
    })
    return () => h(DefaultTheme.Layout)
  },
})

export default {
  extends: DefaultTheme,
  Layout: AccessibleLayout,
  enhanceApp({ app, siteData }) {
    app.component('ConfigStudio', ConfigStudio)
    if (typeof window === 'undefined') return
    installHistoryPositionTracking()

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
        target = `${enBase}${rest.slice(0, -EN_HTML_SUFFIX.length)}${cleanUrls ? "" : HTML_EXT}`
      } else if (cleanUrls && rest.endsWith(HTML_EXT)) {
        target = `/${rest.slice(0, -HTML_EXT.length)}` // Apply clean URLs
      } else {
        target = `/${rest}`
      }
    } else {
      return
    }

    const resolved = new URL(target + search + hash, window.location.origin)
    if (resolved.href !== window.location.href) {
      window.location.replace(resolved.href)
    }
  }
} satisfies Theme

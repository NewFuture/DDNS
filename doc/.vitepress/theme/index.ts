import DefaultTheme from 'vitepress/theme'
import { onMounted } from 'vue'
import type { Theme } from 'vitepress'

export default {
  extends: DefaultTheme,
  setup() {
    onMounted(() => {
      // Handle redirects for old /doc/ URLs
      const path = window.location.pathname
      
      // Redirect /doc/xxx to /xxx
      if (path.startsWith('/doc/')) {
        const newPath = path.replace('/doc/', '/')
        window.location.replace(newPath + window.location.search + window.location.hash)
        return
      }
      
      // Redirect /doc/xxx.en.html to /en/xxx.html
      const enHtmlMatch = path.match(/^\/doc\/(.+)\.en\.html$/)
      if (enHtmlMatch) {
        const pagePath = enHtmlMatch[1]
        window.location.replace(`/en/${pagePath}.html` + window.location.search + window.location.hash)
        return
      }
    })
  }
} satisfies Theme

#!/usr/bin/env node
/**
 * Format sitemap.xml for better readability
 * This script is run after VitePress builds the site
 */

import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const sitemapPath = path.join(__dirname, '../.vitepress/dist/sitemap.xml')

if (fs.existsSync(sitemapPath)) {
  try {
    const sitemapContent = fs.readFileSync(sitemapPath, 'utf-8')
    
    // Add proper XML formatting with indentation
    const formattedSitemap = sitemapContent
      .replace(/></g, '>\n<')
      .replace(/<url>/g, '\n  <url>')
      .replace(/<\/url>/g, '\n  </url>')
      .replace(/<loc>/g, '\n    <loc>')
      .replace(/<\/loc>/g, '</loc>')
      .replace(/<lastmod>/g, '\n    <lastmod>')
      .replace(/<\/lastmod>/g, '</lastmod>')
      .replace(/<xhtml:link/g, '\n    <xhtml:link')
      .replace(/<\/urlset>/g, '\n</urlset>')
      .replace(/^\n+/gm, '\n')  // Remove multiple consecutive newlines
      .replace(/^\n/, '')  // Remove leading newline
      .replace(/\n$/g, '') + '\n'  // Ensure single trailing newline
    
    fs.writeFileSync(sitemapPath, formattedSitemap, 'utf-8')
    console.log('✓ Formatted sitemap.xml with proper indentation')
  } catch (error) {
    console.error('✗ Failed to format sitemap.xml:', error.message)
    process.exit(1)
  }
} else {
  console.warn('⚠ sitemap.xml not found at:', sitemapPath)
}

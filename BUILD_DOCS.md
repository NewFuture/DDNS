# Build Documentation

Build DDNS documentation website using [VitePress 2.0](https://vitepress.dev/).

## Quick Start

```bash
cd doc
npm install
npm run build
```

Output: `doc/.vitepress/dist/`

## Commands

```bash
cd doc
npm run build          # Build for production
npm run docs:dev       # Development server (http://localhost:5173)
npm run docs:preview   # Preview production build
```

## Features

- **Bilingual** - Chinese/English with i18n
- **Search** - Full-text local search
- **Dark Mode** - Theme toggle
- **TOC** - Auto-generated table of contents
- **Mobile** - Responsive design
- **SEO** - Sitemap + llms.txt
- **Redirects** - Legacy URL support (`/doc/*` → `/*`)

## Requirements

- Node.js 22+
- npm

## Resources

- [VitePress Documentation](https://vitepress.dev/)
- Configuration: `doc/.vitepress/config.mts`
- Markdown Features: [Guide](https://vitepress.dev/guide/markdown)

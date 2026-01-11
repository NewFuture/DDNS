# Documentation Website Builder

This document describes how to build the DDNS documentation website using VitePress.

## Overview

The documentation is built using **[VitePress](https://vitepress.dev/)** - a Vue-powered static site generator specifically designed for documentation websites.

### Why VitePress?

- **专为文档设计** - Purpose-built for documentation sites
- **快速构建** - Lightning-fast build times with Vite
- **现代化** - Vue 3 + Vite stack, modern developer experience
- **内置功能丰富** - Search, i18n, dark mode, responsive design out of the box
- **中文友好** - Created by Evan You (Vue creator), excellent Chinese community support

## Features

### Built-in Features

1. **响应式导航**
   - Automatic navigation from directory structure
   - Collapsible sidebar sections
   - Mobile-friendly hamburger menu
   - Active page highlighting

2. **双语支持 (Bilingual Support)**
   - Built-in i18n (internationalization)
   - Chinese (简体中文) and English versions
   - Language switcher in navigation
   - Separate navigation for each language

3. **页内目录 (Table of Contents)**
   - Automatically generated from H2-H3 headers
   - Sticky sidebar on desktop
   - Integrated into content on mobile
   - Smooth scroll navigation

4. **搜索功能 (Search)**
   - Full-text local search
   - Keyboard shortcuts
   - Instant results

5. **主题切换 (Theme Toggle)**
   - Light/Dark mode toggle
   - Smooth transitions
   - Persistent user preference

6. **GitHub 集成**
   - "Edit this page" link on every page
   - Repository link in navigation
   - Last updated timestamp

7. **代码高亮 (Code Highlighting)**
   - Syntax highlighting for multiple languages
   - Line numbers
   - Code groups and tabs

## Requirements

- **Node.js** 18+ or 20+
- **npm** (comes with Node.js)

## Installation

### Quick Start

One command to install, setup, and build:

```bash
cd doc
npm install
npm run build
```

This automatically:
1. Installs dependencies
2. Sets up directory structure
3. Builds the static site

## Usage

### One-Command Build

```bash
cd doc
npm run build
```

This command automatically:
1. Sets up the doc directory structure
2. Copies README files
3. Builds the production site

Output: `doc/.vitepress/dist/` directory

### Development

Start the development server (auto-setup included):

```bash
cd doc
npm run docs:dev
```

Then open http://localhost:5173 in your browser.

### Building

Build the static site:

```bash
cd doc
npm run docs:build
```

### Preview

Preview the production build locally:

```bash
cd doc
npm run docs:preview
```

## Directory Structure

```
.
├── doc/                     # Single documentation directory
│   ├── package.json        # Node.js dependencies and scripts
│   ├── .vitepress/         # VitePress configuration
│   │   ├── config.mts      # Main configuration file
│   │   ├── cache/          # Build cache (gitignored)
│   │   └── dist/           # Built static site (gitignored)
│   ├── build_docs.sh       # Build script
│   ├── setup-docs.mjs      # Setup script
│   ├── config/             # Configuration guides (source)
│   ├── providers/          # DNS provider documentation (source)
│   ├── dev/                # Developer documentation (source)
│   ├── img/                # Images (source)
│   ├── index.md            # Homepage (generated, gitignored)
│   ├── en/                 # English version (generated, gitignored)
│   └── public/             # Static assets (generated, gitignored)
```

## Configuration

The main configuration file is `doc/.vitepress/config.mts`. It includes:

- **Site metadata** - Title, description, base URL
- **Navigation** - Top navbar structure
- **Sidebar** - Side navigation for different sections
- **i18n** - Multi-language configuration
- **Theme** - Colors, logos, social links
- **Search** - Local search configuration
- **Markdown** - Code highlighting, line numbers

### Customizing

To customize the documentation:

1. Edit `doc/.vitepress/config.mts` for configuration
2. Add/edit markdown files in `doc/` subdirectories
3. For Chinese version: `doc/**/*.md`
4. For English version: `doc/**/*.en.md`

## Adding Documentation

### Chinese Documentation

1. Create markdown file in `doc/` directory (e.g., `doc/config/new-guide.md`)
2. Add to sidebar configuration in `doc/.vitepress/config.mts`
3. Run `npm run docs:dev` to preview

### English Documentation

1. Create markdown file with `.en.md` extension
2. Place in same directory structure (e.g., `doc/config/new-guide.en.md`)
3. Add to English sidebar configuration
4. Run `npm run docs:dev` to preview

## Markdown Features

VitePress supports enhanced markdown features:

### Code Blocks

````markdown
```js
console.log('Hello, World!')
```
````

### Containers (Admonitions)

```markdown
::: tip
This is a tip
:::

::: warning
This is a warning
:::

::: danger
This is a danger notice
:::

::: details Click to expand
This is hidden by default
:::
```

### Code Groups

```markdown
::: code-group
```sh [npm]
npm install vitepress
```

```sh [pnpm]
pnpm add vitepress
```
:::
```

### Custom Containers

```markdown
::: info Custom Title
This is an info box with custom title
:::
```

See [VitePress Markdown Features](https://vitepress.dev/guide/markdown) for more.

## Deployment

The built static site in `doc/.vitepress/dist/` can be deployed to:

- **GitHub Pages** - Use GitHub Actions or `gh-pages` branch
- **Netlify** - Drag & drop or CI/CD
- **Vercel** - Import from GitHub
- **Any static hosting** - Upload `dist/` contents

### GitHub Pages Example

```yaml
# .github/workflows/deploy.yml
name: Deploy Docs

on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: bash doc/build_docs.sh
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: doc/.vitepress/dist
```

## Advantages Over Other Solutions

✅ **Faster than Jekyll/Hugo** - Vite-powered instant HMR  
✅ **More flexible than Docusaurus** - Lighter weight, Vue ecosystem  
✅ **Better i18n than Sphinx** - Built-in multi-language support  
✅ **Easier than custom solutions** - Configuration over code  
✅ **Modern developer experience** - Vue 3, TypeScript, Vite  
✅ **Chinese-friendly** - Excellent Chinese documentation and community  

## Troubleshooting

### Node.js Version

If you encounter errors, ensure you're using Node.js 18+ or 20+:

```bash
node --version  # Should be v18.x.x or v20.x.x
```

### Port Already in Use

If port 5173 is in use, specify a different port:

```bash
npm run docs:dev -- --port 8080
```

### Build Errors

Clear cache and reinstall:

```bash
rm -rf node_modules package-lock.json doc/.vitepress/cache
npm install
npm run docs:build
```

## Resources

- [VitePress Documentation](https://vitepress.dev/)
- [VitePress中文文档](https://vitejs.cn/vitepress/)
- [Vue.js Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)

## License

This build configuration is part of the DDNS project and is licensed under the MIT License.

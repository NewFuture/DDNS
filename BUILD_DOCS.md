# Documentation Build Script

This document describes how to build the DDNS documentation website from markdown files.

## Overview

The `build_docs.py` script converts markdown documentation into a static HTML website with the following features:

1. **Responsive Navigation Bar** - Global navigation with collapsible directory tree, adapts to screen size
2. **In-Page Table of Contents** - Right sidebar with page TOC for quick navigation (hidden on small screens)
3. **Language Switcher** - Easy switching between Chinese and English versions
4. **Pure Static HTML** - No server-side processing required, can be hosted anywhere
5. **Footer with Links** - Includes GitHub repository, issues, and edit page links

## Requirements

- Python 3.x (no external dependencies, uses only standard library)

## Usage

### Building the Documentation

Run the build script from the project root:

```bash
python3 build_docs.py
```

This will:
- Parse all markdown files in the `doc/` directory
- Generate HTML files in the `build/` directory
- Copy static assets (images, favicon, CNAME)
- Create both Chinese and English versions

### Output Structure

```
build/
├── index.html              # Homepage (Chinese)
├── index.en.html          # Homepage (English)
├── config/                # Configuration documentation
│   ├── cli.html
│   ├── cli.en.html
│   └── ...
├── providers/             # DNS provider guides
│   ├── dnspod.html
│   ├── dnspod.en.html
│   └── ...
├── dev/                   # Developer documentation
│   ├── provider.html
│   ├── provider.en.html
│   └── ...
└── doc/                   # Static assets
    └── img/
```

### Testing Locally

After building, you can test the documentation website locally:

```bash
cd build
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

## Features Details

### 1. Responsive Navigation

The navigation sidebar shows:
- Top-level documentation files (Docker, Install, Release)
- Grouped sections:
  - **配置方式** / **Configuration** - CLI, JSON, Environment configuration
  - **DNS 服务商** / **DNS Providers** - All provider guides
  - **开发文档** / **Development** - Developer guides

On mobile devices (width < 768px):
- Navigation is hidden by default
- Toggle button appears in header
- Click to show/hide navigation

### 2. In-Page Table of Contents

For pages in the `doc/` directory:
- Automatically generates TOC from H1-H3 headers
- Fixed position on the right side
- Click to jump to sections
- Hidden on screens < 1200px wide

### 3. Language Switcher

- Automatically detects language version (.md vs .en.md)
- Shows "Switch to English" on Chinese pages
- Shows "切换到中文" on English pages
- Navigation and labels adapt to current language
- Link to alternate version if it exists

### 4. Footer

Each page includes footer with:
- Link to GitHub repository
- Link to GitHub issues
- Link to edit the current page on GitHub
- Copyright notice

## Markdown Features Supported

The build script supports standard markdown:

- Headers (H1-H6)
- Paragraphs
- Lists (ordered and unordered)
- Code blocks with language highlighting
- Inline code
- Links and images
- Bold and italic text
- Blockquotes
- Horizontal rules
- YAML front matter (for page metadata)

### Front Matter

Pages can include YAML front matter for metadata:

```markdown
---
title: Page Title
description: Page description
---

# Content starts here
```

## Customization

### Styling

All CSS is embedded in the HTML template. To customize:
1. Edit the `HTML_TEMPLATE` variable in `build_docs.py`
2. Modify the `<style>` section
3. Rebuild the documentation

### Navigation Structure

The navigation tree is automatically generated from the directory structure. Directory labels are defined in the `build_nav_tree()` function:

```python
dir_labels = {
    "config": {"zh": "配置方式", "en": "Configuration"},
    "dev": {"zh": "开发文档", "en": "Development"},
    "providers": {"zh": "DNS 服务商", "en": "DNS Providers"}
}
```

### GitHub Links

Update the repository and branch in the script header:

```python
GITHUB_REPO = "NewFuture/DDNS"
GITHUB_BRANCH = "master"
```

## Deployment

The generated `build/` directory can be deployed to any static hosting service:

- **GitHub Pages**: Push to `gh-pages` branch
- **Netlify**: Deploy from `build/` directory
- **Vercel**: Deploy from `build/` directory
- **Any web server**: Copy `build/` contents to web root

## Troubleshooting

### Build Errors

If the build fails:
1. Check that all markdown files have valid syntax
2. Ensure `doc/` directory exists with markdown files
3. Verify Python 3.x is installed

### Missing Pages

If some pages don't appear:
1. Check that files end with `.md` or `.en.md`
2. Verify file permissions
3. Check for errors in console output

### Language Switcher Not Working

If language switching doesn't work:
1. Ensure both language versions exist (e.g., `file.md` and `file.en.md`)
2. Check that file names match except for `.en` suffix
3. Verify paths are correct

## Contributing

When adding new documentation:

1. Create both Chinese (.md) and English (.en.md) versions
2. Use consistent naming (same base name)
3. Include front matter with title
4. Test the build locally before committing
5. Run `python3 build_docs.py` to generate HTML

## License

This build script is part of the DDNS project and is licensed under the MIT License.

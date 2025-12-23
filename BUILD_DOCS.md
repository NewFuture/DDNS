# Documentation Build Script

This document describes how to build the DDNS documentation website using MkDocs with Material theme.

## Overview

The documentation is built using mature, industry-standard tools:

- **[MkDocs](https://www.mkdocs.org/)** - Popular static site generator for project documentation
- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** - Modern, responsive theme with extensive features

## Features

### Built-in Features from Material Theme

1. **Responsive Navigation**
   - Automatic navigation from directory structure
   - Collapsible sections
   - Mobile-friendly hamburger menu
   - Search functionality

2. **Table of Contents**
   - Automatic TOC generation from headers
   - Sticky TOC sidebar
   - Smooth scrolling navigation
   - Responsive (integrates on small screens)

3. **Language Support**
   - Multi-language documentation support via i18n plugin
   - Language switcher in header
   - Separate navigation for each language

4. **Theme Features**
   - Light/dark mode toggle
   - Code syntax highlighting with copy button
   - Admonitions (notes, warnings, tips)
   - Tabbed content blocks
   - Icon support (Material Design, FontAwesome)
   - Social links in footer

5. **GitHub Integration**
   - Edit page link on every page
   - Repository link in header
   - Social media links

## Requirements

- Python 3.6+
- pip

## Installation

The build script will automatically install dependencies if needed:

```bash
python3 build_docs.py
```

Or install manually:

```bash
pip install mkdocs-material
```

## Usage

### Building the Documentation

Run the build script:

```bash
python3 build_docs.py
```

This will:
1. Check for required dependencies (install if missing)
2. Generate `mkdocs.yml` configuration
3. Prepare documentation files
4. Build the static site to `site/` directory

### Preview Locally

After building, preview the documentation:

```bash
mkdocs serve
```

Then open http://localhost:8000 in your browser.

### Deploy to GitHub Pages

Deploy directly to GitHub Pages:

```bash
mkdocs gh-deploy
```

## Configuration

The build script automatically generates `mkdocs.yml` with:

- Site metadata (name, URL, description)
- Material theme configuration
- Navigation structure from doc/ directory
- Markdown extensions (code highlighting, admonitions, etc.)
- Language support (Chinese and English)
- Social links and GitHub integration

To customize, edit the generated `mkdocs.yml` or modify `build_docs.py`.

## Directory Structure

```
.
├── build_docs.py          # Build script
├── mkdocs.yml            # Generated configuration (after build)
├── docs/                 # Generated docs directory (after build)
│   ├── index.md         # Homepage (from README.md)
│   └── doc/             # Documentation files
│       ├── config/      # Configuration guides
│       ├── providers/   # DNS provider documentation
│       └── dev/         # Developer documentation
└── site/                # Built static site (after build)
    └── ...              # HTML files ready for deployment
```

## Adding Documentation

1. Add markdown files to `doc/` directory
2. For bilingual docs, use `.md` (Chinese) and `.en.md` (English)
3. Update navigation in `build_docs.py` if needed
4. Run `python3 build_docs.py` to rebuild

## Markdown Extensions

Material for MkDocs supports many markdown extensions:

### Code Blocks

````markdown
```python
def hello():
    print("Hello, World!")
```
````

### Admonitions

```markdown
!!! note "Note Title"
    This is a note admonition.

!!! warning
    This is a warning.

!!! tip
    This is a helpful tip.
```

### Tabs

```markdown
=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

### Task Lists

```markdown
- [x] Completed task
- [ ] Pending task
```

See [Material for MkDocs documentation](https://squidfunk.github.io/mkdocs-material/reference/) for more features.

## Deployment Options

The generated `site/` directory can be deployed to:

- **GitHub Pages**: `mkdocs gh-deploy`
- **Netlify**: Deploy from `site/` directory
- **Vercel**: Deploy from `site/` directory
- **Any web server**: Copy `site/` contents to web root

## Troubleshooting

### Dependencies Not Found

If dependencies are missing:

```bash
pip install mkdocs-material pyyaml
```

### Build Errors

Check that:
1. All markdown files are valid
2. `doc/` directory exists
3. Python 3.6+ is installed

### Preview Not Working

Ensure port 8000 is available or specify a different port:

```bash
mkdocs serve -a localhost:8080
```

## Advantages Over Custom Solution

Using MkDocs with Material theme provides:

✅ **Mature, well-tested codebase** - Used by thousands of projects  
✅ **Active development** - Regular updates and bug fixes  
✅ **Extensive documentation** - Comprehensive guides and examples  
✅ **Rich features** - Search, i18n, versioning, etc.  
✅ **Beautiful design** - Professional, modern appearance  
✅ **Easy maintenance** - Configuration-based, not code  
✅ **Plugin ecosystem** - Extend functionality as needed  
✅ **Accessibility** - WCAG compliant, keyboard navigation  
✅ **Performance** - Optimized static site generation  
✅ **Community support** - Large user base and contributors  

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
- [Material for MkDocs Reference](https://squidfunk.github.io/mkdocs-material/reference/)
- [MkDocs Plugins](https://github.com/mkdocs/mkdocs/wiki/MkDocs-Plugins)

## License

This build script is part of the DDNS project and is licensed under the MIT License.

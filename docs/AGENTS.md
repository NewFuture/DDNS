# Documentation Guide

## Scope

Maintain the VitePress site in `docs/`. Keep Chinese source pages and their
English counterparts in `docs/en/` aligned: preserve option names, JSON keys,
CLI flags, provider IDs, examples, and behavior in both languages.

## Navigation and links

- Add or remove pages from the matching Chinese and English navigation and
  sidebar entries in `docs/.vitepress/config.mts`.
- Use relative links between documentation pages. Chinese pages link to Chinese
  pages; English pages link to `docs/en/` pages. Use full URLs for external
  destinations.
- Keep `docs/llms.txt` current when adding or removing pages. The build writes
  the dated copy to the site output.
- The VitePress build checks dead links. Do not disable that check to bypass a
  broken link.

## Sources and generated files

- Edit root `README.md` and `README.en.md` for home-page content. The VitePress
  config generates `docs/index.md` and `docs/en/index.md` from them.
- Treat `docs/.vitepress/dist/` as generated output; do not edit or commit it.
- `docs/public/` contains source static assets, but its linked `schema/` and
  `tests/` content comes from the repository sources. Update the source
  directories, not generated copies.

## Executable documentation files

`docs/public/install.sh` and `docs/esa.js` are executable deployment code, not
ordinary prose. Change them only when required, preserve their runtime
contracts, and review downloads, redirects, caching, and user input handling
as code.

## Validation

Do not install dependencies unless the task permits it. When validation is
allowed, run exactly:

```sh
npm --prefix docs ci
npm --prefix docs run build
```

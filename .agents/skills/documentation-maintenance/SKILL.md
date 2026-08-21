---
name: documentation-maintenance
description: Maintain DDNS VitePress documentation with bilingual parity, correct navigation and links, safe executable-doc changes, and build verification.
---

# Documentation Maintenance

1. Read the root `AGENTS.md`, `docs/AGENTS.md`, and the relevant documentation,
   implementation, schema, and tests before editing.
2. Keep Chinese pages and their `docs/en/` counterparts behaviorally aligned.
   Preserve option names, JSON keys, CLI flags, provider IDs, and examples.
3. For new or removed pages, update both locale navigation and sidebars in
   `docs/.vitepress/config.mts`, then update `docs/llms.txt`.
4. Use relative links for internal documentation and full URLs for external
   destinations. Keep each locale within its own documentation tree.
5. Edit source content only: root `README.md` and `README.en.md` generate the
   documentation home pages; do not edit or commit `docs/.vitepress/dist/`.
6. Treat `docs/public/install.sh` and `docs/esa.js` as executable code. Preserve
   their runtime contracts and review downloads, redirects, caching, and inputs.
7. When dependency installation is permitted, validate with:

   ```sh
   npm --prefix docs ci
   npm --prefix docs run build
   ```

Report changed files and any validation not run.

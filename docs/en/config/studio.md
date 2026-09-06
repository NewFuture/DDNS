---
title: DDNS Configuration Builder and Validator
description: Build and import DDNS Schema v4.1 configurations in your browser, with static checks for structure and runtime requirements. Supports multiple providers, IPv4/IPv6, proxies, cache, and logging.
layout: page
editLink: false
lastUpdated: false
aside: false
sidebar: false
---

<!--
THESIS: Turn configuration documentation into an operational deployment workbench, rejecting a wizard that reveals mistakes only after submission.
OWN-WORLD: Extend DDNS blue and VitePress light/dark themes with the divisions, fine rules, and live signals of a network control surface.
STORY: Users choose providers, records, and runtime policy while seeing canonical JSON, exact error paths, and deployment warnings, then copy or download.
FIRST VIEWPORT: The title and local-only privacy promise lead directly into three columns: providers, configuration, and persistent JSON validation.
FORM: A complete Operate page inside the established documentation world, using a continuously visible workbench instead of hidden sequential steps.
-->

<ConfigStudio />

::: details Imports, drafts, and custom fields
For configurations created, pasted, or edited on this page, **Load into builder** does not count as an export. When temporary browser storage is available, complete unexported drafts (including credentials) are saved in the current tab and can be restored after a refresh; copying or downloading marks them as exported. An unchanged file import still uses the original file as its saved baseline. Older drafts without file-origin information are conservatively retained as unexported.

Leave provider custom fields blank to inherit the global JSON `extra`; enter `{}` for an explicit empty override, which does not clear custom fields supplied by environment variables. Imports resolve flat fields, `extra_` aliases, and nested `extra` in runtime precedence order. To preserve effective values, inherited fields are expanded into explicit provider custom fields when needed; those explicit values subsequently override global settings.
:::

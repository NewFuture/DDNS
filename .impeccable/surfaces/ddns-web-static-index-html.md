---
version: 1
slug: "ddns-web-static-index-html"
primary_target: "web/index.html"
related_targets: ["web/dashboard.css","web/dashboard.js"]
---

# Built-in DDNS dashboard

- **Scope:** `web/index.html`, its CSS, and its browser behavior.
- **Mode:** Operate.
- **Audience and job:** A self-hosting or network-operations user checks this device's DDNS state, runs a sync, and maintains the active local configuration.
- **Primary states:** Healthy after sync, configured but not yet synced, needs attention, connection failure, invalid configuration repair, and no configuration yet.
- **Primary task:** Daily status is first when configured. When no provider is configured, the same opening position becomes a first-configuration path and leads directly into the real editor.
- **Content and proof:** Only local API data: detected addresses, provider and record counts, cache results, activity, scheduler state, configuration path, validation, backups, and save state.
- **Constraints:** Built into the standard-library Python server; no remote assets or runtime dependencies; loopback and token protected; responsive; keyboard accessible; Config Studio remains a separate advanced design tool.
- **Direction:** A modern signal-path workbench: cool powder-coated surfaces, one dark trace deck, cobalt routes, green and amber state signals, and ruled calibration-style forms. It refuses a generic sidebar and summary-card dashboard.
- **Memorable moment:** An immediate sync sends one restrained pulse from local address through provider to DNS records. In first-run mode, the editor opens directly with provider, domain, and save-then-sync steps.
- **Unresolved decisions:** None.

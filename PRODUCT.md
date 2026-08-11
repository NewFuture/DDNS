# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is a self-hosting or network-operations user running DDNS on their own device. They open the built-in interface to understand the current local service state, maintain the active configuration, and trigger operational actions without switching to a separate tool.

## Product Purpose

DDNS keeps DNS records aligned with the current IPv4 and IPv6 addresses. Its built-in web interface makes the running client observable and maintainable: success means the user can quickly confirm whether updates are healthy, understand what is configured, safely change the current configuration, and recover when a change is invalid.

## Positioning

The dashboard is a local control surface shipped inside the DDNS program, backed by the same configuration and runtime authority as the client. It is not a documentation website or a second configuration generator.

## Operating Context

- The interface is served from the running DDNS process on a loopback address and opened in a browser on the same device.
- The user works with the machine's active configuration, current address sources, DNS providers, update activity, and scheduler state.
- The documentation-side Config Studio remains the place for designing complex configurations, static validation, and JSON import or export.

## Capabilities and Constraints

- Show current runtime health, addresses, configured records, recent update activity, and scheduler state.
- Read, validate, save, restore, and repair the local configuration while preserving sparse configuration semantics.
- Trigger an immediate synchronization and maintain the Web process's built-in scheduler without duplicating system tasks.
- Use `ddns/config/field-model.json` as shared configuration metadata across the built-in server and Config Studio.
- Treat Python normalization and validation as the final runtime authority; browser validation is feedback, not a competing implementation contract.
- Keep the built-in server loopback-only and token-protected.
- Preserve zero runtime dependencies, Python 2.7 and 3.x compatibility, and offline operation.
- Keep Config Studio and the built-in dashboard separate; they exchange configuration through JSON or files rather than a live browser connection.

## Brand Commitments

Use the established DDNS name and project mark. The built-in surface should speak in concise operational language and must not present itself as documentation, a hosted service, or a generic admin portal.

## Evidence on Hand

Runtime state and actions come from the local dashboard APIs. Provider metadata and configuration rules come from the shared field model. No external monitoring history, customer claims, benchmarks, or remote service data are available and they must not be fabricated.

## Product Principles

1. Put current state before configuration detail.
2. Make the common operational path obvious and keep advanced controls progressive.
3. Preserve configuration intent instead of expanding inherited defaults into the saved file.
4. Keep destructive or network-changing actions explicit, reversible where possible, and grounded in local runtime feedback.
5. Share configuration truth without forcing the documentation tool and built-in dashboard into the same UI.

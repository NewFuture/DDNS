# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Inferred from the repository: self-hosters, developers, and operators who need DNS records to follow changing IPv4 or IPv6 addresses across home labs, servers, containers, and scheduled jobs.

## Product Purpose

DDNS detects the current IP address and keeps one or more DNS records synchronized through a selected DNS provider. Success means users can create a valid configuration, run it unattended, and understand failures without provider-specific guesswork.

## Positioning

DDNS combines a dependency-free Python client, broad provider support, dual-stack address detection, and interchangeable CLI, environment, and JSON configuration in one portable tool.

## Operating Context

Users configure DDNS in documentation, code editors, shells, Docker deployments, and operating-system schedulers. Credentials, domain lists, provider APIs, proxies, cache behavior, and logs are recurring parts of setup and diagnosis.

## Capabilities and Constraints

- Supports Python 2.7 and Python 3.x without runtime dependencies.
- Supports multiple DNS providers in one schema v4.1 configuration.
- Supports IPv4 and IPv6, multiple address sources, proxies, SSL controls, caching, logging, and provider-specific extra fields.
- Configuration priority is CLI, then JSON, then environment variables.
- Provider credentials are sensitive and must not be persisted or transmitted by documentation tooling.
- Chinese and English documentation must remain aligned.

## Brand Commitments

The product name is DDNS. The incumbent documentation uses the blue globe-and-refresh logo at `docs/public/img/ddns.svg`, VitePress navigation conventions, concise technical language, and light/dark themes.

## Evidence on Hand

Repository documentation, provider guides, schema files, tests, and implementation code are the source of truth. No customer claims, usage benchmarks, or commercial claims are established.

## Product Principles

- Make a working configuration easier to produce than an incomplete one.
- Explain provider differences at the point of configuration.
- Keep secrets local and make their handling explicit.
- Validate syntax, schema rules, and deployment readiness as separate signals.
- Preserve portable, dependency-free operation.

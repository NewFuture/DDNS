# Security Policy

## Reporting a vulnerability

Do not open a public issue for vulnerabilities, leaked credentials, or private
configuration. Use GitHub's private vulnerability reporting for this repository:

https://github.com/NewFuture/DDNS/security/advisories/new

Include the affected version, impact, reproduction details, and a minimal
redacted example. Do not include working provider credentials or customer data.

If credentials may have been exposed, revoke or rotate them immediately and
remove public logs or artifacts containing them.

## Supported versions

Security fixes target the latest stable release and the active default branch.
Older releases may require an upgrade.

## Security-sensitive changes

Changes to authentication, credential masking, HTTP/TLS behavior, remote
configuration, installers, workflows, release publishing, MCP mutation, or
repository permissions require explicit human review. Automated agents must not
publish, use live credentials, or bypass required checks.

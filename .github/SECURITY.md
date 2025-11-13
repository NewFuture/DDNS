# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 3.x     | :white_check_mark: |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Disclose Publicly

Please **do not** create a public GitHub issue for security vulnerabilities. This protects users while the issue is being fixed.

### 2. Report Privately

Report security vulnerabilities through one of these methods:

- **GitHub Security Advisories** (preferred): Use the [Security Advisories](https://github.com/NewFuture/DDNS/security/advisories) page
- **Email**: Send details to python@newfuture.cc with subject line "SECURITY: [Brief Description]"

### 3. Include Details

When reporting, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)
- Your contact information for follow-up

### 4. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity and complexity

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Secure Credentials**: 
   - Never commit API keys or tokens to version control
   - Use environment variables or secure configuration files
   - Set appropriate file permissions (e.g., `chmod 600 config.json`)
3. **Review Logs**: Check logs regularly for suspicious activity
4. **Network Security**: Use HTTPS for all DNS provider APIs
5. **Docker Security**: 
   - Use official images from trusted sources
   - Keep Docker images updated
   - Run containers with minimal privileges

### For Contributors

1. **Code Review**: All changes require review before merging
2. **Dependency Management**: 
   - Minimize external dependencies
   - Use only Python standard library when possible
   - Document any required dependencies
3. **Input Validation**: Always validate and sanitize user input
4. **Sensitive Data**: 
   - Use `_mask_sensitive_data()` when logging
   - Never log credentials or tokens
5. **Error Handling**: 
   - Catch specific exceptions
   - Don't expose sensitive information in error messages
6. **Authentication**: 
   - Support secure authentication methods (HMAC-SHA256)
   - Implement proper token/credential handling

## Known Security Considerations

### API Credentials

DDNS requires API credentials to update DNS records. These credentials should be:

- Stored securely with appropriate file permissions
- Never committed to version control
- Rotated regularly according to your security policy
- Limited to minimum necessary permissions

### Network Communication

- All DNS provider APIs use HTTPS
- HTTP proxy support available if needed
- Certificate verification enabled by default

### Local Cache

- Cache files may contain DNS record information
- Default location: system temp directory
- Set appropriate file permissions if needed
- Can be disabled if security concerns exist

## Security Updates

Security fixes are released as soon as possible after verification. Users will be notified through:

- GitHub Security Advisories
- Release notes
- Updated documentation

## Disclosure Policy

When a security vulnerability is fixed:

1. A security advisory will be published
2. The fix will be included in the next release
3. Credit will be given to the reporter (if desired)
4. Details will be disclosed after users have time to update

## Third-Party Dependencies

DDNS minimizes dependencies to reduce attack surface:

- **Core functionality**: Python standard library only
- **Optional features**: Minimal, well-vetted packages
- **Development**: Additional tools for testing and linting

We regularly review dependencies for security vulnerabilities.

## Compliance

This project follows industry best practices for:

- Secure coding standards
- Vulnerability disclosure
- Security patch management
- Privacy protection

## Contact

For security-related questions or concerns:

- **Security Issues**: Use GitHub Security Advisories or email python@newfuture.cc
- **General Questions**: Open a regular GitHub issue
- **Project Maintainer**: @NewFuture

Thank you for helping keep DDNS and its users secure!

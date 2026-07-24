# Security Policy

## Supported Versions

We actively maintain the latest release. Security fixes are backported to the current major version.

| Version | Supported |
|---------|-----------|
| latest  | ✅        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

- **GitHub Security Advisory**: [Report a vulnerability](https://github.com/wenwanqing1217/monorepo/security/advisories/new)
- **Email**: wenwanqing1217@github.com

Please include:

1. Description of the vulnerability
2. Steps to reproduce
3. Affected component and version
4. Potential impact assessment
5. Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix or mitigation**: Within 30 days (critical) / 90 days (non-critical)

## Security Best Practices for Contributors

### Secrets Management

- **Never** commit API keys, tokens, or credentials
- Use environment variables for all sensitive configuration
- Rotate keys immediately if accidentally exposed

### Code Review Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user-facing endpoints
- [ ] Parameterized queries (no SQL injection)
- [ ] Output encoding (no XSS)
- [ ] Authentication/authorization checks
- [ ] Rate limiting on sensitive endpoints

### Dependencies

- Dependabot is enabled for automatic security updates
- Run `pip audit` / `npm audit` before submitting PRs
- Pin dependency versions in production

## Security Measures

- **JWT + jti revocation**: Every token has a unique ID; logout revokes instantly
- **Token rotation**: Refresh tokens are single-use; rotation detects reuse
- **Rate limiting**: Sliding window per-IP (5 req/60s for sensitive endpoints)
- **AES-256-GCM**: Private memory chain encrypted at rest
- **Ed25519 DID**: Client-side key generation via Web Crypto API
- **CORS allowlist**: Explicit origin whitelist, not `*`
- **No hardcoded secrets**: All credentials via environment variables

## Security Hall of Fame

We thank the following for responsible disclosure:

<!-- Security researchers who report valid vulnerabilities will be listed here -->

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

## Known Security Considerations

- Ghost.html uses `allow_origins=["*"]` for CORS — acceptable for the public gateway layer, but internal APIs should restrict origins
- The demo mode in DS uses default credentials — **always** change `DASH_PASS` in production
- JWT tokens should use strong, randomly generated secrets (`AUTH_MASTER_KEY`)

## Security Hall of Fame

We thank the following for responsible disclosure:

<!-- Security researchers who report valid vulnerabilities will be listed here -->

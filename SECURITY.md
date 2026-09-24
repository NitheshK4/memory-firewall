# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | ✅ Yes     |
| 0.1.x   | ⚠️ Critical fixes only |
| < 0.1   | ❌ No      |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, send a report to **nitheshk236@gmail.com** with:

1. A description of the vulnerability and its potential impact.
2. Steps to reproduce (proof-of-concept code is welcome).
3. Any suggested fixes or mitigations.

You can expect:
- An acknowledgment within **48 hours**.
- A detailed response (including whether we accept or decline the report) within **7 days**.
- A patch and public disclosure coordinated with you once the fix is ready.

## Security Considerations

Memory Firewall processes potentially sensitive AI memory content. Please pay particular attention to:

- **Prompt injection** attacks via crafted memory payloads.
- **Trust-score manipulation** by feeding carefully crafted content that bypasses heuristics.
- **API authentication bypass** or privilege escalation.
- **Denial-of-service** via large or malformed payloads.
- **Information leakage** through error messages or audit log endpoints.

## Disclosure Policy

We follow [responsible disclosure](https://cheatsheetseries.owasp.org/cheatsheets/Vulnerability_Disclosure_Cheat_Sheet.html). We will credit researchers in the release notes unless they prefer to remain anonymous.

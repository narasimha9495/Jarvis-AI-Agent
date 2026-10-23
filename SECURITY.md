# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue.
2. Email the maintainer at **budhilreddy024@gmail.com** with details.
3. Include steps to reproduce the vulnerability.
4. Allow up to 48 hours for an initial response.

## Security Measures

- All destructive actions require explicit user confirmation.
- Shell command execution is blocked by the safety engine.
- Rate limiting is enforced on all API actions.
- Input sanitization is applied to all user-provided data.

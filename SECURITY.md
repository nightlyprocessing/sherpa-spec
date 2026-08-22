# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security and integrity of SherpaMD and all associated specifications seriously.

If you discover a security vulnerability, credential leak, or sensitive information exposure within this repository, please report it responsibly:

- **Do NOT** open a public issue on GitHub.
- Submit a private security report through GitHub Security Advisories or contact repository maintainers.
- Provide a detailed summary of the vulnerability, reproduction steps, affected files, and potential impact.

Maintainers will acknowledge receipt within 48 hours and coordinate remediation and disclosure.

## Security & Secret Hygiene Directives

All contributors and automated agents must adhere to the following security principles:
1. **Zero Secrets in Repository**: Never commit API keys, auth tokens, private keys, session cookies, passwords, or personal credentials.
2. **Path Sanitization**: Never commit absolute local filesystem paths containing personal usernames (e.g. `/home/<username>/`). Use relative repository paths or standard environment variables.
3. **Infrastructure Abstraction**: Abstract private IP addresses, private ports, VPN hostnames, and internal infrastructure topologies into generic role archetypes.
4. **Validation**: Run `python3 scripts/validate_sherpa.py` and security scans before committing any specification or documentation file.

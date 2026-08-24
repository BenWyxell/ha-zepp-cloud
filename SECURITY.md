# Security policy

## Credentials

A Zepp `apptoken` should be treated as a password/session credential.

Never include a token in:

- GitHub issues
- screenshots
- debug logs
- Home Assistant diagnostics attachments
- public configuration examples
- chat messages

If a token is exposed, invalidate/replace it by obtaining a fresh authenticated
Zepp session token.

## Diagnostics privacy

This integration's diagnostics output intentionally excludes:

- app token
- Zepp user ID
- raw health measurements
- sleep records
- heart-rate series
- stress series
- other health payloads

## Reporting security issues

If this project is published on GitHub, use the repository's private security
advisory feature when available instead of a public issue.

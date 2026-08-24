# Contributing

Contributions are welcome.

Please do not attach real Zepp tokens or personally identifiable health exports
to issues or pull requests. Use sanitized or synthetic fixtures.

When adding a new Zepp endpoint:

1. keep all network access in `api.py`;
2. parse unknown/missing fields defensively;
3. never convert missing data to zero;
4. avoid logging request URLs containing user IDs;
5. add a translated entity name;
6. keep diagnostics free of credentials and health payloads.

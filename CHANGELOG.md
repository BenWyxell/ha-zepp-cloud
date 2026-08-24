# Changelog

## 1.0.0

- Public, user-agnostic release.
- No embedded token, user ID, domain, regional host, device name, or other personal data.
- Config flow for per-user credentials.
- Password-style token input.
- Validated Zepp/Huami API hostname.
- Automatic cloud polling.
- Configurable poll interval and recent-day lookback.
- Reauthentication flow for expired/rejected tokens.
- Minute heart-rate decoding using `data_hr` with 8-byte-record fallback.
- Sleep decoding including light/deep/REM and sleep score.
- Daily activity, stress, training load, VO2 max and best-effort SpO2 sensors.
- Manual refresh button.
- Privacy-safe diagnostics.
- English and Hungarian UI translations.
- HACS metadata and repository validation workflows.

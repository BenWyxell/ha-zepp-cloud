# Changelog

## 1.4.0

- Expose the decoded one-minute heart-rate cloud series as timestamped chart data.
- Lovelace/ApexCharts can now render the actual minute samples instead of only Home Assistant's polling-time sensor states.
- Existing blood-pressure and SpO2 chart-history attributes are unchanged.

## 1.3.0

- Expose compact timestamped blood-pressure and SpO2 histories for Lovelace charts.
- Blood-pressure history contains actual measurement time, systolic, diastolic and pulse values.
- SpO2 history contains actual cloud sample time, saturation and manual/automatic flag.
- Histories are capped to avoid unbounded state attributes.

## 1.2.0

- Added current Zepp `Spo2V2` / `real_data` cloud support.
- Parse `value.samples[].spo2` and reconstruct the actual measurement completion time.
- Keep the legacy `blood_oxygen` event source as fallback.

## 1.1.0

- Added Zepp Cloud blood-pressure polling via `/users/me/bloodPressure`.
- Added latest combined blood pressure, systolic, diastolic and measurement pulse sensors.
- Added today's blood-pressure measurement count plus systolic/diastolic minimum, maximum and average sensors.
- Added English and Hungarian blood-pressure translations.
- Added privacy-safe diagnostics flag showing whether blood-pressure data are available.
- Blood-pressure parsing is defensive across multiple possible Zepp response key names and does not fabricate missing readings.

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

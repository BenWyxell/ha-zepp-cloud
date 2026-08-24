# Zepp Cloud for Home Assistant

An unofficial Home Assistant custom integration for reading health and activity data from the Zepp / Amazfit cloud.

> **Not affiliated with Zepp Health, Amazfit, Huami, or Home Assistant.**  
> This integration uses private, undocumented Zepp API endpoints. They may change without notice.

## Privacy

This repository contains **no user credentials or personal data**.

During Home Assistant setup, each user supplies their own:

- Zepp app token
- Zepp user ID
- regional Zepp API host
- optional display name
- refresh interval

Credentials are stored by Home Assistant in the local config entry. They are not hard-coded in the integration and are not sent anywhere except the Zepp API host configured by the user.

The diagnostics implementation deliberately excludes the token, Zepp user ID and raw health measurements.

## Features

The integration polls Zepp Cloud automatically and exposes Home Assistant entities for data available for the user's account/device, including:

- current/latest cloud heart rate
- heart-rate sample age
- daily heart-rate minimum / maximum / average
- daily steps, distance, active calories and active minutes
- daily goals and goal progress
- stress, daily stress minimum / maximum / average
- sleep score
- total / light / deep / REM sleep
- awake time during sleep
- sleep start / end
- sleep resting heart rate
- sleep awakenings
- training load
- VO2 max, when returned by Zepp
- SpO2, when returned by the account's API stream
- cloud refresh status
- manual **Refresh Zepp Cloud now** button

For Zepp `band_data` responses that expose a 1440-byte `data_hr` field, the integration uses that field as the minute-level heart-rate source. If `data_hr` is missing, it falls back to the matching byte in the known 8-byte minute records.

The integration re-reads a recent cloud window, so data uploaded late by the phone can be picked up on a later refresh.

## Requirements

- Home Assistant with support for modern config-flow custom integrations
- A Zepp/Amazfit account with data present in Zepp Cloud
- Your own Zepp app token, Zepp user ID and regional API host

## Manual installation

1. Download or clone this repository.
2. Copy:

   `custom_components/zepp_cloud`

   to:

   `/config/custom_components/zepp_cloud`

3. Restart Home Assistant completely.
4. Open **Settings → Devices & services → Add integration**.
5. Search for **Zepp Cloud**.
6. Enter your own Zepp credentials and regional API host.

## Getting the Zepp credentials

Zepp does not currently provide a public general-purpose API login flow for this use case. A practical method is to inspect traffic from **your own Zepp account** and extract the authenticated request values.

A useful helper project is [`m4ary/zepp-health-cli`](https://github.com/m4ary/zepp-health-cli).

Typical values you need are:

- `apptoken` request header → **App token**
- `/users/<number>/...` → **User ID**
- hostname such as `api-mifit-xx.zepp.com` → **API host**

Treat the app token like a password. Do not post it in issues, screenshots, logs, chat messages or public repositories.

## Token expiry / reauthentication

If Zepp rejects the token, Home Assistant will mark the config entry as requiring reauthentication. Obtain a fresh token and complete the Zepp Cloud reauthentication flow in Home Assistant.

## Data model notes

Zepp's API is private and varies by device, firmware, account region and Zepp app version. Therefore:

- unavailable data remain unavailable instead of being fabricated;
- a working endpoint may return no values for a device that does not collect them;
- SpO2 / VO2 max / training load may be unavailable for some users;
- missing data are not silently converted to zero.

## Security

The configured API host is validated and must start with `api-mifit` and belong to a `zepp.com` or `huami.com` hostname. Arbitrary hosts are rejected.

See [`SECURITY.md`](SECURITY.md) for credential-handling guidance.

## License

MIT. See [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

The private Zepp API behavior and endpoint mapping were informed by the MIT-licensed [`m4ary/zepp-health-cli`](https://github.com/m4ary/zepp-health-cli) project.

from __future__ import annotations

DOMAIN = "zepp_cloud"

CONF_APP_TOKEN = "app_token"
CONF_USER_ID = "user_id"
CONF_HOST = "host"
CONF_NAME = "name"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_LOOKBACK_DAYS = "lookback_days"

DEFAULT_NAME = "Zepp Cloud"
DEFAULT_UPDATE_INTERVAL = 5
DEFAULT_LOOKBACK_DAYS = 4

MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 60
MIN_LOOKBACK_DAYS = 2
MAX_LOOKBACK_DAYS = 14

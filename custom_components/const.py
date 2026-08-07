from __future__ import annotations

from datetime import timedelta
import logging

DOMAIN = "spotify_ambient"
LOGGER = logging.getLogger(__package__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SCOPES = "user-read-currently-playing user-read-playback-state user-read-private"

CONF_PRIMARY_LIGHTS = "primary_lights"
CONF_SECONDARY_LIGHTS = "secondary_lights"
CONF_ACCENT_LIGHTS = "accent_lights"
CONF_BRIGHTNESS = "brightness"
CONF_TRANSITION = "transition"
CONF_ENABLED = "enabled"

DEFAULT_BRIGHTNESS = 200
DEFAULT_TRANSITION = 1.5
DEFAULT_ENABLED = True

IDLE_INTERVAL = timedelta(seconds=30)
PAUSED_INTERVAL = timedelta(seconds=15)
PLAYING_INTERVAL = timedelta(seconds=5)
ENDING_INTERVAL = timedelta(seconds=1)
ENDING_THRESHOLD_SECONDS = 12

CACHE_VERSION = 1

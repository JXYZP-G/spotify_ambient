from __future__ import annotations

from http import HTTPStatus
from typing import Any

from aiohttp import ClientResponseError

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import SPOTIFY_API_BASE
from .models import SpotifyTrack


class SpotifyAmbientApi:
    def __init__(self, oauth_session: OAuth2Session) -> None:
        self._oauth_session = oauth_session

    async def async_get_profile(self) -> dict[str, Any]:
        return await self._async_get_json("/me")

    async def async_get_current_track(self) -> SpotifyTrack | None:
        response = await self._oauth_session.async_request(
            "GET",
            f"{SPOTIFY_API_BASE}/me/player/currently-playing",
            params={"additional_types": "track,episode"},
        )

        async with response:
            if response.status == HTTPStatus.NO_CONTENT:
                return None

            if response.status == HTTPStatus.UNAUTHORIZED:
                raise ConfigEntryAuthFailed("Spotify authorization expired")

            if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                retry_after = response.headers.get("Retry-After", "30")
                raise UpdateFailed(f"Spotify rate limit reached; retry after {retry_after}s")

            try:
                response.raise_for_status()
            except ClientResponseError as err:
                raise UpdateFailed(f"Spotify API error: HTTP {err.status}") from err

            payload = await response.json()

        item = payload.get("item")
        if not item:
            return None

        item_type = item.get("type", "track")
        if item_type == "episode":
            artwork = ((item.get("images") or [{}])[0]).get("url")
            album_name = item.get("show", {}).get("name", "Podcast")
            artist = item.get("show", {}).get("publisher", "Podcast")
        else:
            album = item.get("album") or {}
            artwork = ((album.get("images") or [{}])[0]).get("url")
            album_name = album.get("name", "")
            artists = item.get("artists") or []
            artist = ", ".join(a.get("name", "") for a in artists if a.get("name"))

        return SpotifyTrack(
            track_id=item.get("id") or item.get("uri") or "",
            name=item.get("name", "Unknown"),
            artists=artist or "Unknown",
            album=album_name or "Unknown",
            artwork_url=artwork,
            duration_ms=int(item.get("duration_ms") or 0),
            progress_ms=int(payload.get("progress_ms") or 0),
            is_playing=bool(payload.get("is_playing")),
            item_type=item_type,
        )

    async def _async_get_json(self, path: str) -> dict[str, Any]:
        response = await self._oauth_session.async_request(
            "GET",
            f"{SPOTIFY_API_BASE}{path}",
        )
        async with response:
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise ConfigEntryAuthFailed("Spotify authorization expired")
            response.raise_for_status()
            return await response.json()

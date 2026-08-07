from __future__ import annotations

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SpotifyAmbientApi
from .cache import PaletteCache
from .colors import extract_palette
from .const import (
    DOMAIN,
    ENDING_INTERVAL,
    ENDING_THRESHOLD_SECONDS,
    IDLE_INTERVAL,
    LOGGER,
    PAUSED_INTERVAL,
    PLAYING_INTERVAL,
)
from .lights import SpotifyAmbientLightController
from .models import SpotifyAmbientData, SpotifyTrack


class SpotifyAmbientCoordinator(DataUpdateCoordinator[SpotifyAmbientData]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: SpotifyAmbientApi,
        cache: PaletteCache,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=IDLE_INTERVAL,
            config_entry=entry,
        )
        self.entry = entry
        self.api = api
        self.cache = cache
        self.light_controller = SpotifyAmbientLightController(hass, entry.options)
        self._last_track_id: str | None = None
        self._last_artwork_url: str | None = None
        self._last_palette = None

    async def _async_update_data(self) -> SpotifyAmbientData:
        try:
            track = await self.api.async_get_current_track()
        except ClientError as err:
            raise UpdateFailed(f"Error communicating with Spotify: {err}") from err

        self._set_next_interval(track)

        if track is None:
            self._last_track_id = None
            return SpotifyAmbientData(track=None, palette=self._last_palette)

        track_changed = track.track_id != self._last_track_id
        artwork_changed = track.artwork_url != self._last_artwork_url

        if track_changed:
            LOGGER.info(
                "Spotify track changed: %s — %s",
                track.artists,
                track.name,
            )
            self._last_track_id = track.track_id

        if track.is_playing and track.artwork_url and (track_changed or artwork_changed):
            palette = await self._async_get_palette(track.artwork_url)
            self._last_palette = palette
            self._last_artwork_url = track.artwork_url
            await self.light_controller.async_apply_palette(palette)

        return SpotifyAmbientData(track=track, palette=self._last_palette)

    def _set_next_interval(self, track: SpotifyTrack | None) -> None:
        if track is None:
            self.update_interval = IDLE_INTERVAL
        elif not track.is_playing:
            self.update_interval = PAUSED_INTERVAL
        elif track.remaining_seconds <= ENDING_THRESHOLD_SECONDS:
            self.update_interval = ENDING_INTERVAL
        else:
            self.update_interval = PLAYING_INTERVAL

    async def _async_get_palette(self, artwork_url: str):
        cached = self.cache.get(artwork_url)
        if cached:
            return cached

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(artwork_url) as response:
                response.raise_for_status()
                image_bytes = await response.read()
        except ClientError as err:
            raise UpdateFailed(f"Unable to download Spotify artwork: {err}") from err

        palette = await self.hass.async_add_executor_job(
            extract_palette,
            image_bytes,
            3,
        )
        await self.cache.async_set(artwork_url, palette)
        return palette

    def update_options(self) -> None:
        self.light_controller = SpotifyAmbientLightController(
            self.hass,
            self.entry.options,
        )

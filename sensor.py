from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpotifyAmbientCoordinator


async def async_setup_entry(
    hass,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            SpotifyAmbientTrackSensor(coordinator, entry),
            SpotifyAmbientStatusSensor(coordinator, entry),
        ]
    )


class SpotifyAmbientBaseSensor(
    CoordinatorEntity[SpotifyAmbientCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Spotify Ambient",
            manufacturer="Spotify Ambient",
        )


class SpotifyAmbientTrackSensor(SpotifyAmbientBaseSensor):
    _attr_name = "Current track"
    _attr_icon = "mdi:spotify"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_track"

    @property
    def native_value(self):
        track = self.coordinator.data.track if self.coordinator.data else None
        return track.name if track else "Nothing playing"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data or not data.track:
            return {}

        track = data.track
        attrs = {
            "artist": track.artists,
            "album": track.album,
            "is_playing": track.is_playing,
            "progress_ms": track.progress_ms,
            "duration_ms": track.duration_ms,
            "artwork_url": track.artwork_url,
            "item_type": track.item_type,
        }
        if data.palette:
            attrs["palette"] = [list(color) for color in data.palette]
        return attrs


class SpotifyAmbientStatusSensor(SpotifyAmbientBaseSensor):
    _attr_name = "Status"
    _attr_icon = "mdi:lightbulb-multiple"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data or not data.track:
            return "idle"
        return "playing" if data.track.is_playing else "paused"

    @property
    def extra_state_attributes(self):
        return {
            "poll_interval_seconds": (
                self.coordinator.update_interval.total_seconds()
                if self.coordinator.update_interval
                else None
            )
        }

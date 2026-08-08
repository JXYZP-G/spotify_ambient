from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .api import SpotifyAmbientApi
from .cache import PaletteCache
from .coordinator import SpotifyAmbientCoordinator
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]


@dataclass(slots=True)
class SpotifyAmbientRuntimeData:
    coordinator: SpotifyAmbientCoordinator


type SpotifyAmbientConfigEntry = ConfigEntry[SpotifyAmbientRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpotifyAmbientConfigEntry,
) -> bool:
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    oauth_session = OAuth2Session(hass, entry, implementation)
    api = SpotifyAmbientApi(oauth_session)

    cache = PaletteCache(hass)
    await cache.async_load()

    coordinator = SpotifyAmbientCoordinator(hass, entry, api, cache)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = SpotifyAmbientRuntimeData(coordinator=coordinator)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SpotifyAmbientConfigEntry,
) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(
    hass: HomeAssistant,
    entry: SpotifyAmbientConfigEntry,
) -> None:
    entry.runtime_data.coordinator.update_options()
    await entry.runtime_data.coordinator.async_request_refresh()

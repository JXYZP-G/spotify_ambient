from __future__ import annotations

import hashlib

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import CACHE_VERSION, DOMAIN
from .models import RGBColor


class PaletteCache:
    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, list[list[int]]]] = Store(
            hass,
            CACHE_VERSION,
            f"{DOMAIN}.palettes",
        )
        self._data: dict[str, list[list[int]]] = {}

    async def async_load(self) -> None:
        self._data = await self._store.async_load() or {}

    def _key(self, artwork_url: str) -> str:
        return hashlib.sha256(artwork_url.encode()).hexdigest()

    def get(self, artwork_url: str) -> list[RGBColor] | None:
        value = self._data.get(self._key(artwork_url))
        if not value:
            return None
        return [tuple(color) for color in value]  # type: ignore[list-item]

    async def async_set(
        self,
        artwork_url: str,
        palette: list[RGBColor],
    ) -> None:
        self._data[self._key(artwork_url)] = [list(color) for color in palette]
        await self._store.async_save(self._data)

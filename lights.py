from __future__ import annotations

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_ON,
)

from .const import (
    CONF_ACCENT_LIGHTS,
    CONF_BRIGHTNESS,
    CONF_ENABLED,
    CONF_PRIMARY_LIGHTS,
    CONF_SECONDARY_LIGHTS,
    CONF_TRANSITION,
    DEFAULT_BRIGHTNESS,
    DEFAULT_ENABLED,
    DEFAULT_TRANSITION,
)
from .models import RGBColor


class SpotifyAmbientLightController:
    def __init__(self, hass: HomeAssistant, options: dict) -> None:
        self.hass = hass
        self.options = options

    @property
    def enabled(self) -> bool:
        return bool(self.options.get(CONF_ENABLED, DEFAULT_ENABLED))

    @property
    def has_lights(self) -> bool:
        return any(
            self.options.get(key)
            for key in (
                CONF_PRIMARY_LIGHTS,
                CONF_SECONDARY_LIGHTS,
                CONF_ACCENT_LIGHTS,
            )
        )

    async def async_apply_palette(self, palette: list[RGBColor]) -> None:
        if not self.enabled or not self.has_lights:
            return

        brightness = int(self.options.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS))
        transition = float(self.options.get(CONF_TRANSITION, DEFAULT_TRANSITION))

        groups = (
            (self.options.get(CONF_PRIMARY_LIGHTS, []), palette[0]),
            (self.options.get(CONF_SECONDARY_LIGHTS, []), palette[1]),
            (self.options.get(CONF_ACCENT_LIGHTS, []), palette[2]),
        )

        for entity_ids, color in groups:
            if not entity_ids:
                continue

            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                SERVICE_TURN_ON,
                {
                    ATTR_ENTITY_ID: entity_ids,
                    ATTR_RGB_COLOR: list(color),
                    ATTR_BRIGHTNESS: brightness,
                    ATTR_TRANSITION: transition,
                },
                blocking=False,
            )

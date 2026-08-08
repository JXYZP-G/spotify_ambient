from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
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
    DOMAIN,
    LOGGER,
    SPOTIFY_API_BASE,
    SPOTIFY_SCOPES,
)


class SpotifyAmbientConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    VERSION = 1
    DOMAIN = DOMAIN

    @property
    def logger(self):
        return LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        return {
            "scope": SPOTIFY_SCOPES,
            "show_dialog": "false",
        }

    async def async_oauth_create_entry(
        self,
        data: dict[str, Any],
    ) -> ConfigFlowResult:
        access_token = data[CONF_TOKEN]["access_token"]
        session = async_get_clientsession(self.hass)

        async with session.get(
            f"{SPOTIFY_API_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as response:
            response.raise_for_status()
            profile = await response.json()

        spotify_user_id = profile["id"]
        await self.async_set_unique_id(spotify_user_id)
        self._abort_if_unique_id_configured()

        title = profile.get("display_name") or spotify_user_id
        return self.async_create_entry(title=title, data=data)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SpotifyAmbientOptionsFlow:
        return SpotifyAmbientOptionsFlow()


class SpotifyAmbientOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        light_selector = EntitySelector(
            EntitySelectorConfig(domain="light", multiple=True)
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PRIMARY_LIGHTS,
                    default=options.get(CONF_PRIMARY_LIGHTS, []),
                ): light_selector,
                vol.Optional(
                    CONF_SECONDARY_LIGHTS,
                    default=options.get(CONF_SECONDARY_LIGHTS, []),
                ): light_selector,
                vol.Optional(
                    CONF_ACCENT_LIGHTS,
                    default=options.get(CONF_ACCENT_LIGHTS, []),
                ): light_selector,
                vol.Required(
                    CONF_BRIGHTNESS,
                    default=options.get(CONF_BRIGHTNESS, DEFAULT_BRIGHTNESS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=255,
                        step=1,
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_TRANSITION,
                    default=options.get(CONF_TRANSITION, DEFAULT_TRANSITION),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=10,
                        step=0.5,
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Required(
                    CONF_ENABLED,
                    default=options.get(CONF_ENABLED, DEFAULT_ENABLED),
                ): BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

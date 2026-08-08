from __future__ import annotations

from homeassistant.components.application_credentials import (
    AuthImplementation,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
)

from .const import (
    SPOTIFY_AUTHORIZE_URL,
    SPOTIFY_SCOPES,
    SPOTIFY_TOKEN_URL,
)


class SpotifyOAuth2Implementation(LocalOAuth2ImplementationWithPkce):
    """Spotify OAuth implementation using Authorization Code with PKCE."""

    @property
    def extra_authorize_data(self) -> dict:
        data = {
            "scope": SPOTIFY_SCOPES,
            "show_dialog": "false",
        }
        data.update(super().extra_authorize_data)
        return data


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> AbstractOAuth2Implementation:
    """Return Spotify OAuth implementation.

    PKCE is used intentionally. Spotify accepts PKCE token exchange with the
    client ID and code verifier, so the client secret is not sent.
    """
    return SpotifyOAuth2Implementation(
        hass,
        auth_domain,
        credential.client_id,
        authorize_url=SPOTIFY_AUTHORIZE_URL,
        token_url=SPOTIFY_TOKEN_URL,
        client_secret="",
        code_verifier_length=128,
    )


async def async_get_description_placeholders(
    hass: HomeAssistant,
) -> dict[str, str]:
    return {
        "console_url": "https://developer.spotify.com/dashboard",
        "redirect_uri": "https://my.home-assistant.io/redirect/oauth",
    }

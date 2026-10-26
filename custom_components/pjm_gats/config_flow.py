"""Config flow for the PJM GATS integration."""

# pylint: disable=broad-exception-caught, abstract-method
import logging
from typing import Any, override

import probatio
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .coordinator import PjmGatsApiError, PjmGatsAuthError, PjmGatsClient

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_USERNAME): str,
        probatio.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_create_clientsession(hass)
    client = PjmGatsClient(session, data[CONF_USERNAME], data[CONF_PASSWORD])
    await client.login()

    return {"title": f"PJM GATS ({data[CONF_USERNAME]})"}


class PjmGatsConfigFlow(ConfigFlow, domain="pjm_gats"):
    """Handle a config flow for PJM GATS."""

    VERSION = 1

    @override
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except PjmGatsAuthError:
                errors["base"] = "invalid_auth"
            except PjmGatsApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

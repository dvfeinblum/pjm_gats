"""Test the PJM GATS config flow validation logic."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.pjm_gats.config_flow import validate_input
from custom_components.pjm_gats.coordinator import (
    PjmGatsApiError,
    PjmGatsAuthError,
)


async def test_validate_input_success(hass: HomeAssistant) -> None:
    """Test validate_input function with success."""
    with patch("custom_components.pjm_gats.config_flow.PjmGatsClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.login = AsyncMock()
        mock_client.get_home_page_data = AsyncMock(return_value={"generation_mwh": 123.456})

        result = await validate_input(
            hass, {"username": "user@example.com", "password": "correct_password"}
        )

        assert result == {"title": "PJM GATS (user@example.com)"}
        mock_client.login.assert_awaited_once()


async def test_validate_input_auth_error(hass: HomeAssistant) -> None:
    """Test validate_input function with auth error."""
    with patch("custom_components.pjm_gats.config_flow.PjmGatsClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.login = AsyncMock(side_effect=PjmGatsAuthError("Invalid credentials"))

        with pytest.raises(PjmGatsAuthError):
            await validate_input(
                hass, {"username": "user@example.com", "password": "wrong_password"}
            )


async def test_validate_input_api_error(hass: HomeAssistant) -> None:
    """Test validate_input function with API error."""
    with patch("custom_components.pjm_gats.config_flow.PjmGatsClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.login = AsyncMock(side_effect=PjmGatsApiError("Cannot connect"))

        with pytest.raises(PjmGatsApiError):
            await validate_input(hass, {"username": "user@example.com", "password": "password"})

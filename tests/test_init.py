"""Tests for the PJM GATS integration init module."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pjm_gats import async_setup_entry, async_unload_entry


async def test_async_setup_entry_creates_coordinator(
    hass: HomeAssistant,
    _mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test async_setup_entry creates coordinator."""
    config_entry = MockConfigEntry(
        domain="pjm_gats",
        title="PJM GATS (user@example.com)",
        data={"username": "user@example.com", "password": "secret"},
        unique_id="user@example.com",
    )
    config_entry.add_to_hass(hass)

    with patch("custom_components.pjm_gats.PjmGatsDataUpdateCoordinator") as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        # Mock the forward_entry_setups to avoid integration loading issues
        with patch.object(
            hass.config_entries, "async_forward_entry_setups", AsyncMock(return_value=True)
        ):
            await async_setup_entry(hass, config_entry)

        mock_coordinator_class.assert_called_once()
        mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()
        assert config_entry.runtime_data == mock_coordinator


async def test_async_unload_entry(
    hass: HomeAssistant,
) -> None:
    """Test async_unload_entry."""
    config_entry = MockConfigEntry(
        domain="pjm_gats",
        title="PJM GATS (user@example.com)",
        data={"username": "user@example.com", "password": "secret"},
        unique_id="user@example.com",
    )
    config_entry.add_to_hass(hass)

    # Set up the data in hass.data
    mock_coordinator = AsyncMock()
    hass.data["pjm_gats"] = {"coordinator": mock_coordinator}
    config_entry.runtime_data = mock_coordinator

    # Mock the unload_platforms to avoid integration loading issues
    with patch.object(
        hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)
    ) as mock_unload:
        await async_unload_entry(hass, config_entry)

    # Should call async_unload_platforms
    mock_unload.assert_awaited_once()

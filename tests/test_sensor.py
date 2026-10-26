"""Tests for the PJM GATS sensor platform."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.pjm_gats.coordinator import PjmGatsDataUpdateCoordinator
from custom_components.pjm_gats.sensor import SENSORS, PjmGatsSensor


async def test_sensor_creation(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test sensor creation."""
    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)
    coordinator.data = mock_pjm_gats_client.get_home_page_data.return_value

    # Test each sensor can be created
    for description in SENSORS:
        sensor = PjmGatsSensor(coordinator, description)
        assert sensor.entity_description == description
        # Unique ID is based on the config entry unique_id + sensor key
        # Since we're not using a config entry in this test, just check the format
        assert sensor.unique_id is not None


async def test_sensor_native_value(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test sensor native value."""
    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)
    coordinator.data = mock_pjm_gats_client.get_home_page_data.return_value

    for description in SENSORS:
        sensor = PjmGatsSensor(coordinator, description)
        expected_value = coordinator.data.get(description.data_key)
        assert sensor.native_value == expected_value


async def test_sensor_unique_ids(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test sensor unique IDs."""
    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)

    for description in SENSORS:
        sensor = PjmGatsSensor(coordinator, description)
        assert sensor.unique_id is not None

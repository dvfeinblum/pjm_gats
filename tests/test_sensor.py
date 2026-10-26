"""Tests for the PJM GATS sensor platform."""

from unittest.mock import AsyncMock

from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.pjm_gats.coordinator import PjmGatsDataUpdateCoordinator
from homeassistant.components.pjm_gats.sensor import SENSORS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry


async def test_sensor_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
    entity_registry: EntityRegistry,
) -> None:
    """Test sensor setup."""
    from homeassistant.components.pjm_gats.sensor import async_setup_entry

    coordinator = PjmGatsDataUpdateCoordinator(
        hass, mock_config_entry, mock_pjm_gats_client
    )
    mock_config_entry.runtime_data = coordinator

    await async_setup_entry(hass, mock_config_entry, lambda entities: None)
    await hass.async_block_till_done()

    # Verify all sensors are created
    for description in SENSORS:
        entity_id = f"sensor.pjm_gats_{description.key}"
        assert entity_registry.async_get(entity_id) is not None


async def test_sensor_values(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test sensor values."""
    from homeassistant.components.pjm_gats.sensor import (
        PjmGatsSensor,
        async_setup_entry,
    )

    coordinator = PjmGatsDataUpdateCoordinator(
        hass, mock_config_entry, mock_pjm_gats_client
    )
    mock_config_entry.runtime_data = coordinator

    entities_added: list[PjmGatsSensor] = []

    async def mock_add_entities(entities):
        entities_added.extend(entities)

    await async_setup_entry(hass, mock_config_entry, mock_add_entities)
    await hass.async_block_till_done()

    # Update coordinator data
    await coordinator.async_config_entry_first_refresh()
    await hass.async_block_till_done()

    # Verify each sensor returns the correct value
    for entity in entities_added:
        expected_value = mock_pjm_gats_client.get_home_page_data.return_value.get(
            entity.entity_description.data_key
        )
        assert entity.native_value == expected_value


async def test_sensor_unique_ids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
    entity_registry: EntityRegistry,
) -> None:
    """Test sensor unique IDs."""
    from homeassistant.components.pjm_gats.sensor import async_setup_entry

    coordinator = PjmGatsDataUpdateCoordinator(
        hass, mock_config_entry, mock_pjm_gats_client
    )
    mock_config_entry.runtime_data = coordinator

    await async_setup_entry(hass, mock_config_entry, lambda entities: None)
    await hass.async_block_till_done()

    for description in SENSORS:
        entity_id = f"sensor.pjm_gats_{description.key}"
        entry = entity_registry.async_get(entity_id)
        assert entry is not None
        # Unique ID should be username_key
        assert entry.unique_id == f"user@example.com_{description.key}"

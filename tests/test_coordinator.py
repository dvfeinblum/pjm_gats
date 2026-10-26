"""Tests for the PJM GATS coordinator."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.pjm_gats.coordinator import (
    PjmGatsApiError,
    PjmGatsAuthError,
    PjmGatsDataUpdateCoordinator,
)


async def test_coordinator_first_run(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test the coordinator on its first run."""
    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)
    data = await coordinator._async_update_data()

    assert data == mock_pjm_gats_client.get_home_page_data.return_value
    mock_pjm_gats_client.get_home_page_data.assert_awaited_once()


async def test_coordinator_auth_error(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test the coordinator handles auth error."""
    mock_pjm_gats_client.get_home_page_data.side_effect = PjmGatsAuthError("Auth failed")

    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_api_error(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test the coordinator handles API error."""
    mock_pjm_gats_client.get_home_page_data.side_effect = PjmGatsApiError("API error")

    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_subsequent_run(
    hass: HomeAssistant,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test the coordinator on subsequent runs."""
    coordinator = PjmGatsDataUpdateCoordinator(hass, mock_pjm_gats_client)

    # First run
    data1 = await coordinator._async_update_data()
    assert data1 == mock_pjm_gats_client.get_home_page_data.return_value

    # Second run with updated data
    updated_data = {
        "generation_mwh": 234.567,
        "certificates_active": 15,
        "certificates_ceps": 8,
        "certificates_on_bb": 5,
        "certificates_reserved": 3,
        "certificates_total": 31,
        "certificates_active_hourly": 2.5,
        "certificates_ceps_hourly": 1.25,
        "certificates_reserved_hourly": 0.5,
        "generator_id": "GEN123456",
        "generator_plant": "Test Plant - Unit 1",
        "generator_status": "ACT",
    }
    mock_pjm_gats_client.get_home_page_data.return_value = updated_data

    data2 = await coordinator._async_update_data()
    assert data2 == updated_data
    assert mock_pjm_gats_client.get_home_page_data.call_count == 2  # noqa: PLR2004

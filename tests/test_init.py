"""Tests for the PJM GATS integration."""

from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.pjm_gats.const import DOMAIN
from homeassistant.components.pjm_gats.coordinator import (
    PjmGatsApiError,
    PjmGatsAuthError,
)
from homeassistant.components.recorder import Recorder
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_setup_unload_entry(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test successful setup and unload of a config entry."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    mock_pjm_gats_client.login.assert_awaited_once()
    mock_pjm_gats_client.get_home_page_data.assert_awaited_once()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.data.get(DOMAIN)


@pytest.mark.parametrize(
    ("login_side_effect", "expected_state"),
    [
        (
            PjmGatsApiError("Cannot connect"),
            ConfigEntryState.SETUP_RETRY,
        ),
        (
            PjmGatsAuthError("Invalid credentials"),
            ConfigEntryState.SETUP_ERROR,
        ),
    ],
)
async def test_login_error(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
    login_side_effect: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test for login error."""
    mock_pjm_gats_client.login.side_effect = login_side_effect

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is expected_state


async def test_get_home_page_data_error(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test for API error when getting home page data."""
    mock_pjm_gats_client.get_home_page_data.side_effect = PjmGatsApiError(
        "Home page error"
    )

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY

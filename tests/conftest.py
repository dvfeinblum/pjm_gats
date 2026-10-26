"""Fixtures for the PJM GATS integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.pjm_gats.const import DOMAIN
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return the default mocked config entry."""
    config_entry = MockConfigEntry(
        title="PJM GATS (user@example.com)",
        domain=DOMAIN,
        data={
            "username": "user@example.com",
            "password": "supersecret",
        },
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def mock_pjm_gats_client() -> Generator[AsyncMock]:
    """Mock PJM GATS client."""
    with patch(
        "homeassistant.components.pjm_gats.coordinator.PjmGatsClient", autospec=True
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.username = "user@example.com"
        client.get_home_page_data.return_value = {
            "generation_mwh": 123.456,
            "certificates_active": 10,
            "certificates_ceps": 5,
            "certificates_on_bb": 3,
            "certificates_reserved": 2,
            "certificates_total": 20,
            "certificates_active_hourly": 1.5,
            "certificates_ceps_hourly": 0.75,
            "certificates_reserved_hourly": 0.25,
            "generator_id": "GEN123456",
            "generator_plant": "Test Plant - Unit 1",
            "generator_status": "ACT",
        }
        yield client


@pytest.fixture(autouse=True)
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.pjm_gats.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry

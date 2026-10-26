"""Fixtures for the PJM GATS integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_pjm_gats_client() -> Generator[AsyncMock]:
    """Mock PJM GATS client."""
    with patch(
        "custom_components.pjm_gats.coordinator.PjmGatsClient", autospec=True
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

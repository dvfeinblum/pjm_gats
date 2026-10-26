"""Test the PJM GATS config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry, get_schema_suggested_value

from homeassistant import config_entries
from homeassistant.components.pjm_gats.const import DOMAIN
from homeassistant.components.pjm_gats.coordinator import (
    PjmGatsApiError,
    PjmGatsAuthError,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_form(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_pjm_gats_client: AsyncMock
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
    ) as mock_validate:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "user@example.com",
                "password": "supersecret",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "PJM GATS (user@example.com)"
    assert result2["data"] == {
        "username": "user@example.com",
        "password": "supersecret",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_validate.call_count == 1


@pytest.mark.parametrize(
    ("api_exception", "expected_error"),
    [
        (PjmGatsAuthError("Invalid credentials"), "invalid_auth"),
        (PjmGatsApiError("Cannot connect"), "cannot_connect"),
    ],
)
async def test_form_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    api_exception: Exception,
    expected_error: str,
) -> None:
    """Test we handle exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
        side_effect=api_exception,
    ) as mock_validate:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "user@example.com",
                "password": "supersecret",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}
    # On error, the form should have the previous user input as suggested values.
    data_schema = result2["data_schema"].schema
    assert get_schema_suggested_value(data_schema, "username") == "user@example.com"
    assert get_schema_suggested_value(data_schema, "password") == "supersecret"
    assert mock_validate.call_count == 1

    # Retry with success
    with patch("homeassistant.components.pjm_gats.config_flow.validate_input"):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "user@example.com",
                "password": "supersecret",
            },
        )
    assert result3["type"] is FlowResultType.CREATE_ENTRY


async def test_form_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test user input for config_entry that already exists."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
    ) as mock_validate:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "user@example.com",
                "password": "supersecret",
            },
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
    assert mock_validate.call_count == 0


async def test_form_not_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_pjm_gats_client: AsyncMock,
) -> None:
    """Test user input for config_entry different than the existing one."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
    ) as mock_validate:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "other@example.com",
                "password": "differentpass",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "PJM GATS (other@example.com)"
    assert result2["data"] == {
        "username": "other@example.com",
        "password": "differentpass",
    }
    assert len(mock_setup_entry.mock_calls) == 2
    assert mock_validate.call_count == 1


async def test_form_valid_reauth(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_pjm_gats_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that we can handle a valid reauth."""
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    hass.config.components.add(DOMAIN)
    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"
    assert result["context"]["source"] == "reauth"
    assert result["context"]["title_placeholders"] == {"name": mock_config_entry.title}

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
        side_effect=PjmGatsAuthError("Invalid credentials"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["data_schema"].schema.keys() == {
            "username",
            "password",
        }

    with patch(
        "homeassistant.components.pjm_gats.config_flow.validate_input",
    ) as mock_validate:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "user@example.com", "password": "newsecret"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    await hass.async_block_till_done()
    assert mock_config_entry.data == {
        "username": "user@example.com",
        "password": "newsecret",
    }
    assert mock_validate.call_count == 1

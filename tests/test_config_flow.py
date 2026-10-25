"""Tests for the config and options flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gotabiblioteken.const import (
    CONF_BRANCHES,
    CUSTOMER_ID,
    DOMAIN,
)

BRANCHES = ["Borensbergs bibliotek", "Motala bibliotek"]

FETCH_NAMES = "custom_components.gotabiblioteken.config_flow.async_fetch_branch_names"


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    with patch(FETCH_NAMES, AsyncMock(return_value=BRANCHES)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        with patch(
            "custom_components.gotabiblioteken.async_setup_entry",
            return_value=True,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_BRANCHES: ["Motala bibliotek"]},
            )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Götabiblioteken"
    assert result2["data"] == {CONF_BRANCHES: ["Motala bibliotek"]}


async def test_single_instance_aborts(hass: HomeAssistant) -> None:
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUSTOMER_ID,
        version=2,
        data={CONF_BRANCHES: ["Motala bibliotek"]},
    ).add_to_hass(hass)

    with patch(FETCH_NAMES, AsyncMock(return_value=BRANCHES)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_cannot_connect_aborts(hass: HomeAssistant) -> None:
    with patch(FETCH_NAMES, AsyncMock(side_effect=Exception("boom"))):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_options_flow_updates_favorites(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUSTOMER_ID,
        version=2,
        data={CONF_BRANCHES: ["Motala bibliotek"]},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.gotabiblioteken.config_flow.async_fetch_branch_names",
        AsyncMock(return_value=BRANCHES),
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_BRANCHES: ["Motala bibliotek", "Borensbergs bibliotek"]},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_BRANCHES: ["Motala bibliotek", "Borensbergs bibliotek"]
    }

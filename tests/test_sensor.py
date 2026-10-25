"""End-to-end setup: config entry -> coordinator -> sensors."""

from unittest.mock import AsyncMock, patch

from freezegun import freeze_time

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gotabiblioteken.const import (
    CONF_BRANCHES,
    CONF_INCLUDE_SELF_SERVICE,
    CUSTOMER_ID,
    DOMAIN,
)

from .const import SAMPLE_PAYLOAD

FETCH_DATES = "custom_components.gotabiblioteken.coordinator.async_fetch_dates"


async def _setup(
    hass: HomeAssistant,
    branches,
    include_self_service=True,
    now="2026-10-20 12:00:00",
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUSTOMER_ID,
        data={
            CONF_BRANCHES: branches,
            CONF_INCLUDE_SELF_SERVICE: include_self_service,
        },
    )
    entry.add_to_hass(hass)
    # The test hass defaults to US/Pacific; pin to UTC so the naive freeze_time
    # string matches the computed local time. (Context-manager freeze form —
    # the decorator form doesn't reach dt_util.now() across the awaited setup.)
    await hass.config.async_set_time_zone("UTC")
    with freeze_time(now), patch(FETCH_DATES, AsyncMock(return_value=SAMPLE_PAYLOAD)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _entity_id(hass: HomeAssistant, entry, branch: str) -> str:
    unique_id = f"{entry.entry_id}_{slugify(branch)}"
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None, f"no sensor registered for {branch}"
    return entity_id


async def test_sensor_created_per_favorite(hass: HomeAssistant) -> None:
    entry = await _setup(hass, ["Motala bibliotek", "Borensbergs bibliotek"])

    motala_id = _entity_id(hass, entry, "Motala bibliotek")
    borensberg_id = _entity_id(hass, entry, "Borensbergs bibliotek")
    assert motala_id and borensberg_id

    motala = hass.states.get(motala_id)
    assert motala.state == "10:00–19:00"
    assert motala.attributes["open_now"] is True
    assert motala.attributes["status"] == "staffed"
    assert motala.attributes["branch"] == "Motala bibliotek"

    borensberg = hass.states.get(borensberg_id)
    assert borensberg.state == "09:00–14:00"
    assert borensberg.attributes["self_service_summary"] == "14:00–21:00"
    assert borensberg.attributes["status"] == "staffed"  # staffed 09–14 at 12:00
    assert len(borensberg.attributes["shifts"]) == 2


async def test_self_service_toggle_affects_open_now(hass: HomeAssistant) -> None:
    # At 20:00 Borensbergs is only in its self-service window (14–21), so with
    # self-service NOT counted as open, the sensor must read closed.
    entry = await _setup(
        hass,
        ["Borensbergs bibliotek"],
        include_self_service=False,
        now="2026-10-20 20:00:00",
    )
    state = hass.states.get(_entity_id(hass, entry, "Borensbergs bibliotek"))
    assert state.attributes["status"] == "self_service"
    assert state.attributes["open_now"] is False


async def test_unload(hass: HomeAssistant) -> None:
    entry = await _setup(hass, ["Motala bibliotek"])
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN not in hass.data or entry.entry_id not in hass.data.get(DOMAIN, {})

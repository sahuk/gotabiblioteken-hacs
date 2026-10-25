"""End-to-end setup: config entry -> coordinator -> per-library devices."""

from unittest.mock import AsyncMock, patch

from freezegun import freeze_time
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import slugify
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gotabiblioteken.const import (
    CONF_BRANCHES,
    CUSTOMER_ID,
    DOMAIN,
)

from .const import SAMPLE_PAYLOAD

FETCH_DATES = "custom_components.gotabiblioteken.coordinator.async_fetch_dates"
BORENSBERG = "Borensbergs bibliotek"
MOTALA = "Motala bibliotek"
PLATFORM_BY_KEY = {
    "hours": "sensor",
    "staffed": "binary_sensor",
    "self_service": "binary_sensor",
}


def _entry(branches: list[str], version: int = 2, **extra_data) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUSTOMER_ID,
        version=version,
        data={CONF_BRANCHES: branches, **extra_data},
    )


async def _setup(
    hass: HomeAssistant, entry: MockConfigEntry, now: str = "2026-10-20 12:00:00"
) -> MockConfigEntry:
    entry.add_to_hass(hass)
    # The test hass defaults to US/Pacific; pin to UTC so the naive freeze_time
    # string matches the computed local time. (Context-manager freeze form —
    # the decorator form doesn't reach dt_util.now() across the awaited setup.)
    await hass.config.async_set_time_zone("UTC")
    with freeze_time(now), patch(FETCH_DATES, AsyncMock(return_value=SAMPLE_PAYLOAD)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _entity_id(hass: HomeAssistant, entry, branch: str, key: str) -> str:
    unique_id = f"{entry.entry_id}_{slugify(branch)}_{key}"
    entity_id = er.async_get(hass).async_get_entity_id(
        PLATFORM_BY_KEY[key], DOMAIN, unique_id
    )
    assert entity_id is not None, f"no {key} entity for {branch}"
    return entity_id


def _state(hass: HomeAssistant, entry, branch: str, key: str):
    state = hass.states.get(_entity_id(hass, entry, branch, key))
    assert state is not None
    return state


async def test_one_device_with_three_entities_per_library(hass: HomeAssistant) -> None:
    entry = await _setup(hass, _entry([MOTALA, BORENSBERG]))

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    devices = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    assert sorted(str(d.name) for d in devices) == [BORENSBERG, MOTALA]
    for device in devices:
        entities = er.async_entries_for_device(ent_reg, device.id)
        assert sorted(str(e.translation_key) for e in entities) == [
            "hours",
            "self_service",
            "staffed",
        ]

    # Entity IDs are "<device>_<translated name>" (test hass runs in English).
    assert _entity_id(hass, entry, MOTALA, "hours") == (
        "sensor.motala_bibliotek_opening_hours"
    )
    assert _entity_id(hass, entry, MOTALA, "self_service") == (
        "binary_sensor.motala_bibliotek_self_service_access"
    )

    hours = _state(hass, entry, MOTALA, "hours")
    assert hours.state == "10:00–19:00"
    assert hours.attributes["branch"] == MOTALA
    assert hours.attributes["status"] == "staffed"
    assert _state(hass, entry, MOTALA, "staffed").state == "on"
    # Bemannat is Ja/Nej, not a door; only Meröppet is about getting in.
    assert "device_class" not in _state(hass, entry, MOTALA, "staffed").attributes
    assert (
        _state(hass, entry, MOTALA, "self_service").attributes["device_class"] == "door"
    )


@pytest.mark.parametrize(
    ("now", "staffed", "self_service"),
    [
        ("2026-10-20 12:00:00", "on", "on"),  # staffed 09–14
        ("2026-10-20 15:00:00", "off", "on"),  # Meröppet 14–21
        ("2026-10-20 22:00:00", "off", "off"),  # closed
    ],
)
async def test_open_states_through_the_day(
    hass: HomeAssistant, now: str, staffed: str, self_service: str
) -> None:
    entry = await _setup(hass, _entry([BORENSBERG]), now=now)

    assert _state(hass, entry, BORENSBERG, "hours").state == (
        "09:00–14:00, Meröppet 14:00–21:00"
    )
    staffed_state = _state(hass, entry, BORENSBERG, "staffed")
    assert staffed_state.state == staffed
    assert staffed_state.attributes["hours"] == "09:00–14:00"
    self_service_state = _state(hass, entry, BORENSBERG, "self_service")
    assert self_service_state.state == self_service
    assert self_service_state.attributes["hours"] == "09:00–21:00"


async def test_removing_favorite_removes_its_device(hass: HomeAssistant) -> None:
    entry = await _setup(hass, _entry([MOTALA, BORENSBERG]))
    staffed_id = _entity_id(hass, entry, BORENSBERG, "staffed")

    with (
        freeze_time("2026-10-20 12:00:00"),
        patch(FETCH_DATES, AsyncMock(return_value=SAMPLE_PAYLOAD)),
    ):
        hass.config_entries.async_update_entry(entry, options={CONF_BRANCHES: [MOTALA]})
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [d.name for d in devices] == [MOTALA]
    assert er.async_get(hass).async_get(staffed_id) is None


async def test_stale_device_removed_even_if_api_is_down(hass: HomeAssistant) -> None:
    entry = await _setup(hass, _entry([MOTALA, BORENSBERG]))

    with patch(FETCH_DATES, AsyncMock(side_effect=Exception("API down"))):
        hass.config_entries.async_update_entry(entry, options={CONF_BRANCHES: [MOTALA]})
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [d.name for d in devices] == [MOTALA]


async def test_migrates_v1_entry(hass: HomeAssistant) -> None:
    entry = _entry([BORENSBERG], version=1, include_self_service=True)
    entry.add_to_hass(hass)
    old_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Götabiblioteken",
    )
    old_entity = er.async_get(hass).async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_{slugify(BORENSBERG)}",
        config_entry=entry,
        device_id=old_device.id,
    )

    await _setup(hass, entry)

    assert entry.version == 2
    assert entry.data == {CONF_BRANCHES: [BORENSBERG]}
    assert er.async_get(hass).async_get(old_entity.entity_id) is None
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [d.name for d in devices] == [BORENSBERG]
    assert _state(hass, entry, BORENSBERG, "staffed").state == "on"


async def test_unload(hass: HomeAssistant) -> None:
    entry = await _setup(hass, _entry([MOTALA]))
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN not in hass.data or entry.entry_id not in hass.data.get(DOMAIN, {})

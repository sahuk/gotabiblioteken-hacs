"""Sensor platform: today's opening hours (all, and staffed) for each library."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GotaCoordinator
from .entity import GotaBranchEntity, favorite_branches


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the hours sensors for each favorite library."""
    coordinator: GotaCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors: list[SensorEntity] = []
    for branch in favorite_branches(entry):
        sensors.append(LibraryHoursSensor(coordinator, entry, branch))
        sensors.append(LibraryStaffedHoursSensor(coordinator, entry, branch))
    async_add_entities(sensors)


class LibraryHoursSensor(GotaBranchEntity, SensorEntity):
    """Today's shifts, e.g. `09:00–14:00, Self-service 14:00–21:00`."""

    def __init__(
        self, coordinator: GotaCoordinator, entry: ConfigEntry, branch: str
    ) -> None:
        super().__init__(coordinator, entry, branch, "hours")

    @property
    def native_value(self) -> str:
        return self._compute()["hours"]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        return self._compute()["attributes"]


class LibraryStaffedHoursSensor(GotaBranchEntity, SensorEntity):
    """Today's staffed hours only, e.g. `09:00–14:00`, or `Not staffed`.

    The hours companion of the Staffed binary sensor: opt-in for people who
    need in-person help, so it is created disabled like that sensor.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: GotaCoordinator, entry: ConfigEntry, branch: str
    ) -> None:
        super().__init__(coordinator, entry, branch, "staffed_hours")

    @property
    def native_value(self) -> str:
        return self._compute()["staffed"]["hours"]

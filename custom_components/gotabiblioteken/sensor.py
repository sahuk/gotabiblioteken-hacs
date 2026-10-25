"""Sensor platform: today's opening hours for each favorite library."""

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
    """Create the hours sensor for each favorite library."""
    coordinator: GotaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LibraryHoursSensor(coordinator, entry, branch)
        for branch in favorite_branches(entry)
    )


class LibraryHoursSensor(GotaBranchEntity, SensorEntity):
    """Today's shifts, e.g. `09:00–14:00, Meröppet 14:00–21:00`."""

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

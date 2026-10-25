"""Binary sensors: is each favorite library staffed / accessible right now."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GotaCoordinator
from .data import AccessKey
from .entity import GotaBranchEntity, favorite_branches

# "staffed": someone is working there. "self_service": a cardholder can get in
# (Meröppet or staffed hours).
KEYS: tuple[AccessKey, ...] = ("staffed", "self_service")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the Bemannat and Meröppet sensors for each favorite library."""
    coordinator: GotaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LibraryOpenSensor(coordinator, entry, branch, key)
        for branch in favorite_branches(entry)
        for key in KEYS
    )


class LibraryOpenSensor(GotaBranchEntity, BinarySensorEntity):
    """On/off for one kind of access; `hours` lists exactly when it's on."""

    def __init__(
        self,
        coordinator: GotaCoordinator,
        entry: ConfigEntry,
        branch: str,
        key: AccessKey,
    ) -> None:
        super().__init__(coordinator, entry, branch, key)
        self._key = key
        # Meröppet is about getting in, so it reads as an open/closed door.
        # Bemannat reads Ja/Nej (state translations): showing "closed" while
        # the library is open for Meröppet would be wrong.
        if key == "self_service":
            self._attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def is_on(self) -> bool:
        return self._compute()[self._key]["is_on"]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        return {"hours": self._compute()[self._key]["hours"]}

"""Sensor platform: one "opening hours today" sensor per favorite library."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from .const import (
    CONF_BRANCHES,
    CONF_INCLUDE_SELF_SERVICE,
    DOMAIN,
    LOCAL_REFRESH_INTERVAL,
)
from .coordinator import GotaCoordinator
from .data import compute_branch_today


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one sensor for each selected favorite library."""
    coordinator: GotaCoordinator = hass.data[DOMAIN][entry.entry_id]
    options = {**entry.data, **entry.options}
    branches: list[str] = options.get(CONF_BRANCHES, [])
    include_self_service: bool = options.get(CONF_INCLUDE_SELF_SERVICE, True)

    async_add_entities(
        LibraryHoursSensor(coordinator, entry, branch, include_self_service)
        for branch in branches
    )


class LibraryHoursSensor(CoordinatorEntity[GotaCoordinator], SensorEntity):
    """Today's opening hours for a single library branch."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: GotaCoordinator,
        entry: ConfigEntry,
        branch: str,
        include_self_service: bool,
    ) -> None:
        super().__init__(coordinator)
        self._branch = branch
        self._include_self_service = include_self_service
        self._attr_unique_id = f"{entry.entry_id}_{slugify(branch)}"
        self._attr_name = f"Öppettider {branch.strip()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Götabiblioteken",
            manufacturer="Axiell",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._unsub_timer: CALLBACK_TYPE | None = None

    def _compute(self) -> dict[str, Any]:
        payload = self.coordinator.data or {}
        return compute_branch_today(
            payload, self._branch, self._include_self_service, dt_util.now()
        )

    @property
    def native_value(self) -> str:
        state: str = self._compute()["state"]
        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes: dict[str, Any] = self._compute()["attributes"]
        return attributes

    @property
    def icon(self) -> str:
        return "mdi:door-open" if self._compute()["open_now"] else "mdi:door-closed"

    @property
    def available(self) -> bool:
        return super().available and bool((self.coordinator.data or {}).get("dates"))

    async def async_added_to_hass(self) -> None:
        """Recompute locally every minute for open_now / midnight rollover."""
        await super().async_added_to_hass()
        self._unsub_timer = async_track_time_interval(
            self.hass, self._handle_local_refresh, LOCAL_REFRESH_INTERVAL
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _handle_local_refresh(self, _now: datetime) -> None:
        self.async_write_ha_state()

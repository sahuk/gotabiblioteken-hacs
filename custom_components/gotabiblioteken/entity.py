"""Shared base for the per-library entities."""

from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from .const import CONF_BRANCHES, DOMAIN, LOCAL_REFRESH_INTERVAL
from .coordinator import GotaCoordinator
from .data import BranchToday, compute_branch_today, labels_for
from .websites import website_for


def favorite_branches(entry: ConfigEntry) -> list[str]:
    """The favorite libraries; options (Configure) override the initial setup."""
    branches: list[str] = {**entry.data, **entry.options}.get(CONF_BRANCHES, [])
    return branches


def branch_device_id(entry: ConfigEntry, branch: str) -> str:
    """Device identifier for one favorite library."""
    return f"{entry.entry_id}_{slugify(branch)}"


class GotaBranchEntity(CoordinatorEntity[GotaCoordinator]):
    """One entity of a library device; recomputes locally every minute."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GotaCoordinator,
        entry: ConfigEntry,
        branch: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._branch = branch
        self._attr_translation_key = key
        self._attr_unique_id = f"{branch_device_id(entry, branch)}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, branch_device_id(entry, branch))},
            name=branch.strip(),
            manufacturer="Axiell",
            configuration_url=website_for(branch),
            entry_type=DeviceEntryType.SERVICE,
        )
        self._unsub_timer: CALLBACK_TYPE | None = None

    def _compute(self) -> BranchToday:
        return compute_branch_today(
            self.coordinator.data or {},
            self._branch,
            dt_util.now(),
            labels_for(self.hass.config.language),
        )

    @property
    def available(self) -> bool:
        return super().available and bool((self.coordinator.data or {}).get("dates"))

    async def async_added_to_hass(self) -> None:
        """Recompute locally every minute for open/closed and midnight rollover."""
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

"""The Götabiblioteken opening-hours integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import GotaCoordinator
from .entity import branch_device_id, favorite_branches

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Götabiblioteken from a config entry."""
    _async_remove_stale_devices(hass, entry)
    session = async_get_clientsession(hass)
    coordinator = GotaCoordinator(hass, session)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


def _async_remove_stale_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Drop devices (and their entities) for libraries no longer favorited."""
    wanted = {
        (DOMAIN, branch_device_id(entry, branch)) for branch in favorite_branches(entry)
    }
    dev_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        if not device.identifiers & wanted:
            dev_reg.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    if entry.version == 1:
        # v1 had one shared device and one sensor per library, plus a setup
        # toggle for counting Meröppet as open. v2 makes a device per library
        # with separate Bemannat/Meröppet sensors, so drop the toggle and the
        # old entities. Setup recreates them and detaches the old shared
        # device as stale.
        removed = "include_self_service"
        data = {k: v for k, v in entry.data.items() if k != removed}
        options = {k: v for k, v in entry.options.items() if k != removed}
        ent_reg = er.async_get(hass)
        for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            ent_reg.async_remove(entity.entity_id)
        hass.config_entries.async_update_entry(
            entry, data=data, options=options, version=2
        )
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options (favorites) change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

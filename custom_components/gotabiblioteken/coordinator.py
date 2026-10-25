"""Data update coordinator for the Götabiblioteken integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import async_fetch_dates
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GotaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the opening-hours API and shares the payload with all sensors."""

    def __init__(self, hass: HomeAssistant, session: ClientSession) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._session = session

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await async_fetch_dates(self._session)
        except Exception as err:  # surfaced as UpdateFailed
            raise UpdateFailed(f"Error fetching opening hours: {err}") from err

"""Config and options flow for the Götabiblioteken integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import async_fetch_branch_names
from .const import CONF_BRANCHES, CUSTOMER_ID, DOMAIN


def _schema(branch_options: list[str], defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_BRANCHES,
                default=defaults.get(CONF_BRANCHES, []),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=branch_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=True,
                )
            ),
        }
    )


class GotaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(CUSTOMER_ID)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Götabiblioteken", data=user_input)

        session = async_get_clientsession(self.hass)
        try:
            branches = await async_fetch_branch_names(session)
        except Exception:  # noqa: BLE001
            return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(branches, {}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GotaOptionsFlow(config_entry)


class GotaOptionsFlow(OptionsFlow):
    """Change favorite libraries after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._entry.data, **self._entry.options}

        session = async_get_clientsession(self.hass)
        try:
            branches = await async_fetch_branch_names(session)
        except Exception:  # noqa: BLE001 - fall back to already-selected names
            branches = current.get(CONF_BRANCHES, [])

        # Make sure previously selected branches remain selectable even if the
        # API list changes.
        branches = sorted(
            set(branches) | set(current.get(CONF_BRANCHES, [])), key=str.lower
        )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(branches, current),
        )

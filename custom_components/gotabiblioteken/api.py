"""Thin async client for the Axiell opening-hours API."""

from __future__ import annotations

import asyncio

from aiohttp import ClientSession

from .const import API_URL, CUSTOMER_ID
from .data import ApiPayload, branch_names


async def async_fetch_dates(
    session: ClientSession,
    days: int = 2,
    customer_id: str = CUSTOMER_ID,
) -> ApiPayload:
    """Fetch the raw opening-hours payload (today plus `days - 1` more)."""
    url = API_URL.format(customer_id=customer_id)
    params: dict[str, str | int] = {
        "locale": "sv_SE",
        "daysFromNow": 0,
        "numOfDays": days,
    }
    async with asyncio.timeout(20):
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            payload: ApiPayload = await resp.json()
            return payload


async def async_fetch_branch_names(
    session: ClientSession,
    customer_id: str = CUSTOMER_ID,
) -> list[str]:
    """Fetch the current list of branch names for the config/options flow.

    Fetches a week because the API omits branches on days they are closed;
    unioning several days yields the full roster.
    """
    payload = await async_fetch_dates(session, days=7, customer_id=customer_id)
    return branch_names(payload)

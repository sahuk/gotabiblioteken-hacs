"""Thin async client for the Axiell opening-hours API."""

from __future__ import annotations

import asyncio
import json

from aiohttp import ClientResponse, ClientSession

from .const import API_URL, CUSTOMER_ID
from .data import ApiPayload, branch_names

# A week of hours for every branch is a few tens of KB; anything near this is
# not an opening-hours payload and is refused before it is parsed.
MAX_RESPONSE_BYTES = 1024 * 1024


class ResponseTooLargeError(ValueError):
    """The API answered with more than MAX_RESPONSE_BYTES."""


async def _read_capped(resp: ClientResponse, limit: int) -> bytes:
    """The body, or ResponseTooLargeError past `limit` bytes.

    The cap counts decompressed bytes, as read from `resp.content`. The
    Content-Length shortcut counts bytes on the wire (compressed, if the
    server compresses), so it can only reject early, never let more through.
    """
    if resp.content_length is not None and resp.content_length > limit:
        raise ResponseTooLargeError(f"Response is {resp.content_length} bytes")
    body = bytearray()
    # read(n) may return less than n before EOF, so loop; stop at limit + 1.
    while chunk := await resp.content.read(limit + 1 - len(body)):
        body += chunk
        if len(body) > limit:
            raise ResponseTooLargeError(f"Response exceeds {limit} bytes")
    return bytes(body)


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
            body = await _read_capped(resp, MAX_RESPONSE_BYTES)
    payload: ApiPayload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Unexpected response: not a JSON object")
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

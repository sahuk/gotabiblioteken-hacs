"""The API client against a local aiohttp server: size cap and response shape."""

import json
from unittest.mock import patch

from aiohttp import web
import pytest

from custom_components.gotabiblioteken import api
from custom_components.gotabiblioteken.api import (
    MAX_RESPONSE_BYTES,
    ResponseTooLargeError,
    async_fetch_branch_names,
    async_fetch_dates,
)

from .const import SAMPLE_PAYLOAD

OVERSIZED = b'{"dates": [' + b" " * MAX_RESPONSE_BYTES + b"]}"


async def _sized(request: web.Request) -> web.Response:
    return web.Response(body=json.dumps(SAMPLE_PAYLOAD).encode())


async def _oversized(request: web.Request) -> web.Response:
    return web.Response(body=OVERSIZED, content_type="application/json")


async def _oversized_chunked(request: web.Request) -> web.StreamResponse:
    # No Content-Length: the cap must hold while streaming.
    resp = web.StreamResponse()
    resp.enable_chunked_encoding()
    await resp.prepare(request)
    for start in range(0, len(OVERSIZED), 64 * 1024):
        await resp.write(OVERSIZED[start : start + 64 * 1024])
    await resp.write_eof()
    return resp


async def _sized_chunked(request: web.Request) -> web.StreamResponse:
    resp = web.StreamResponse()
    resp.enable_chunked_encoding()
    await resp.prepare(request)
    await resp.write(json.dumps(SAMPLE_PAYLOAD).encode())
    await resp.write_eof()
    return resp


async def _not_an_object(request: web.Request) -> web.Response:
    return web.json_response([1, 2, 3])


@pytest.fixture
async def client(aiohttp_client, socket_enabled):
    """A local server standing in for the API (sockets are off by default)."""
    app = web.Application()
    for name, handler in [
        ("sized", _sized),
        ("oversized", _oversized),
        ("oversized-chunked", _oversized_chunked),
        ("sized-chunked", _sized_chunked),
        ("list", _not_an_object),
    ]:
        app.router.add_get(f"/customers/{name}/openinghours", handler)
    test_client = await aiohttp_client(app)
    url = f"{test_client.make_url('/')}customers/{{customer_id}}/openinghours"
    with patch.object(api, "API_URL", url):
        yield test_client


@pytest.mark.parametrize("customer_id", ["sized", "sized-chunked"])
async def test_fetch_parses_payload(client, customer_id):
    payload = await async_fetch_dates(client.session, customer_id=customer_id)
    assert payload == SAMPLE_PAYLOAD
    assert await async_fetch_branch_names(client.session, customer_id) == [
        "Borensbergs bibliotek",
        "Finspångs huvudbibliotek",
        "Mjölby bibliotek",
        "Motala bibliotek",
    ]


@pytest.mark.parametrize("customer_id", ["oversized", "oversized-chunked"])
async def test_oversized_response_is_refused(client, customer_id):
    with pytest.raises(ResponseTooLargeError):
        await async_fetch_dates(client.session, customer_id=customer_id)


async def test_non_object_response_is_refused(client):
    with pytest.raises(ValueError, match="not a JSON object"):
        await async_fetch_dates(client.session, customer_id="list")


def test_sample_payload_is_far_below_the_cap():
    assert len(json.dumps(SAMPLE_PAYLOAD)) * 100 < MAX_RESPONSE_BYTES

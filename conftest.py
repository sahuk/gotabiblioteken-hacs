"""Shared pytest fixtures for the test suite."""

from collections.abc import Generator
from unittest.mock import PropertyMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow tests to load the custom integration."""
    yield


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Create entities that are disabled by default as enabled (as HA core does)."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        new_callable=PropertyMock,
        return_value=True,
    ):
        yield

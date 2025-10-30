"""Pytest fixtures for Ennatuurlijk Disruptions integration tests.

Mirrors Home Assistant core patterns (see Nederlandse Spoorwegen tests) using
MockConfigEntry and patching network-facing layers.
"""
from __future__ import annotations
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry  # type: ignore

from custom_components.ennatuurlijk_disruptions.const import (
    DOMAIN,
    CONF_TOWN,
    CONF_POSTAL_CODE,
)

# Enable pytest-homeassistant-custom-component fixtures like `hass`
pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Provide a default mock config entry for the integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Ennatuurlijk Disruptions",
        data={
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
        unique_id="ennatuurlijk_test_entry",
    )


@pytest.fixture
def mockEntry() -> MockConfigEntry:
    """Provide a mock config entry for calendar and coordinator tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Ennatuurlijk Disruptions",
        data={
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
        entry_id="test-entry",
    )


@pytest.fixture
def load_fixture():
    """Load a fixture file."""
    def _load_fixture(filename: str) -> str:
        """Load fixture data from file."""
        import os
        path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
        with open(path, encoding="utf-8") as file:
            return file.read()
    return _load_fixture


@pytest.fixture
async def mock_aiohttp_session(load_fixture):
    """Mock aiohttp client session to return the HTML fixture."""
    class MockResponse:
        """Mock aiohttp response."""
        def __init__(self, text: str, status: int = 200):
            self._text = text
            self.status = status
            
        async def text(self):
            return self._text
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        def raise_for_status(self):
            if self.status >= 400:
                raise Exception(f"HTTP {self.status}")
    
    class MockSession:
        """Mock aiohttp session."""
        def get(self, url, **kwargs):
            html = load_fixture("ennatuurlijk_storingen.html")
            return MockResponse(html)
    
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_get_session:
        mock_get_session.return_value = MockSession()
        yield mock_get_session


@pytest.fixture
def mock_requests_get(mock_aiohttp_session):
    """Alias for backwards compatibility - now uses aiohttp mock."""
    return mock_aiohttp_session


@pytest.fixture
def mock_async_update_data() -> Generator[AsyncMock, None, None]:
    """Patch fetch_disruption_section to avoid network and return deterministic data."""
    with patch(
        "custom_components.ennatuurlijk_disruptions.coordinator.fetch_disruption_section",
        autospec=True,
    ) as mock:
        async def mock_fetch(hass, section, town, postal_code):
            if section == "planned":
                return {"state": True, "dates": [{"description": "Planned Tilburg", "date": "30-10-2025", "link": "https://ennatuurlijk.nl/storingen/108227"}]}
            elif section == "solved":
                return {"state": True, "dates": [{"description": "Solved Breda", "date": "29-10-2025", "link": "https://ennatuurlijk.nl/storingen/108219"}]}
            else:
                return {"state": False, "dates": []}
        
        mock.side_effect = mock_fetch
        yield mock


async def setup_integration(hass, entry: MockConfigEntry) -> None:
    """Set up the integration for the provided entry in Home Assistant."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

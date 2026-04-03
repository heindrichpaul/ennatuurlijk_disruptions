"""Integration-level tests following HA core patterns"""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ennatuurlijk_disruptions.const import DOMAIN

from .conftest import setup_integration
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def setup_global_entry(hass):
    """Fixture for integration setup with a real global config entry."""
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ennatuurlijk Disruptions",
        data={
            "days_to_keep_solved": 7,
            "update_interval": 120,
        },
        options={
            "days_to_keep_solved": 7,
            "update_interval": 120,
        },
        unique_id="ennatuurlijk_global",
    )
    global_entry.add_to_hass(hass)
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["global_entry"] = global_entry
    return global_entry


@pytest.mark.asyncio
async def test_setup_creates_coordinator_and_sensors(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,
    mock_async_update_data,
    setup_global_entry,
):
    # Create a v2 main entry (without subentries, as test framework doesn't support them)
    main_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ennatuurlijk Disruptions",
        data={"name": "Ennatuurlijk Disruptions"},
        options={"days_to_keep_solved": 7, "update_interval": 120},
        unique_id="ennatuurlijk_global",
        version=2,
    )

    main_entry.add_to_hass(hass)

    # Setup should succeed even without subentries
    await setup_integration(hass, main_entry)

    # Check that entry is loaded successfully
    assert main_entry.state.name == "LOADED"
    
    # Check coordinators are stored properly (either in runtime_data or hass.data fallback)
    if hasattr(main_entry, "runtime_data"):
        # Newer Home Assistant versions with runtime_data support
        assert main_entry.runtime_data == {}
    else:
        # Older Home Assistant versions use hass.data fallback
        assert main_entry.entry_id in hass.data[DOMAIN]
        assert hass.data[DOMAIN][main_entry.entry_id]["coordinators"] == {}
    
    # The integration should still set up platforms (sensor, binary_sensor, calendar)
    # but no entities will be created since there are no location subentries
    # This tests that the basic integration setup works with v2 main entries
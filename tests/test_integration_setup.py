"""Integration-level tests following HA core patterns (NS examples)."""

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
            "is_global": True,
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
    # Ensure the subentry is a real MockConfigEntry and added to hass
    mock_config_entry.add_to_hass(hass)
    await setup_integration(hass, mock_config_entry)
    # Coordinator should be stored in hass.data
    assert mock_config_entry.entry_id in hass.data.get(DOMAIN, {})
    stored = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert "coordinator" in stored
    # Basic smoke test that at least one sensor entity is created when data present
    sensor_states = [
        s for s in hass.states.async_all() if s.entity_id.startswith("sensor.")
    ]
    assert len(sensor_states) >= 3  # Should have planned, current, solved sensors
    # Check binary sensors
    binary_sensor_states = [
        s for s in hass.states.async_all() if s.entity_id.startswith("binary_sensor.")
    ]
    assert (
        len(binary_sensor_states) >= 3
    )  # Should have planned_alert, current_alert, solved_alert

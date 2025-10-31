"""Integration-level tests following HA core patterns (NS examples)."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.ennatuurlijk_disruptions.const import DOMAIN
from .conftest import setup_integration



@pytest.fixture
def setup_global_entry(hass, mock_global_config_entry):
    """Fixture for integration setup with global config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["global_entry"] = mock_global_config_entry

@pytest.mark.asyncio
async def test_setup_creates_coordinator_and_sensors(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,
    mock_async_update_data,
    setup_global_entry,
):
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

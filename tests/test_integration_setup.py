"""Integration-level tests following HA core patterns (NS examples)."""
import pytest
from homeassistant.core import HomeAssistant

from custom_components.ennatuurlijk_disruptions.const import DOMAIN
from .conftest import setup_integration


@pytest.mark.asyncio
async def test_setup_creates_coordinator_and_sensors(
    hass: HomeAssistant,
    enable_custom_integrations,
    mock_config_entry,  # from conftest.py
    mock_async_update_data,  # patched fetch
):
    await setup_integration(hass, mock_config_entry)

    # Coordinator should be stored in hass.data
    assert mock_config_entry.entry_id in hass.data.get(DOMAIN, {})
    stored = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert "coordinator" in stored

    # Basic smoke test that at least one sensor entity is created when data present
    sensor_states = [s for s in hass.states.async_all() if s.entity_id.startswith("sensor.")]
    assert len(sensor_states) >= 3  # Should have planned, current, solved sensors
    
    # Check binary sensors
    binary_sensor_states = [s for s in hass.states.async_all() if s.entity_id.startswith("binary_sensor.")]
    assert len(binary_sensor_states) >= 3  # Should have planned_alert, current_alert, solved_alert

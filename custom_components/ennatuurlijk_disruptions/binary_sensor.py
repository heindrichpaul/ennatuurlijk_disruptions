"""Binary sensor platform for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_CREATE_ALERT_SENSORS,
    DEFAULT_CREATE_ALERT_SENSORS,
    _LOGGER,
)
from .entity import EnnatuurlijkBinarySensor
from .binary_sensor_types import BINARY_SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ennatuurlijk Disruptions binary sensors from a config entry."""
    _LOGGER.info(
        "Setting up Ennatuurlijk Disruptions binary sensor for entry: %s",
        entry.entry_id,
    )

    # Check if alert sensors are enabled
    create_alert_sensors = (
        entry.options.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)
        if hasattr(entry, "options")
        else DEFAULT_CREATE_ALERT_SENSORS
    )

    if not create_alert_sensors:
        _LOGGER.info("Alert sensors disabled for entry: %s", entry.entry_id)
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [EnnatuurlijkBinarySensor(coordinator, entry, description) for description in BINARY_SENSOR_TYPES]

    async_add_entities(sensors)
    _LOGGER.info("Binary sensor setup completed for entry: %s", entry.entry_id)

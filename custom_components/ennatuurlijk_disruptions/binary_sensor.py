"""Binary sensor platform for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
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
        "Setting up Ennatuurlijk Disruptions binary sensors for entry: %s",
        entry.entry_id,
    )

    # Get coordinators for all subentries
    coordinators = entry.runtime_data

    for subentry_id, coordinator in coordinators.items():
        # Get the subentry object
        subentry = entry.subentries[subentry_id]

        # Check if alert sensors are enabled for this subentry
        create_alert_sensors = subentry.options.get(
            CONF_CREATE_ALERT_SENSORS,
            subentry.data.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS),
        )

        if not create_alert_sensors:
            _LOGGER.info("Alert sensors disabled for subentry: %s", subentry_id)
            continue

        # Create binary sensors for this subentry
        sensors = [
            EnnatuurlijkBinarySensor(coordinator, subentry, description)
            for description in BINARY_SENSOR_TYPES
        ]

        async_add_entities(sensors)

    _LOGGER.info("Binary sensor setup completed for entry: %s", entry.entry_id)

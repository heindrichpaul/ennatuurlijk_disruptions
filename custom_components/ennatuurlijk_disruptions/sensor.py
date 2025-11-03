"""Sensor platform for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import EnnatuurlijkSensor
from .sensor_types import SENSOR_TYPES

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Ennatuurlijk Disruptions sensors from a config entry."""
    _LOGGER.info(
        "Setting up Ennatuurlijk Disruptions sensors for entry: %s", entry.entry_id
    )

    # Get coordinators from runtime_data
    coordinators = entry.runtime_data
    
    _LOGGER.debug(
        "Found %d coordinators for entry %s: %s", 
        len(coordinators), 
        entry.entry_id,
        list(coordinators.keys())
    )

    if not coordinators:
        _LOGGER.info("No location subentries found, no sensors to create for entry: %s", entry.entry_id)
        return

    for subentry_id, coordinator in coordinators.items():
        # Get the subentry object
        subentry = entry.subentries[subentry_id]

        _LOGGER.info("Creating sensors for subentry %s (%s)", subentry_id, subentry.data.get("town", "Unknown"))

        # Create sensors for this subentry
        sensors = [
            EnnatuurlijkSensor(coordinator, subentry, description)
            for description in SENSOR_TYPES
        ]

        _LOGGER.info("Adding %d sensors for subentry %s", len(sensors), subentry_id)

        # Add entities with proper subentry association (following NS pattern)
        async_add_entities(sensors, config_subentry_id=subentry_id)

    _LOGGER.info("Entity setup completed for entry: %s", entry.entry_id)

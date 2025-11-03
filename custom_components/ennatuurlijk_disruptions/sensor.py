"""Sensor platform for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import EnnatuurlijkSensor
from .sensor_types import SENSOR_TYPES

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ennatuurlijk Disruptions sensors from a config entry."""
    _LOGGER.info(
        "Setting up Ennatuurlijk Disruptions sensors for entry: %s", entry.entry_id
    )

    # Get coordinators from runtime_data
    coordinators = entry.runtime_data

    for subentry_id, coordinator in coordinators.items():
        # Get the subentry object
        subentry = entry.subentries[subentry_id]

        # Create sensors for this subentry
        sensors = [
            EnnatuurlijkSensor(coordinator, subentry, description)
            for description in SENSOR_TYPES
        ]

        # Add entities with proper subentry association
        async_add_entities(sensors)

    _LOGGER.info("Entity setup completed for entry: %s", entry.entry_id)

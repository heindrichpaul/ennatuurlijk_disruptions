"""Sensor platform for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, _LOGGER
from .entity import EnnatuurlijkSensor
from .sensor_types import SENSOR_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ennatuurlijk Disruptions sensors from a config entry."""
    _LOGGER.info(
        "Setting up Ennatuurlijk Disruptions sensor for entry: %s", entry.entry_id
    )

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [EnnatuurlijkSensor(coordinator, entry, description) for description in SENSOR_TYPES]

    async_add_entities(sensors)
    _LOGGER.info("Entity setup completed for entry: %s", entry.entry_id)

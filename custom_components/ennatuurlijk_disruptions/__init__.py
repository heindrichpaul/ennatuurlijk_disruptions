"""Ennatuurlijk Disruptions integration: subentry setup and migration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import create_coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entries from v1 to v2."""
    _LOGGER.info(
        "Migrating config entry %s from version %s", entry.entry_id, entry.version
    )

    if entry.version != 1:
        return True

    # V1→V2 migration: Convert to appropriate pattern based on entry type
    postal_code = entry.data.get("postal_code")
    town = entry.data.get("town", "")

    # Extract config options from v1 data to move to options
    config_options = {}
    for key in ["days_to_keep_solved", "create_alert_sensors", "update_interval"]:
        if key in entry.data:
            config_options[key] = entry.data[key]

    # Merge with existing options (options take precedence)
    new_options = {**config_options, **entry.options}

    if not postal_code:
        # This is a main entry
        new_data = {"name": "Ennatuurlijk Disruptions"}
        new_unique_id = "ennatuurlijk_global"
        new_title = "Ennatuurlijk Disruptions"
    else:
        # This is a location entry, convert to subentry-compatible format
        new_data = {
            "name": entry.data.get("name", "Ennatuurlijk Disruptions"),
            "town": town,
            "postal_code": postal_code,
        }
        new_unique_id = postal_code
        new_title = f"{town} - {postal_code}"

    hass.config_entries.async_update_entry(
        entry,
        unique_id=new_unique_id,
    )

    hass.config_entries.async_update_entry(
        entry,
        title=new_title,
        data=new_data,
        options=new_options,
        version=2,
    )

    _LOGGER.info(
        "Converted entry %s to main entry (v1 location: %s %s will need re-adding)",
        entry.entry_id,
        town,
        postal_code,
    )
    _LOGGER.info("Please add your locations back via the UI after migration")

    return True


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ennatuurlijk Disruptions from a config entry."""
    _LOGGER.info("Setting up Ennatuurlijk Disruptions entry: %s (title: %s)", entry.entry_id, entry.title)
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)
    _LOGGER.debug("Entry subentries: %s", list(entry.subentries.keys()) if entry.subentries else "None")
    
    coordinators: dict[str, object] = {}

    # Set up coordinators for all existing location subentries
    for subentry_id, subentry in entry.subentries.items():
        _LOGGER.debug("Processing subentry %s: type=%s, data=%s", subentry_id, subentry.subentry_type, subentry.data)
        if subentry.subentry_type == "location":
            # Create coordinator from subentry, passing main entry for global settings
            coordinator = create_coordinator(hass, subentry, main_entry=entry)
            _LOGGER.info("Created coordinator for subentry %s (%s %s)", subentry_id, subentry.data.get("town"), subentry.data.get("postal_code"))
            _LOGGER.debug("Initial data refresh for subentry %s", subentry_id)
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("Initial refresh successful for subentry %s", subentry_id)
            coordinators[subentry_id] = coordinator

    _LOGGER.info("Created %d coordinators for entry %s", len(coordinators), entry.entry_id)

    # Store coordinators in runtime_data
    entry.runtime_data = coordinators

    # Add reload listener for when subentries are added/removed
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Set up platforms for all subentries
    _LOGGER.info("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Setup completed for entry %s", entry.entry_id)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when subentries are added/removed."""
    _LOGGER.info("Reloading Ennatuurlijk Disruptions entry due to subentry changes: %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clear runtime_data to ensure clean reload
        _LOGGER.debug("Clearing runtime_data for entry %s during unload", entry.entry_id)
        entry.runtime_data = {}
    
    return unload_ok

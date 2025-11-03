"""Ennatuurlijk Disruptions integration: subentry setup and migration."""

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
from .const import DOMAIN, _LOGGER
from .coordinator import create_coordinator


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entries from v1 to v2 (subentry pattern)."""
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
    """Set up config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Set up coordinators for all existing location subentries (like NS pattern)
    coordinators: dict[str, object] = {}

    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type == "location":
            # Create coordinator from subentry (contains all location settings)
            coordinator = create_coordinator(hass, subentry)
            _LOGGER.debug("Initial data refresh for subentry %s", subentry_id)
            await coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("Initial refresh successful for subentry %s", subentry_id)
            coordinators[subentry_id] = coordinator

    entry.runtime_data = coordinators

    # Set up platforms for all subentries
    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "binary_sensor", "calendar"]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up runtime data."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "binary_sensor", "calendar"]
    )
    if unload_ok and hasattr(entry, "runtime_data"):
        entry.runtime_data = None
    return unload_ok

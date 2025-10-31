"""Ennatuurlijk Disruptions integration: setup, migration, and entry management."""

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
from .const import DOMAIN, _LOGGER

from .coordinator import create_coordinator


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entries from v1 to v2 (global+subentry)."""
    _LOGGER.info("Migrating config entry %s from version %s", entry.entry_id, entry.version)
    if entry.version == 1:
        data = dict(entry.data)
        options = dict(entry.options)
        if data.get("is_global"):
            hass.config_entries.async_update_entry(entry, unique_id="ennatuurlijk_global")
            _LOGGER.info("Set unique_id to ennatuurlijk_global for global entry %s", entry.entry_id)
        else:
            postal_code = data.get("postal_code")
            if postal_code:
                hass.config_entries.async_update_entry(entry, unique_id=postal_code)
                _LOGGER.info("Set unique_id to %s for subentry %s", postal_code, entry.entry_id)
        hass.config_entries.async_update_entry(entry, version=2, data=data, options=options)
        _LOGGER.info("Migration of entry %s to version 2 complete", entry.entry_id)
        return True
    return True

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entry: global or subentry."""
    hass.data.setdefault(DOMAIN, {})

    if entry.unique_id == "ennatuurlijk_global":
        _LOGGER.debug("Registering global config entry")
        hass.data[DOMAIN]["global_entry"] = entry
        return True

    global_entry = hass.data[DOMAIN].get("global_entry")
    if not global_entry:
        _LOGGER.error("No global config entry found. Please add the global settings first.")
        return False

    coordinator = create_coordinator(hass, entry, global_entry=global_entry)
    _LOGGER.debug(f"Initial data refresh for subentry {entry.entry_id}")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial refresh successful for subentry %s", entry.entry_id)

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "entry": entry}

    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "binary_sensor", "calendar"]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "binary_sensor", "calendar"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

"""Ennatuurlijk Disruptions integration: setup, migration, and entry management."""

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
from .const import DOMAIN, _LOGGER
from .coordinator import create_coordinator

def _find_global_entry(hass: HomeAssistant):
    """Return the global config entry if present, else None."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.unique_id == "ennatuurlijk_global":
            return entry
    return None



def _find_v1_global_entry(hass: HomeAssistant):
    """Return a v1 global config entry if present, else None."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        data = dict(entry.data)
        if entry.version == 1 and (data.get("is_global") or not data.get("postal_code")):
            return entry
    return None

async def _create_global_entry(hass: HomeAssistant, data: dict):
    """Create a new global config entry via migration flow."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "migration"},
        data={
            "is_global": True,
            "days_to_keep_solved": data.get("days_to_keep_solved", 7),
            "update_interval": data.get("update_interval", 120),
        },
    )
    _LOGGER.info("Created new global config entry during migration.")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entries from v1 to v2 (global+subentry)."""
    _LOGGER.info("Migrating config entry %s from version %s", entry.entry_id, entry.version)
    if entry.version != 1:
        return True
    data = dict(entry.data)
    options = dict(entry.options)
    # Migrate global entry
    if data.get("is_global") or (not data.get("postal_code")):
        hass.config_entries.async_update_entry(entry, unique_id="ennatuurlijk_global")
        hass.config_entries.async_update_entry(entry, version=2, data=data, options=options)
        _LOGGER.info("Set unique_id to ennatuurlijk_global for global entry %s", entry.entry_id)
        _LOGGER.info("Migration of entry %s to version 2 complete", entry.entry_id)
        return True

    # For subentries, ensure global entry exists and is migrated first
    global_entry = _find_global_entry(hass)
    if not global_entry:
        v1_global = _find_v1_global_entry(hass)
        if v1_global:
            _LOGGER.info("Migrating global entry %s before subentry %s", v1_global.entry_id, entry.entry_id)
            await async_migrate_entry(hass, v1_global)
            global_entry = _find_global_entry(hass)
    if not global_entry:
        await _create_global_entry(hass, data)
    # Now migrate this subentry
    postal_code = data.get("postal_code")
    if postal_code:
        hass.config_entries.async_update_entry(entry, unique_id=postal_code)
        _LOGGER.info("Set unique_id to %s for subentry %s", postal_code, entry.entry_id)
    hass.config_entries.async_update_entry(entry, version=2, data=data, options=options)
    _LOGGER.info("Migration of entry %s to version 2 complete", entry.entry_id)
    return True


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)




async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entry: global or subentry."""
    hass.data.setdefault(DOMAIN, {})
    # Always register the global entry if this is the global entry
    if entry.unique_id == "ennatuurlijk_global":
        _register_global_entry(hass, entry)
        return True
    # If the global entry is not registered but this entry is global, register it
    if "global_entry" not in hass.data[DOMAIN] and getattr(entry, "unique_id", None) == "ennatuurlijk_global":
        _register_global_entry(hass, entry)
        return True
    global_entry = hass.data[DOMAIN].get("global_entry")
    if not global_entry:
        _LOGGER.error("No global config entry found. Please add the global settings first.")
        return False
    return await _setup_subentry(hass, entry, global_entry)


def _register_global_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the global config entry in hass.data."""
    _LOGGER.debug("Registering global config entry")
    hass.data[DOMAIN]["global_entry"] = entry


async def _setup_subentry(hass: HomeAssistant, entry: ConfigEntry, global_entry: ConfigEntry) -> bool:
    """Set up a subentry: create coordinator, refresh, and forward setups."""
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
    """Unload a config entry and clean up hass.data."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "binary_sensor", "calendar"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

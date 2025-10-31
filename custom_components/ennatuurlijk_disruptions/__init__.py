from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
from .const import DOMAIN, _LOGGER
from .coordinator import create_coordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Move coordinator creation here for all platforms

    coordinator = create_coordinator(hass, entry)
    _LOGGER.debug("Performing initial data refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial refresh successful")

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "entry": entry}

    # Forward sensor, binary_sensor, and calendar platforms
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

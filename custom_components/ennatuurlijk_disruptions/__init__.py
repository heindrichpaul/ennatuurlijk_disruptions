from homeassistant.config_entries import ConfigEntry # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.helpers import config_validation as cv # type: ignore
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator # type: ignore
from datetime import timedelta
from .const import DOMAIN, _LOGGER, CONF_TOWN, CONF_POSTAL_CODE, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Move coordinator creation here for all platforms

    from .fetch import async_update_data
    update_interval_min = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL) if hasattr(entry, "options") else DEFAULT_UPDATE_INTERVAL
    try:
        update_interval = timedelta(minutes=int(update_interval_min))
    except Exception:
        update_interval = timedelta(minutes=DEFAULT_UPDATE_INTERVAL)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=lambda: async_update_data(hass, entry),
        update_interval=update_interval,
    )
    _LOGGER.debug("Performing initial data refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial refresh successful")

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "entry": entry}

    # Forward both sensor and calendar platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "calendar"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
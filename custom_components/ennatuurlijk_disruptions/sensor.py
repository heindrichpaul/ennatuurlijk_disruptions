from homeassistant.helpers.update_coordinator import DataUpdateCoordinator # type: ignore
from .const import DOMAIN, CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS, _LOGGER
from .sensor_planned import EnnatuurlijkPlannedSensor, EnnatuurlijkPlannedAlertSensor
from .sensor_current import EnnatuurlijkCurrentSensor, EnnatuurlijkCurrentAlertSensor
from .sensor_solved import EnnatuurlijkSolvedSensor, EnnatuurlijkSolvedAlertSensor

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Ennatuurlijk Disruptions sensor for entry: %s", entry.entry_id)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    create_alert_sensors = entry.options.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS) if hasattr(entry, "options") else DEFAULT_CREATE_ALERT_SENSORS
    sensors = [
        EnnatuurlijkPlannedSensor(coordinator, entry),
        EnnatuurlijkCurrentSensor(coordinator, entry),
        EnnatuurlijkSolvedSensor(coordinator, entry),
    ]
    if create_alert_sensors:
        sensors.extend([
            EnnatuurlijkPlannedAlertSensor(coordinator, entry),
            EnnatuurlijkCurrentAlertSensor(coordinator, entry),
            EnnatuurlijkSolvedAlertSensor(coordinator, entry),
        ])
    async_add_entities(sensors)
    _LOGGER.info("Entity setup completed for entry: %s", entry.entry_id)
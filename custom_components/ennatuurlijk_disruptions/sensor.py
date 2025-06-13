import requests
from bs4 import BeautifulSoup
import re
from homeassistant.components.sensor import SensorEntity # type: ignore
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.entity import EntityDescription # type: ignore
from homeassistant.const import Platform # type: ignore
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE, SCAN_INTERVAL, _LOGGER, CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
from .sensor_planned import EnnatuurlijkPlannedSensor, EnnatuurlijkPlannedAlertSensor
from .sensor_current import EnnatuurlijkCurrentSensor, EnnatuurlijkCurrentAlertSensor
from .sensor_solved import EnnatuurlijkSolvedSensor, EnnatuurlijkSolvedAlertSensor
from .fetch import fetch_disruption_section

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Ennatuurlijk Disruptions sensor for entry: %s", entry.entry_id)
    town = entry.data[CONF_TOWN]
    postal_code = entry.data[CONF_POSTAL_CODE]

    async def async_update_data():
        _LOGGER.debug("Fetching all disruption data for %s, %s", town, postal_code)
        try:
            # Fetch all sections centrally
            planned = await hass.async_add_executor_job(fetch_disruption_section, "planned", town, postal_code)
            current = await hass.async_add_executor_job(fetch_disruption_section, "current", town, postal_code)
            solved = await hass.async_add_executor_job(fetch_disruption_section, "solved", town, postal_code)
            # Compose the result in the same structure as before
            result = {
                "planned": planned or {"state": False, "dates": []},
                "current": current or {"state": False, "dates": []},
                "solved": solved or {"state": False, "dates": []},
                "details": "See attributes for details.",
                "disruptions": [],
                "town": town,
                "postal_code": postal_code
            }
            return result
        except Exception as e:
            _LOGGER.error("Unexpected error fetching disruption data: %s", str(e))
            return {
                "planned": {"state": False, "dates": []},
                "current": {"state": False, "dates": []},
                "solved": {"state": False, "dates": []},
                "details": f"Unexpected error: {str(e)}",
                "disruptions": [],
                "town": town,
                "postal_code": postal_code
            }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Patch: force_refresh on manual update
    orig_async_request_refresh = coordinator.async_request_refresh
    async def _async_force_refresh(*args, **kwargs):
        _LOGGER.debug("Manual update requested, forcing data refresh for Ennatuurlijk Disruptions")
        await hass.async_add_executor_job(fetch_disruption_section, "planned", town, postal_code, True)
        await hass.async_add_executor_job(fetch_disruption_section, "current", town, postal_code, True)
        await hass.async_add_executor_job(fetch_disruption_section, "solved", town, postal_code, True)
        await orig_async_request_refresh(*args, **kwargs)
    coordinator.async_request_refresh = _async_force_refresh

    _LOGGER.debug("Performing initial data refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial refresh successful")

    _LOGGER.debug("Adding EnnatuurlijkSensor entity")
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
    _LOGGER.info("Entity setup completed for %s, %s", town, postal_code)

class EnnatuurlijkSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_icon = "mdi:alert"
        self._attr_translation_key = "ennatuurlijk_disruptions"  # Uses integration name for translation
        _LOGGER.debug("Initialized EnnatuurlijkSensor with unique_id: %s", self._attr_unique_id)

    @property
    def state(self):
        # Return 'on' if any planned or current disruption is active, else 'off'
        planned = self.coordinator.data.get("planned", {}).get("state", False)
        current = self.coordinator.data.get("current", {}).get("state", False)
        return "on" if planned or current else "off"

    @property
    def extra_state_attributes(self):
        # Expose all data as attributes for compatibility
        return self.coordinator.data

    @property
    def available(self):
        return self.coordinator.data is not None

class EnnatuurlijkPlannedSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_planned"
        self._attr_icon = "mdi:calendar-alert"
        self._attr_translation_key = "ennatuurlijk_disruptions_planned"

    @property
    def state(self):
        return self.coordinator.data.get("planned", {}).get("state")

    @property
    def extra_state_attributes(self):
        return {"dates": self.coordinator.data.get("planned", {}).get("dates", [])}

    @property
    def available(self):
        return self.coordinator.data is not None

class EnnatuurlijkCurrentSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_current"
        self._attr_icon = "mdi:alert-circle"
        self._attr_translation_key = "ennatuurlijk_disruptions_current"

    @property
    def state(self):
        return self.coordinator.data.get("current", {}).get("state")

    @property
    def extra_state_attributes(self):
        return {"dates": self.coordinator.data.get("current", {}).get("dates", [])}

    @property
    def available(self):
        return self.coordinator.data is not None

class EnnatuurlijkSolvedSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_solved"
        self._attr_icon = "mdi:check-circle"
        self._attr_translation_key = "ennatuurlijk_disruptions_solved"

    @property
    def state(self):
        return self.coordinator.data.get("solved", {}).get("state")

    @property
    def extra_state_attributes(self):
        return {"dates": self.coordinator.data.get("solved", {}).get("dates", [])}

    @property
    def available(self):
        return self.coordinator.data is not None

class EnnatuurlijkDetailsSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_details"
        self._attr_icon = "mdi:text"
        self._attr_translation_key = "ennatuurlijk_disruptions_details"

    @property
    def state(self):
        return self.coordinator.data.get("details")

    @property
    def available(self):
        return self.coordinator.data is not None
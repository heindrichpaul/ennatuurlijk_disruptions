from homeassistant.components.sensor import SensorEntity # type: ignore
from .const import _LOGGER, DOMAIN, SENSOR_PREFIX, ATTR_ERROR, ATTR_FRIENDLY_NAME, ATTR_YEAR_MONTH_DAY_DATE, ATTR_LAST_UPDATE, ATTR_DAYS_SINCE_CURRENT_DATE, ATTR_IS_CURRENT_DATE_TODAY
from datetime import datetime

class EnnatuurlijkCurrentSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_current"
        self._attr_icon = "mdi:alert-circle"
        self._attr_translation_key = "ennatuurlijk_disruptions_current"
        self._attr_name = f"{SENSOR_PREFIX}Current"

    @property
    def state(self):
        current = self.coordinator.data.get("current", {})
        today = datetime.now().date()
        dates = [d["date"] for d in current.get("dates", []) if d.get("date")]
        if not dates:
            _LOGGER.debug(f"[{self._attr_unique_id}] State computed: None")
            return None
        date_objs = [datetime.strptime(d, "%d-%m-%Y").date() for d in dates]
        closest_date = min(date_objs, key=lambda d: abs((d - today).days))
        state = closest_date.strftime("%Y-%m-%d")
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {state}")
        return state

    @property
    def extra_state_attributes(self):
        current = self.coordinator.data.get("current", {})
        today = datetime.now().date()
        dates = current.get("dates", [])
        date_strs = [d["date"] for d in dates if d.get("date")]
        if not date_strs:
            closest_date = None
            latest_link = None
            latest_description = None
        else:
            date_objs = [datetime.strptime(d, "%d-%m-%Y").date() for d in date_strs]
            closest_date = min(date_objs, key=lambda d: abs((d - today).days))
            closest_disruption = min(dates, key=lambda d: abs((datetime.strptime(d["date"], "%d-%m-%Y").date() - today).days))
            latest_link = closest_disruption.get("link")
            latest_description = closest_disruption.get("description")
        days_since = (today - closest_date).days if closest_date else None
        last_update = current.get("last_update_date", None)
        disruption_count = len(dates)
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_YEAR_MONTH_DAY_DATE: closest_date.strftime("%Y-%m-%d") if closest_date else None,
            ATTR_LAST_UPDATE: last_update,
            ATTR_DAYS_SINCE_CURRENT_DATE: days_since,
            ATTR_IS_CURRENT_DATE_TODAY: closest_date == today if closest_date else False,
            "dates": dates,
            "icon": self.icon,
            "latest_link": latest_link,
            "latest_description": latest_description,
            "disruption_count": disruption_count,
            "next_disruption_date": closest_date.strftime("%Y-%m-%d") if closest_date else None,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

class EnnatuurlijkCurrentAlertSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_current_alert"
        self._attr_icon = "mdi:alert"
        self._attr_translation_key = "ennatuurlijk_disruptions_current_alert"
        self._attr_name = f"{SENSOR_PREFIX}Current Alert"

    @property
    def state(self):
        current = self.coordinator.data.get("current", {})
        state = "on" if current.get("state") else "off"
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {state}")
        return state

    @property
    def extra_state_attributes(self):
        current = self.coordinator.data.get("current", {})
        last_update = current.get("last_update_date", None)
        _LOGGER.debug(f"[{self._attr_unique_id}] Last update value: {last_update} (raw: {repr(last_update)})")
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_LAST_UPDATE: last_update,
            "dates": current.get("dates", []),
            "icon": self.icon,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

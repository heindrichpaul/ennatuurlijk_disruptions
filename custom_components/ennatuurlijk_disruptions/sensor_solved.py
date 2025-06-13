from homeassistant.components.sensor import SensorEntity # type: ignore
from .const import _LOGGER, DOMAIN, ATTR_ERROR, ATTR_FRIENDLY_NAME, ATTR_YEAR_MONTH_DAY_DATE, ATTR_LAST_UPDATE, ATTR_DAYS_UNTIL_PLANNED_DATE, ATTR_IS_PLANNED_DATE_TODAY
from datetime import datetime

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
        solved = self.coordinator.data.get("solved", {})
        today = datetime.now().date()
        dates = [d["date"] for d in solved.get("dates", []) if d.get("date")]
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
        solved = self.coordinator.data.get("solved", {})
        today = datetime.now().date()
        dates = [d["date"] for d in solved.get("dates", []) if d.get("date")]
        if not dates:
            closest_date = None
        else:
            date_objs = [datetime.strptime(d, "%d-%m-%Y").date() for d in dates]
            closest_date = min(date_objs, key=lambda d: abs((d - today).days))
        days_since = (today - closest_date).days if closest_date else None
        last_update = None
        if hasattr(self.coordinator, "last_update_success") and self.coordinator.last_update_success:
            last_update = self.coordinator.last_update_success.strftime("%d-%m-%Y %H:%M")
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_YEAR_MONTH_DAY_DATE: closest_date.strftime("%Y-%m-%d") if closest_date else None,
            ATTR_LAST_UPDATE: last_update,
            ATTR_DAYS_UNTIL_PLANNED_DATE: days_since,
            ATTR_IS_PLANNED_DATE_TODAY: closest_date == today if closest_date else False,
            "dates": dates,
            "icon": self.icon,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

class EnnatuurlijkSolvedAlertSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_solved_alert"
        self._attr_icon = "mdi:alert"
        self._attr_translation_key = "ennatuurlijk_disruptions_solved_alert"

    @property
    def state(self):
        solved = self.coordinator.data.get("solved", {})
        state = "on" if solved.get("state") else "off"
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {state}")
        return state

    @property
    def extra_state_attributes(self):
        solved = self.coordinator.data.get("solved", {})
        last_update = None
        if hasattr(self.coordinator, "last_update_success") and self.coordinator.last_update_success:
            last_update = self.coordinator.last_update_success.strftime("%d-%m-%Y %H:%M")
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_LAST_UPDATE: last_update,
            "dates": solved.get("dates", []),
            "icon": self.icon,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

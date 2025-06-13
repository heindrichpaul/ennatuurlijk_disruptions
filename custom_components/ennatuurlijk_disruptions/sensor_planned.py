from homeassistant.components.sensor import SensorEntity # type: ignore

from .const import _LOGGER, DOMAIN, ATTR_ERROR, ATTR_FRIENDLY_NAME, ATTR_YEAR_MONTH_DAY_DATE, ATTR_LAST_UPDATE, ATTR_DAYS_UNTIL_PLANNED_DATE, ATTR_IS_PLANNED_DATE_TODAY
from datetime import datetime

class EnnatuurlijkPlannedSensor(SensorEntity):
    def __init__(self, coordinator, entry, days_to_keep_solved=7):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_planned"
        self._attr_icon = "mdi:calendar-alert"
        self._attr_translation_key = "ennatuurlijk_disruptions_planned"
        self.days_to_keep_solved = days_to_keep_solved

    @property
    def state(self):
        planned = self.coordinator.data.get("planned", {})
        today = datetime.now().date()
        dates = [d["date"] for d in planned.get("dates", []) if d.get("date")]
        future_dates = [d for d in dates if datetime.strptime(d, "%d-%m-%Y").date() >= today]
        closest_date = min((datetime.strptime(d, "%d-%m-%Y").date() for d in future_dates), default=None)
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {closest_date.strftime('%Y-%m-%d') if closest_date else None}")
        return closest_date.strftime("%Y-%m-%d") if closest_date else None

    @property
    def extra_state_attributes(self):
        planned = self.coordinator.data.get("planned", {})
        today = datetime.now().date()
        dates = [d["date"] for d in planned.get("dates", []) if d.get("date")]
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

class EnnatuurlijkPlannedAlertSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_planned_alert"
        self._attr_icon = "mdi:alert"
        self._attr_translation_key = "ennatuurlijk_disruptions_planned_alert"

    @property
    def state(self):
        planned = self.coordinator.data.get("planned", {})
        state = "on" if planned.get("state") else "off"
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {state}")
        return state

    @property
    def extra_state_attributes(self):
        planned = self.coordinator.data.get("planned", {})
        last_update = None
        if hasattr(self.coordinator, "last_update_success") and self.coordinator.last_update_success:
            last_update = self.coordinator.last_update_success.strftime("%d-%m-%Y %H:%M")
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_LAST_UPDATE: last_update,
            "dates": planned.get("dates", []),
            "icon": self.icon,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

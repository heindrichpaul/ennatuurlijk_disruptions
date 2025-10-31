from homeassistant.components.sensor import SensorEntity # type: ignore

from .const import _LOGGER, DOMAIN, SENSOR_PREFIX, ATTR_ERROR, ATTR_FRIENDLY_NAME, ATTR_YEAR_MONTH_DAY_DATE, ATTR_LAST_UPDATE, ATTR_DAYS_UNTIL_PLANNED_DATE, ATTR_IS_PLANNED_DATE_TODAY
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
        self._attr_name = f"{SENSOR_PREFIX}Planned"

    @property
    def state(self):
        planned = self.coordinator.planned
        today = datetime.now().date()
        dates = [d["date"] for d in planned.get("dates", []) if d.get("date")]
        future_dates = [d for d in dates if datetime.strptime(d, "%d-%m-%Y").date() >= today]
        closest_date = min((datetime.strptime(d, "%d-%m-%Y").date() for d in future_dates), default=None)
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {closest_date.strftime('%Y-%m-%d') if closest_date else None}")
        return closest_date.strftime("%Y-%m-%d") if closest_date else None

    @property
    def extra_state_attributes(self):
        planned = self.coordinator.planned
        today = datetime.now().date()
        dates = planned.get("dates", [])
        date_strs = [d["date"] for d in dates if d.get("date")]
        if not date_strs:
            closest_date = None
            latest_link = None
            latest_description = None
        else:
            date_objs = [datetime.strptime(d, "%d-%m-%Y").date() for d in date_strs]
            closest_date = min(date_objs, key=lambda d: abs((d - today).days))
            # Find the disruption dict for the closest date
            closest_disruption = min(dates, key=lambda d: abs((datetime.strptime(d["date"], "%d-%m-%Y").date() - today).days))
            latest_link = closest_disruption.get("link")
            latest_description = closest_disruption.get("description")
        days_until = (closest_date - today).days if closest_date else None
        last_update = planned.get("last_update_date", None)
        disruption_count = len(dates)
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_YEAR_MONTH_DAY_DATE: closest_date.strftime("%Y-%m-%d") if closest_date else None,
            ATTR_LAST_UPDATE: last_update,
            ATTR_DAYS_UNTIL_PLANNED_DATE: days_until,
            ATTR_IS_PLANNED_DATE_TODAY: closest_date == today if closest_date else False,
            "dates": dates,
            "icon": self.icon,
            "latest_link": latest_link,
            "latest_description": latest_description,
            "disruption_count": disruption_count,
            "next_disruption_date": closest_date.strftime("%Y-%m-%d") if closest_date else None,
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
        self._attr_name = f"{SENSOR_PREFIX}Planned Alert"

    @property
    def state(self):
        planned = self.coordinator.planned
        state = "on" if planned.get("state") else "off"
        _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {state}")
        return state

    @property
    def extra_state_attributes(self):
        planned = self.coordinator.planned
        last_update = planned.get("last_update_date", None)
        _LOGGER.debug(f"[{self._attr_unique_id}] Last update value: {last_update} (raw: {repr(last_update)})")
        attrs = {
            ATTR_ERROR: False,
            ATTR_FRIENDLY_NAME: self.name,
            ATTR_LAST_UPDATE: last_update,
            "dates": planned.get("dates", []),
            "icon": self.icon,
        }
        _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
        return attrs

from homeassistant.components.calendar import CalendarEntity, CalendarEvent # type: ignore
from homeassistant.util import dt as dt_util # type: ignore
from datetime import datetime, timedelta
from .const import DOMAIN, SENSOR_PREFIX, _LOGGER

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    _LOGGER.debug("Setting up Ennatuurlijk Planned Disruptions Calendar for entry: %s", entry.entry_id)
    async_add_entities([EnnatuurlijkPlannedDisruptionsCalendar(coordinator, entry)])

class EnnatuurlijkPlannedDisruptionsCalendar(CalendarEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_planned_calendar"
        self._attr_name = f"{SENSOR_PREFIX}Planned Disruptions Calendar"
        self._attr_icon = "mdi:calendar-alert"

    @property
    def event(self):
        today = dt_util.now().date()
        events = self._get_events(today, today + timedelta(days=365))
        if events:
            _LOGGER.debug(f"[calendar:{self._attr_unique_id}] Preview event: {events[0].summary} on {events[0].start}")
        else:
            _LOGGER.debug(f"[calendar:{self._attr_unique_id}] No upcoming events for preview.")
        return events[0] if events else None

    async def async_get_events(self, hass, start_date, end_date):
        _LOGGER.debug(f"[calendar:{self._attr_unique_id}] Fetching events from {start_date} to {end_date}")
        return self._get_events(start_date.date(), end_date.date())

    def _get_events(self, start_date, end_date):
        planned = self.coordinator.data.get("planned", {})
        events = []
        for disruption in planned.get("dates", []):
            date_str = disruption.get("date")
            if not date_str:
                continue
            try:
                event_date = datetime.strptime(date_str, "%d-%m-%Y").date()
            except Exception as e:
                _LOGGER.debug(f"[calendar:{self._attr_unique_id}] Skipping disruption with invalid date '{date_str}': {e}")
                continue
            if start_date <= event_date <= end_date:
                summary = disruption.get("description", "Planned Disruption")
                link = disruption.get("link")
                event = CalendarEvent(
                    summary=summary,
                    start=dt_util.start_of_local_day(event_date),
                    end=dt_util.start_of_local_day(event_date) + timedelta(days=1),
                    description=link or ""
                )
                _LOGGER.debug(f"[calendar:{self._attr_unique_id}] Adding event: {summary} on {event_date} (link: {link})")
                events.append(event)
        events.sort(key=lambda e: e.start)
        _LOGGER.debug(f"[calendar:{self._attr_unique_id}] Total events returned: {len(events)}")
        return events

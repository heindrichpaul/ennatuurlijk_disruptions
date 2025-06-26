from homeassistant.components.calendar import CalendarEntity, CalendarEvent # type: ignore
from homeassistant.util import dt as dt_util # type: ignore
from datetime import datetime, timedelta
import re
from .const import DOMAIN, SENSOR_PREFIX, _LOGGER

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    _LOGGER.debug("Setting up Ennatuurlijk Disruptions Calendar for entry: %s", entry.entry_id)
    async_add_entities([EnnatuurlijkDisruptionsCalendar(coordinator, entry)])

class EnnatuurlijkDisruptionsCalendar(CalendarEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_calendar"
        self._attr_name = f"{SENSOR_PREFIX}Disruptions Calendar"
        self._attr_icon = "mdi:calendar-alert"
        self._event_logs = {}  # {disruption_id: [log entries]}

    @property
    def event(self):
        today = dt_util.now().date()
        events = self._get_events(today, today + timedelta(days=365))
        return events[0] if events else None

    async def async_get_events(self, hass, start_date, end_date):
        return self._get_events(start_date.date(), end_date.date())

    def _get_events(self, start_date, end_date):
        # Build a dict of disruptions by id, merging statuses
        disruptions_by_id = {}
        # Gather all disruptions by id and status
        for status in ("planned", "current", "solved"):
            for disruption in self.coordinator.data.get(status, {}).get("dates", []):
                link = disruption.get("link")
                disruption_id = self._extract_id_from_link(link)
                if not disruption_id:
                    continue
                if disruption_id not in disruptions_by_id:
                    disruptions_by_id[disruption_id] = {"id": disruption_id, "statuses": {}, "link": link, "description": disruption.get("description", "Disruption")}
                disruptions_by_id[disruption_id]["statuses"][status] = disruption
        events = []
        for disruption_id, info in disruptions_by_id.items():
            statuses = info["statuses"]
            link = info["link"]
            description = info["description"]
            summary = f"#{disruption_id} - {description}".strip()
            log = self._event_logs.setdefault(disruption_id, [])
            now_str = dt_util.now().strftime("%Y-%m-%d %H:%M")
            # Determine event timing and status
            log_entry = None
            if "current" in statuses:
                # Current event, may become solved
                start_date_str = statuses["current"].get("date")
                start = self._parse_date(start_date_str)
                if "solved" in statuses:
                    end_date_str = statuses["solved"].get("date")
                    end = self._parse_date(end_date_str)
                    status = "solved"
                    log_entry = f"Solved: {now_str} (end: {end})"
                else:
                    end = start + timedelta(days=1)
                    status = "current"
                    log_entry = f"Current: {now_str} (start: {start})"
            elif "planned" in statuses:
                # Planned only
                start_date_str = statuses["planned"].get("date")
                start = self._parse_date(start_date_str)
                end = start + timedelta(days=1)
                status = "planned"
                log_entry = f"Planned: {now_str} (date: {start})"
            elif "solved" in statuses:
                # Solved only (integration installed after event)
                start_date_str = statuses["solved"].get("date")
                start = self._parse_date(start_date_str)
                end = start + timedelta(days=1)
                status = "solved"
                log_entry = f"Solved: {now_str} (date: {start})"
            else:
                continue  # Should not happen
            # Only show events in range
            if not (start_date <= start <= end_date):
                continue
            # Only append log if new
            if log_entry and (not log or log[-1] != log_entry):
                log.append(log_entry)
            # Improved description formatting (no log)
            desc = (
                f"Status: #{status}\n"
                f"Link: {link or 'N/A'}"
            )
            event = CalendarEvent(
                summary=summary,
                start=dt_util.start_of_local_day(start),
                end=dt_util.start_of_local_day(end),
                description=desc
            )
            events.append(event)
        events.sort(key=lambda e: e.start)
        return events

    def _extract_id_from_link(self, link):
        if not link:
            return None
        m = re.search(r"/(\d+)$", link)
        return m.group(1) if m else None

    def _parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except Exception:
            return dt_util.now().date()

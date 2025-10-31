"""Calendar entity for Ennatuurlijk Disruptions."""
from homeassistant.components.calendar import CalendarEntity, CalendarEvent  # type: ignore
from homeassistant.util import dt as dt_util  # type: ignore
from datetime import datetime, timedelta
import re
from .const import DOMAIN, _LOGGER


async def async_setup_entry(hass, entry, async_add_entities):
    # Only create the calendar entity once
    if "calendar_entity_created" in hass.data.setdefault(DOMAIN, {}):
        _LOGGER.debug("Calendar entity already created, skipping for entry: %s", entry.entry_id)
        return
    _LOGGER.debug("Setting up single Ennatuurlijk Disruptions Calendar for the integration")
    async_add_entities([
        EnnatuurlijkDisruptionsCalendar(hass)
    ])
    hass.data[DOMAIN]["calendar_entity_created"] = True




class EnnatuurlijkDisruptionsCalendar(CalendarEntity):
    _attr_icon = "mdi:calendar-alert"

    def __init__(self, hass):
        super().__init__()
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_calendar"
        self._attr_name = "Ennatuurlijk Disruptions Calendar"
        self._event_logs = {}  # {disruption_id: [log entries]}
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "calendar")},
            "name": "Ennatuurlijk Disruptions Calendar",
            "manufacturer": "Ennatuurlijk",
            "model": "Disruption Monitor",
        }


    @property
    def has_entity_name(self) -> bool:
        return True



    @property
    def event(self):
        today = dt_util.now().date()
        events = self._get_events(today, today + timedelta(days=365))
        return events[0] if events else None



    async def async_get_events(self, hass, start_date, end_date):
        return self._get_events(start_date.date(), end_date.date())

    def _get_events(self, start_date, end_date):
        # Aggregate disruptions from all subentries
        disruptions_by_id = {}
        for entry_id, entry_data in self.hass.data.get(DOMAIN, {}).items():
            if entry_id == "global_entry":
                continue
            if not isinstance(entry_data, dict) or "coordinator" not in entry_data:
                continue
            coordinator = entry_data["coordinator"]
            for status in ("planned", "current", "solved"):
                status_data = getattr(coordinator, status, {})
                for disruption in status_data.get("dates", []):
                    link = disruption.get("link")
                    disruption_id = self._extract_id_from_link(link)
                    if not disruption_id:
                        continue
                    if disruption_id not in disruptions_by_id:
                        disruptions_by_id[disruption_id] = {
                            "id": disruption_id,
                            "statuses": {},
                            "link": link,
                            "description": disruption.get("description", "Disruption"),
                        }
                    disruptions_by_id[disruption_id]["statuses"][status] = disruption
        events = []
        for disruption_id, info in disruptions_by_id.items():
            statuses = info["statuses"]
            link = info["link"]
            description = info["description"]
            summary = f"#{disruption_id} - {description}".strip()
            log = self._event_logs.setdefault(disruption_id, [])
            now_str = dt_util.now().strftime("%Y-%m-%d %H:%M")
            # Set event timing and status
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
            # Format description
            desc = f"Status: #{status}\nLink: {link or 'N/A'}"
            event = CalendarEvent(
                summary=summary,
                start=dt_util.start_of_local_day(start),
                end=dt_util.start_of_local_day(end),
                description=desc,
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

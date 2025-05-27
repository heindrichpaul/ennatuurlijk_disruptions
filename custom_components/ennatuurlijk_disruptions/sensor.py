import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import EntityDescription
from homeassistant.const import Platform
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE, SCAN_INTERVAL

# Explicitly define the logger for the module
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Ennatuurlijk Disruptions sensor for entry: %s", entry.entry_id)
    town = entry.data[CONF_TOWN]
    postal_code = entry.data[CONF_POSTAL_CODE]

    async def async_update_data():
        _LOGGER.debug("Fetching disruption data for %s, %s", town, postal_code)
        try:
            url = "https://ennatuurlijk.nl/storingen"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = await hass.async_add_executor_job(
                lambda: requests.get(url, headers=headers)
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            _LOGGER.debug("Successfully fetched page, parsing disruptions")
            result = parse_disruptions(soup, town, postal_code)
            _LOGGER.debug("Parsed data: %s", result)
            return result
        except requests.RequestException as e:
            _LOGGER.error("Network error fetching disruption data: %s", str(e))
            return {
                "planned": {"state": False, "dates": []},
                "current": {"state": False, "dates": []},
                "solved": {"state": False, "dates": []},
                "details": f"Network error: {str(e)}",
                "disruptions": [],
                "town": town,
                "postal_code": postal_code
            }
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

    # Removed hass.loop, as it's not required and causes errors
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,  # Pass the logger as required by your Home Assistant version
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    _LOGGER.debug("Performing initial data refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("Initial refresh successful")

    _LOGGER.debug("Adding EnnatuurlijkSensor entity")
    async_add_entities([
        EnnatuurlijkSensor(coordinator, entry),
        EnnatuurlijkPlannedSensor(coordinator, entry),
        EnnatuurlijkCurrentSensor(coordinator, entry),
        EnnatuurlijkSolvedSensor(coordinator, entry),
        EnnatuurlijkDetailsSensor(coordinator, entry)
    ])
    _LOGGER.info("Entity setup completed for %s, %s", town, postal_code)

def get_sections(soup):
    sections = {
        "current": soup.find("div", id="current"),
        "planned": soup.find("div", id="planned"),
        "completed": soup.find("div", id="completed")
    }
    _LOGGER.debug("Found sections: %s", {k: bool(v) for k, v in sections.items()})
    return sections

def matches_location(title, town, postal_code, postal_code_partial):
    match = (
        town.lower() in title.lower()
        or postal_code in title
        or postal_code_partial in title
    )
    _LOGGER.debug("Location match for title '%s' with %s, %s, %s: %s", title, town, postal_code, postal_code_partial, match)
    return match

def extract_date(disruption, date_pattern):
    import re
    expectation = disruption.find("div", class_="expectation")
    if not expectation:
        _LOGGER.debug("No expectation div found in disruption")
        return ""
    value = expectation.find("div", class_="value")
    date = value.get_text(strip=True) if value else ""
    match = date and re.match(date_pattern, date, re.IGNORECASE)
    if match:
        # Convert Dutch month names to numbers
        months = {
            "januari": "01", "februari": "02", "maart": "03", "april": "04", "mei": "05", "juni": "06",
            "juli": "07", "augustus": "08", "september": "09", "oktober": "10", "november": "11", "december": "12"
        }
        m = re.match(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date, re.IGNORECASE)
        if m:
            day = m.group(1).zfill(2)
            month = months.get(m.group(2).lower(), "01")
            year = m.group(3)
            return f"{day}-{month}-{year}"
    _LOGGER.debug("Extracted date from disruption: %s, matches pattern: %s", date, match)
    return date if match else ""

def parse_disruption_article(disruption, section_name, town, postal_code, postal_code_partial, date_pattern):
    title_elem = disruption.find("h4", class_="h3")
    title = title_elem.get_text(strip=True) if title_elem else ""
    _LOGGER.debug("Processing disruption article, title: %s, section: %s", title, section_name)
    if not matches_location(title, town, postal_code, postal_code_partial):
        return None
    date = extract_date(disruption, date_pattern)
    if date:
        _LOGGER.debug("Parsed disruption: %s, %s, %s", section_name, title, date)
        return (section_name, title, date)
    return None

def parse_section(section, section_name, town, postal_code, postal_code_partial, date_pattern):
    disruptions_info = []
    if not section:
        _LOGGER.debug("Section %s not found on the page", section_name)
        return disruptions_info
    disruptions = section.find_all("article", class_="node--type-malfunction")
    _LOGGER.debug("Found %d disruptions in section %s", len(disruptions), section_name)
    for disruption in disruptions:
        info = parse_disruption_article(disruption, section_name, town, postal_code, postal_code_partial, date_pattern)
        if info:
            disruptions_info.append(info)
    return disruptions_info

def build_result(town, postal_code):
    return {
        "planned": {"state": False, "dates": []},
        "current": {"state": False, "dates": []},
        "solved": {"state": False, "dates": []},
        "details": "No disruptions found.",
        "disruptions": [],
        "town": town,
        "postal_code": postal_code
    }

def parse_disruptions(soup, town, postal_code):
    date_pattern = r'\b(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4})\b'
    sections = get_sections(soup)
    postal_code_partial = postal_code[:4]
    section_map = {
        "current": ("current", "Current disruption: {title} ({date})\n"),
        "planned": ("planned", "Planned disruption: {title} ({date})\n"),
        "completed": ("solved", "Solved disruption: {title} ({date})\n"),
    }
    result = build_result(town, postal_code)
    details_lines = []
    for section_name, section in sections.items():
        disruptions_info = parse_section(section, section_name, town, postal_code, postal_code_partial, date_pattern)
        for sec, title, date in disruptions_info:
            key, details_fmt = section_map[sec]
            result[key]["state"] = True
            result[key]["dates"].append({"description": title, "date": date})
            details_lines.append(details_fmt.format(title=title, date=date))
            result["disruptions"].append({
                "title": title,
                "date": date,
                "status": sec
            })
    result["details"] = "".join(details_lines) if details_lines else "No disruptions found."
    _LOGGER.debug("Final parsed result: %s", result)
    return result

class EnnatuurlijkSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_icon = "mdi:alert"
        self._attr_name = DOMAIN  # Uses entity.sensor.ennatuurlijk_disruptions.name
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
        self._attr_name = "planned"  # Uses entity.sensor.ennatuurlijk_disruptions.planned.name

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
        self._attr_name = "current"  # Uses entity.sensor.ennatuurlijk_disruptions.current.name

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
        self._attr_name = "solved"  # Uses entity.sensor.ennatuurlijk_disruptions.solved.name

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
        self._attr_name = "details"  # Uses entity.sensor.ennatuurlijk_disruptions.details.name

    @property
    def state(self):
        return self.coordinator.data.get("details")

    @property
    def available(self):
        return self.coordinator.data is not None
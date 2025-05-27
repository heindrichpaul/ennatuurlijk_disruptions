import requests
from bs4 import BeautifulSoup
import re
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE, SCAN_INTERVAL

async def async_setup_entry(hass, entry, async_add_entities):
    town = entry.data[CONF_TOWN]
    postal_code = entry.data[CONF_POSTAL_CODE]

    async def async_update_data():
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
            return parse_disruptions(soup, town, postal_code)
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {str(e)}")

    coordinator = DataUpdateCoordinator(
        hass,
        hass.loop,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([EnnatuurlijkSensor(coordinator, entry)])

def get_sections(soup):
    return {
        "current": soup.find("div", id="current"),
        "planned": soup.find("div", id="planned"),
        "completed": soup.find("div", id="completed")
    }

def matches_location(title, town, postal_code, postal_code_partial):
    return (
        town.lower() in title.lower()
        or postal_code in title
        or postal_code_partial in title
    )

def extract_date(disruption, date_pattern):
    expectation = disruption.find("div", class_="expectation")
    if not expectation:
        return ""
    value = expectation.find("div", class_="value")
    date = value.get_text(strip=True) if value else ""
    if date and re.match(date_pattern, date, re.IGNORECASE):
        return date
    return ""

def parse_disruption_article(disruption, section_name, town, postal_code, postal_code_partial, date_pattern):
    title_elem = disruption.find("h4", class_="h3")
    title = title_elem.get_text(strip=True) if title_elem else ""
    if not matches_location(title, town, postal_code, postal_code_partial):
        return None
    date = extract_date(disruption, date_pattern)
    if date:
        return (section_name, title, date)
    return None

def parse_section(section, section_name, town, postal_code, postal_code_partial, date_pattern):
    disruptions_info = []
    if not section:
        return disruptions_info
    disruptions = section.find_all("article", class_="node--type-malfunction")
    for disruption in disruptions:
        info = parse_disruption_article(disruption, section_name, town, postal_code, postal_code_partial, date_pattern)
        if info:
            disruptions_info.append(info)
    return disruptions_info

def build_result(town, postal_code):
    return {
        "planned": False,
        "current": False,
        "solved": False,
        "details": "",
        "dates": [],
        "town": town,
        "postal_code": postal_code
    }

def parse_disruptions(soup, town, postal_code):
    date_pattern = r'\b(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4})\b'
    sections = get_sections(soup)
    postal_code_partial = postal_code[:4]
    section_map = {
        "current": ("current", "Current disruption: {title} ({date})\n", "Current: {title} - {date}", "current"),
        "planned": ("planned", "Planned disruption: {title} ({date})\n", "Planned: {title} - {date}", "planned"),
        "completed": ("solved", "Solved disruption: {title} ({date})\n", "Solved: {title} - {date}", "solved"),
    }
    result = build_result(town, postal_code)
    for section_name, section in sections.items():
        disruptions_info = parse_section(section, section_name, town, postal_code, postal_code_partial, date_pattern)
        for sec, title, date in disruptions_info:
            key, details_fmt, dates_fmt, _ = section_map[sec]
            result[key] = True
            result["details"] += details_fmt.format(title=title, date=date)
            result["dates"].append(dates_fmt.format(title=title, date=date))
    return result

class EnnatuurlijkSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__()
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = "Ennatuurlijk Disruptions"
        self._attr_icon = "mdi:alert"

    @property
    def state(self):
        return "on" if (self.coordinator.data.get("planned") or self.coordinator.data.get("current")) else "off"

    @property
    def extra_state_attributes(self):
        return self.coordinator.data

    @property
    def available(self):
        return self.coordinator.data is not None
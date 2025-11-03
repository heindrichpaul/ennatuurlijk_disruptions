from __future__ import annotations

from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    _LOGGER,
    CONF_TOWN,
    CONF_POSTAL_CODE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MONTH_TO_NUMBER,
    ENNATUURLIJK_DISRUPTIONS_URL,
    ENNATUURLIJK_HEADERS,
)


# HTML Parsing Functions


def get_sections(soup):
    sections = {
        "current": soup.find("div", id="current"),
        "planned": soup.find("div", id="planned"),
        "completed": soup.find("div", id="completed"),
    }
    _LOGGER.debug("Found sections: %s", {k: bool(v) for k, v in sections.items()})

    # Additional debug info about sections content
    for section_name, section in sections.items():
        if section:
            articles = section.find_all("article", class_="node--type-malfunction")
            _LOGGER.debug(
                "Section '%s' contains %d articles", section_name, len(articles)
            )
            for i, article in enumerate(articles):
                title_elem = article.find("h4", class_="h3")
                title = title_elem.get_text(strip=True) if title_elem else "No title"
                _LOGGER.debug("  Article %d in '%s': %s", i + 1, section_name, title)
        else:
            _LOGGER.debug("Section '%s' not found in HTML", section_name)

    return sections


def matches_location(title, town, postal_code, postal_code_partial):
    postal_code_spaced = (
        f"{postal_code_partial} {postal_code[4:]}"
        if len(postal_code) > 4
        else postal_code_partial
    )

    # Check each condition individually for detailed logging
    town_match = town.lower() in title.lower()
    postal_match = postal_code in title
    partial_match = postal_code_partial in title
    spaced_match = postal_code_spaced in title

    match = town_match or postal_match or partial_match or spaced_match

    _LOGGER.debug("Location matching for title '%s':", title)
    _LOGGER.debug("  Town match ('%s' in title): %s", town.lower(), town_match)
    _LOGGER.debug(
        "  Full postal code match ('%s' in title): %s", postal_code, postal_match
    )
    _LOGGER.debug(
        "  Partial postal code match ('%s' in title): %s",
        postal_code_partial,
        partial_match,
    )
    _LOGGER.debug(
        "  Spaced postal code match ('%s' in title): %s",
        postal_code_spaced,
        spaced_match,
    )
    _LOGGER.debug("  Overall match result: %s", match)

    return match


def extract_date(disruption, date_pattern):
    import re

    expectation = disruption.find("div", class_="expectation")
    if not expectation:
        _LOGGER.debug("No expectation div found in disruption article")
        return ""

    value = expectation.find("div", class_="value")
    if not value:
        _LOGGER.debug("No value div found in expectation div")
        return ""

    date = value.get_text(strip=True)
    _LOGGER.debug("Raw date text from expectation value: '%s'", date)

    match = date and re.match(date_pattern, date, re.IGNORECASE)
    _LOGGER.debug(
        "Date pattern match for '%s': %s (pattern: %s)", date, bool(match), date_pattern
    )

    if match:
        m = re.match(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date, re.IGNORECASE)
        if m:
            day = m.group(1).zfill(2)
            month = MONTH_TO_NUMBER.get(m.group(2).lower(), "01")
            year = m.group(3)
            formatted_date = f"{day}-{month}-{year}"
            _LOGGER.debug(
                "Formatted date: %s (from %s %s %s)",
                formatted_date,
                day,
                m.group(2),
                year,
            )
            return formatted_date

    return date if match else ""


def parse_disruption_article(
    disruption, section_name, town, postal_code, postal_code_partial, date_pattern
):
    title_elem = disruption.find("h4", class_="h3")
    title = title_elem.get_text(strip=True) if title_elem else ""
    _LOGGER.debug("Parsing article in section '%s': title='%s'", section_name, title)

    # Robustly find a link to the disruption if present (any <a> in the article)
    link_elem = disruption.find("a", href=True)
    link = None
    if link_elem:
        link = link_elem["href"]
        if link and link.startswith("/"):
            link = f"https://ennatuurlijk.nl{link}"
        _LOGGER.debug("Found link for article: %s", link)
    else:
        _LOGGER.debug("No link found for article: %s", title)

    # Check location match
    location_match = matches_location(title, town, postal_code, postal_code_partial)
    if not location_match:
        _LOGGER.debug(
            "Article '%s' does not match location criteria (town=%s, postal_code=%s)",
            title,
            town,
            postal_code,
        )
        return None

    _LOGGER.debug("Article '%s' matches location, extracting date...", title)
    date = extract_date(disruption, date_pattern)

    if date:
        _LOGGER.debug(
            "Successfully parsed disruption: section=%s, title=%s, date=%s, link=%s",
            section_name,
            title,
            date,
            link,
        )
        return (section_name, title, date, link)
    else:
        _LOGGER.debug("Failed to extract date from article '%s', skipping", title)
        return None


def parse_section(
    section, section_name, town, postal_code, postal_code_partial, date_pattern
):
    disruptions_info = []
    if not section:
        _LOGGER.debug("Section %s not found on the page", section_name)
        return disruptions_info

    disruptions = section.find_all("article", class_="node--type-malfunction")
    _LOGGER.debug("Found %d disruptions in section %s", len(disruptions), section_name)

    for i, disruption in enumerate(disruptions):
        _LOGGER.debug(
            "Processing disruption %d/%d in section '%s'",
            i + 1,
            len(disruptions),
            section_name,
        )
        info = parse_disruption_article(
            disruption,
            section_name,
            town,
            postal_code,
            postal_code_partial,
            date_pattern,
        )
        if info:
            disruptions_info.append(info)
            _LOGGER.debug(
                "Added disruption %d to results: %s", i + 1, info[1]
            )  # info[1] is the title
        else:
            _LOGGER.debug("Skipped disruption %d (no match or invalid)", i + 1)

    _LOGGER.debug(
        "Section '%s' processing complete: %d valid disruptions found",
        section_name,
        len(disruptions_info),
    )
    return disruptions_info


def build_result(town, postal_code):
    return {
        "planned": {"state": False, "dates": []},
        "current": {"state": False, "dates": []},
        "solved": {"state": False, "dates": []},
        "details": "No disruptions found.",
        "disruptions": [],
        "town": town,
        "postal_code": postal_code,
    }


def parse_disruptions(soup, town, postal_code):
    date_pattern = r"\b(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4})\b"
    _LOGGER.debug(
        "Starting disruption parsing for town='%s', postal_code='%s'", town, postal_code
    )
    _LOGGER.debug("Using date pattern: %s", date_pattern)

    sections = get_sections(soup)
    postal_code_partial = postal_code[:4]
    _LOGGER.debug("Postal code partial (first 4 digits): %s", postal_code_partial)

    section_map = {
        "current": ("current", "Current disruption: {title} ({date})\n"),
        "planned": ("planned", "Planned disruption: {title} ({date})\n"),
        "completed": ("solved", "Solved disruption: {title} ({date})\n"),
    }

    result = build_result(town, postal_code)
    details_lines = []

    for section_name, section in sections.items():
        _LOGGER.debug("Processing section: %s", section_name)
        disruptions_info = parse_section(
            section, section_name, town, postal_code, postal_code_partial, date_pattern
        )

        for info in disruptions_info:
            sec, title, date, link = info if len(info) == 4 else (*info, None)
            key, details_fmt = section_map[sec]
            result[key]["state"] = True
            result[key]["dates"].append(
                {"description": title, "date": date, "link": link}
            )
            details_lines.append(details_fmt.format(title=title, date=date))
            result["disruptions"].append(
                {"title": title, "date": date, "status": sec, "link": link}
            )
            _LOGGER.debug(
                "Added to final result: %s disruption '%s' on %s", sec, title, date
            )

    result["details"] = (
        "".join(details_lines) if details_lines else "No disruptions found."
    )
    _LOGGER.debug(
        "Parsing complete. Total disruptions found: %d", len(result["disruptions"])
    )
    _LOGGER.debug(
        "Final result summary: planned=%s, current=%s, solved=%s",
        result["planned"]["state"],
        result["current"]["state"],
        result["solved"]["state"],
    )

    return result


# Async Fetch Functions


async def fetch_disruption_section(hass, section: str, town: str, postal_code: str):
    """
    Fetch and parse a specific disruption section (planned, current, solved) for a given town and postal code.
    Returns a dict with the parsed data for the section, including last_update_date and last_update_success.
    """
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    _LOGGER.debug(
        "Starting fetch for section='%s', town='%s', postal_code='%s'",
        section,
        town,
        postal_code,
    )

    try:
        url = ENNATUURLIJK_DISRUPTIONS_URL
        headers = ENNATUURLIJK_HEADERS
        session = async_get_clientsession(hass)

        _LOGGER.debug("Fetching HTML from: %s", url)
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            html = await response.text()

        _LOGGER.debug("Successfully fetched HTML content (%d characters)", len(html))

        # Parse HTML in executor since BeautifulSoup is CPU-intensive
        _LOGGER.debug("Parsing HTML with BeautifulSoup...")
        soup = await hass.async_add_executor_job(
            lambda: BeautifulSoup(html, "html.parser")
        )

        _LOGGER.debug("Parsing disruptions data...")
        all_data = await hass.async_add_executor_job(
            parse_disruptions, soup, town, postal_code
        )

        # Set last_update_date as a string (YYYY-MM-DD HH:MM) for sensors
        now = datetime.now()
        all_data["last_update_date"] = now.strftime("%Y-%m-%d %H:%M")
        all_data["last_update_success"] = now  # keep for compatibility

        _LOGGER.debug("Extracting section '%s' from parsed data", section)
        section_data = all_data.get(section)
        # Inject last_update_date and last_update_success into section dict for sensor attributes
        if section_data is not None:
            section_data = dict(section_data)  # copy to avoid mutating all_data
            section_data["last_update_date"] = all_data["last_update_date"]
            section_data["last_update_success"] = all_data["last_update_success"]
            _LOGGER.debug(
                "Section '%s' data prepared successfully: state=%s, %d dates",
                section,
                section_data.get("state"),
                len(section_data.get("dates", [])),
            )
        else:
            _LOGGER.warning("Section '%s' not found in parsed data", section)
        return section_data
    except Exception as e:
        _LOGGER.error(
            "Error fetching section '%s' for town='%s', postal_code='%s': %s",
            section,
            town,
            postal_code,
            e,
        )
        _LOGGER.debug("Exception details:", exc_info=True)
        return None


# Coordinator Class



def _get_update_interval_minutes(entry, global_entry=None) -> int:
    """Return the update interval from global entry if present, else from entry, or default."""
    if global_entry is not None:
        # Prefer options, then data
        return global_entry.options.get(
            CONF_UPDATE_INTERVAL,
            global_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
    return entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )



class EnnatuurlijkCoordinator(DataUpdateCoordinator):
    """Coordinator for Ennatuurlijk disruptions integration."""

    def __init__(self, hass: HomeAssistant, entry, global_entry=None) -> None:
        """Initialize the coordinator. Use global_entry for global settings if provided."""
        update_interval = timedelta(minutes=_get_update_interval_minutes(entry, global_entry))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry = entry
        self.global_entry = global_entry

    @property
    def days_to_keep_solved(self) -> int:
        """Return the days to keep solved disruptions from global entry if present, else from entry, or default."""
        entry = self.global_entry if self.global_entry is not None else self.entry
        # Prefer options, then data
        return entry.options.get(
            "days_to_keep_solved",
            entry.data.get("days_to_keep_solved", 7),
        )

    @property
    def planned(self):
        """Return planned disruptions data."""
        return (
            self.data.get("planned", {"state": False, "dates": []})
            if self.data
            else {"state": False, "dates": []}
        )

    @property
    def current(self):
        """Return current disruptions data."""
        return (
            self.data.get("current", {"state": False, "dates": []})
            if self.data
            else {"state": False, "dates": []}
        )

    @property
    def solved(self):
        """Return solved disruptions data."""
        return (
            self.data.get("solved", {"state": False, "dates": []})
            if self.data
            else {"state": False, "dates": []}
        )

    @property
    def town(self):
        """Return the town being monitored."""
        return self.entry.data[CONF_TOWN]

    @property
    def postal_code(self):
        """Return the postal code being monitored."""
        return self.entry.data[CONF_POSTAL_CODE]

    async def _async_update_data(self):
        """Fetch data from Ennatuurlijk."""
        town = self.town
        postal_code = self.postal_code
        _LOGGER.debug("Fetching all disruption data for %s, %s", town, postal_code)
        try:
            planned = await fetch_disruption_section(
                self.hass, "planned", town, postal_code
            )
            current = await fetch_disruption_section(
                self.hass, "current", town, postal_code
            )
            solved = await fetch_disruption_section(
                self.hass, "solved", town, postal_code
            )
            # Purge solved disruptions older than days_to_keep_solved
            if solved and solved.get("dates"):
                keep_days = self.days_to_keep_solved
                now = datetime.now().date()
                filtered = []
                for d in solved["dates"]:
                    try:
                        d_date = datetime.strptime(d["date"], "%d-%m-%Y").date()
                        if (now - d_date).days <= keep_days:
                            filtered.append(d)
                    except Exception:
                        filtered.append(d)  # keep if date parse fails
                solved["dates"] = filtered
            result = {
                "planned": planned or {"state": False, "dates": []},
                "current": current or {"state": False, "dates": []},
                "solved": solved or {"state": False, "dates": []},
                "details": "See attributes for details.",
                "disruptions": [],
                "town": town,
                "postal_code": postal_code,
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
                "postal_code": postal_code,
            }


def create_coordinator(hass: HomeAssistant, entry, global_entry=None) -> EnnatuurlijkCoordinator:
    """Create the EnnatuurlijkCoordinator for this config entry, using global_entry for settings if provided."""
    return EnnatuurlijkCoordinator(hass, entry, global_entry=global_entry)

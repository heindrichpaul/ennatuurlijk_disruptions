import requests
from bs4 import BeautifulSoup
from .const import _LOGGER, MONTH_TO_NUMBER, ENNATUURLIJK_DISRUPTIONS_URL, ENNATUURLIJK_HEADERS
from datetime import datetime


def get_sections(soup):
    sections = {
        "current": soup.find("div", id="current"),
        "planned": soup.find("div", id="planned"),
        "completed": soup.find("div", id="completed")
    }
    _LOGGER.debug("Found sections: %s", {k: bool(v) for k, v in sections.items()})
    return sections


def matches_location(title, town, postal_code, postal_code_partial):
    postal_code_spaced = f"{postal_code_partial} {postal_code[4:]}" if len(postal_code) > 4 else postal_code_partial
    match = (
        town.lower() in title.lower()
        or postal_code in title
        or postal_code_partial in title
        or postal_code_spaced in title
    )
    _LOGGER.debug("Location match for title '%s' with %s, %s, %s, %s: %s", title, town, postal_code, postal_code_partial, postal_code_spaced, match)
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
        m = re.match(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date, re.IGNORECASE)
        if m:
            day = m.group(1).zfill(2)
            month = MONTH_TO_NUMBER.get(m.group(2).lower(), "01")
            year = m.group(3)
            return f"{day}-{month}-{year}"
    _LOGGER.debug("Extracted date from disruption: %s, matches pattern: %s", date, match)
    return date if match else ""


def parse_disruption_article(disruption, section_name, town, postal_code, postal_code_partial, date_pattern):
    title_elem = disruption.find("h4", class_="h3")
    title = title_elem.get_text(strip=True) if title_elem else ""
    # Try to find a link to the disruption if present
    link_elem = title_elem.find("a") if title_elem else None
    link = link_elem["href"] if link_elem and link_elem.has_attr("href") else None
    _LOGGER.debug("Processing disruption article, title: %s, section: %s, link: %s", title, section_name, link)
    if not matches_location(title, town, postal_code, postal_code_partial):
        return None
    date = extract_date(disruption, date_pattern)
    if date:
        _LOGGER.debug("Parsed disruption: %s, %s, %s, %s", section_name, title, date, link)
        return (section_name, title, date, link)
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
        for info in disruptions_info:
            sec, title, date, link = info if len(info) == 4 else (*info, None)
            key, details_fmt = section_map[sec]
            result[key]["state"] = True
            result[key]["dates"].append({"description": title, "date": date, "link": link})
            details_lines.append(details_fmt.format(title=title, date=date))
            result["disruptions"].append({
                "title": title,
                "date": date,
                "status": sec,
                "link": link
            })
    result["details"] = "".join(details_lines) if details_lines else "No disruptions found."
    _LOGGER.debug("Final parsed result: %s", result)
    return result


def fetch_disruption_section(section: str, town: str, postal_code: str):
    """
    Fetch and parse a specific disruption section (planned, current, solved) for a given town and postal code.
    Returns a dict with the parsed data for the section, including last_update_date and last_update_success.
    """
    try:
        url = ENNATUURLIJK_DISRUPTIONS_URL
        headers = ENNATUURLIJK_HEADERS
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        all_data = parse_disruptions(soup, town, postal_code)
        # Set last_update_date as a string (YYYY-MM-DD HH:MM) for sensors
        now = datetime.now()
        all_data["last_update_date"] = now.strftime("%Y-%m-%d %H:%M")
        all_data["last_update_success"] = now  # keep for compatibility
        section_data = all_data.get(section)
        # Inject last_update_date and last_update_success into section dict for sensor attributes
        if section_data is not None:
            section_data = dict(section_data)  # copy to avoid mutating all_data
            section_data["last_update_date"] = all_data["last_update_date"]
            section_data["last_update_success"] = all_data["last_update_success"]
        return section_data
    except Exception as e:
        _LOGGER.error(f"Error fetching section '{section}': {e}")
        return None


def fetch_all_disruptions(town: str, postal_code: str):
    """
    Fetch and parse all disruption sections (planned, current, solved) for a given town and postal code.
    Returns a dict with all parsed data.
    """
    planned = fetch_disruption_section("planned", town, postal_code)
    current = fetch_disruption_section("current", town, postal_code)
    solved = fetch_disruption_section("solved", town, postal_code)
    return {
        "planned": planned or {"state": False, "dates": []},
        "current": current or {"state": False, "dates": []},
        "solved": solved or {"state": False, "dates": []},
    }

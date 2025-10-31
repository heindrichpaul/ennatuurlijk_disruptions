"""Sensor descriptions for Ennatuurlijk Disruptions."""

from __future__ import annotations

from datetime import datetime, date

from .entity import EnnatuurlijkSensorEntityDescription
from .const import (
    ATTR_ERROR,
    ATTR_FRIENDLY_NAME,
    ATTR_YEAR_MONTH_DAY_DATE,
    ATTR_LAST_UPDATE,
    ATTR_DAYS_UNTIL_PLANNED_DATE,
    ATTR_DAYS_SINCE_CURRENT_DATE,
    ATTR_DAYS_SINCE_SOLVED_DATE,
    ATTR_IS_PLANNED_DATE_TODAY,
    ATTR_IS_CURRENT_DATE_TODAY,
    ATTR_IS_SOLVED_DATE_TODAY,
)


def _get_closest_date(data: dict, today: date) -> date | None:
    """Get the closest date from disruption data."""
    dates = [d["date"] for d in data.get("dates", []) if d.get("date")]
    if not dates:
        return None
    date_objs = [datetime.strptime(d, "%d-%m-%Y").date() for d in dates]
    return min(date_objs, key=lambda d: abs((d - today).days))


def _get_closest_disruption(data: dict, today: date) -> dict | None:
    """Get the closest disruption from disruption data."""
    dates = data.get("dates", [])
    if not dates:
        return None

    valid_dates = [d for d in dates if d and d.get("date")]
    if not valid_dates:
        return None

    return min(
        valid_dates,
        key=lambda d: abs(
            (datetime.strptime(d["date"], "%d-%m-%Y").date() - today).days
        ),
    )


def _build_common_attributes(
    data: dict, today: date, name: str, days_key: str, is_today_key: str
) -> dict:
    """Build common attributes for disruption sensors."""
    dates = data.get("dates", [])
    closest_date = _get_closest_date(data, today)
    closest_disruption = _get_closest_disruption(data, today)

    days_diff = None
    if closest_date:
        days_diff = (
            (today - closest_date).days
            if days_key.startswith("days_since")
            else (closest_date - today).days
        )

    return {
        ATTR_ERROR: False,
        ATTR_FRIENDLY_NAME: name,
        ATTR_YEAR_MONTH_DAY_DATE: closest_date.strftime("%Y-%m-%d")
        if closest_date
        else None,
        ATTR_LAST_UPDATE: data.get("last_update_date"),
        days_key: days_diff,
        is_today_key: closest_date == today if closest_date else False,
        "dates": dates,
        "icon": "mdi:calendar-alert",
        "latest_link": closest_disruption.get("link") if closest_disruption else None,
        "latest_description": closest_disruption.get("description")
        if closest_disruption
        else None,
        "disruption_count": len(dates),
        "next_disruption_date": closest_date.strftime("%Y-%m-%d")
        if closest_date
        else None,
    }


def _planned_value_fn(data: dict, today: date) -> str | None:
    """Calculate planned sensor value - next future date."""
    dates = [d["date"] for d in data.get("dates", []) if d.get("date")]
    future_dates = [
        d for d in dates if datetime.strptime(d, "%d-%m-%Y").date() >= today
    ]
    closest_date = min(
        (datetime.strptime(d, "%d-%m-%Y").date() for d in future_dates), default=None
    )
    return closest_date.strftime("%Y-%m-%d") if closest_date else None


def _planned_attributes_fn(data: dict, today: date, name: str) -> dict:
    """Build planned sensor attributes."""
    return _build_common_attributes(
        data, today, name, ATTR_DAYS_UNTIL_PLANNED_DATE, ATTR_IS_PLANNED_DATE_TODAY
    )


def _current_value_fn(data: dict, today: date) -> str | None:
    """Calculate current sensor value - closest date."""
    closest_date = _get_closest_date(data, today)
    return closest_date.strftime("%Y-%m-%d") if closest_date else None


def _current_attributes_fn(data: dict, today: date, name: str) -> dict:
    """Build current sensor attributes."""
    return _build_common_attributes(
        data, today, name, ATTR_DAYS_SINCE_CURRENT_DATE, ATTR_IS_CURRENT_DATE_TODAY
    )


def _solved_value_fn(data: dict, today: date) -> str | None:
    """Calculate solved sensor value - closest date."""
    closest_date = _get_closest_date(data, today)
    return closest_date.strftime("%Y-%m-%d") if closest_date else None


def _solved_attributes_fn(data: dict, today: date, name: str) -> dict:
    """Build solved sensor attributes."""
    return _build_common_attributes(
        data, today, name, ATTR_DAYS_SINCE_SOLVED_DATE, ATTR_IS_SOLVED_DATE_TODAY
    )


SENSOR_TYPES: tuple[EnnatuurlijkSensorEntityDescription, ...] = (
    EnnatuurlijkSensorEntityDescription(
        key="planned",
        translation_key="ennatuurlijk_disruptions_planned",
        name="Planned",
        icon="mdi:calendar-alert",
        data_key="planned",
        value_fn=_planned_value_fn,
        attributes_fn=_planned_attributes_fn,
    ),
    EnnatuurlijkSensorEntityDescription(
        key="current",
        translation_key="ennatuurlijk_disruptions_current",
        name="Current",
        icon="mdi:alert-circle",
        data_key="current",
        value_fn=_current_value_fn,
        attributes_fn=_current_attributes_fn,
    ),
    EnnatuurlijkSensorEntityDescription(
        key="solved",
        translation_key="ennatuurlijk_disruptions_solved",
        name="Solved",
        icon="mdi:check-circle",
        data_key="solved",
        value_fn=_solved_value_fn,
        attributes_fn=_solved_attributes_fn,
    ),
)

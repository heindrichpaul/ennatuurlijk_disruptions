"""Binary sensor descriptions for Ennatuurlijk Disruptions."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .entity import EnnatuurlijkBinarySensorEntityDescription
from .const import (
    ATTR_ERROR,
    ATTR_FRIENDLY_NAME,
    ATTR_LAST_UPDATE,
)


def _alert_is_on_fn(data: dict) -> bool:
    """Determine if alert is on."""
    return bool(data.get("state"))


def _alert_attributes_fn(data: dict) -> dict:
    """Build alert sensor attributes."""
    return {
        ATTR_ERROR: False,
        ATTR_FRIENDLY_NAME: data.get("friendly_name", ""),
        ATTR_LAST_UPDATE: data.get("last_update_date"),
        "dates": data.get("dates", []),
        "icon": "mdi:alert",
    }


BINARY_SENSOR_TYPES: tuple[EnnatuurlijkBinarySensorEntityDescription, ...] = (
    EnnatuurlijkBinarySensorEntityDescription(
        key="planned_alert",
        translation_key="ennatuurlijk_disruptions_planned_alert",
        name="Planned Alert",
        icon="mdi:alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        data_key="planned",
        is_on_fn=_alert_is_on_fn,
        attributes_fn=_alert_attributes_fn,
    ),
    EnnatuurlijkBinarySensorEntityDescription(
        key="current_alert",
        translation_key="ennatuurlijk_disruptions_current_alert",
        name="Current Alert",
        icon="mdi:alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        data_key="current",
        is_on_fn=_alert_is_on_fn,
        attributes_fn=_alert_attributes_fn,
    ),
    EnnatuurlijkBinarySensorEntityDescription(
        key="solved_alert",
        translation_key="ennatuurlijk_disruptions_solved_alert",
        name="Solved Alert",
        icon="mdi:alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        data_key="solved",
        is_on_fn=_alert_is_on_fn,
        attributes_fn=_alert_attributes_fn,
    ),
)

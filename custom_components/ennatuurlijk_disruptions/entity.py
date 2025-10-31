"""Base entity classes for Ennatuurlijk Disruptions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from datetime import datetime, date

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import _LOGGER, DOMAIN
from .coordinator import EnnatuurlijkCoordinator


@dataclass
class EnnatuurlijkSensorEntityDescription(SensorEntityDescription):
    """Describes Ennatuurlijk sensor entity."""

    value_fn: Callable[[dict, date], str | None] | None = None
    attributes_fn: Callable[[dict, date, str], dict] | None = None
    data_key: str | None = (
        None  # Key to access coordinator data (e.g., "planned", "current", "solved")
    )


@dataclass
class EnnatuurlijkBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Ennatuurlijk binary sensor entity."""

    is_on_fn: Callable[[dict], bool] | None = None
    attributes_fn: Callable[[dict], dict] | None = None
    data_key: str | None = None  # Key to access coordinator data


class EnnatuurlijkEntity(CoordinatorEntity):
    """Base class for Ennatuurlijk entities."""

    def __init__(
        self,
        coordinator: EnnatuurlijkCoordinator,
        entry,
        description: SensorEntityDescription | BinarySensorEntityDescription,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"

        # Set device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Ennatuurlijk Disruptions {entry.data.get('town', '')}",
            "manufacturer": "Ennatuurlijk",
            "model": "Disruption Monitor",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class EnnatuurlijkSensor(EnnatuurlijkEntity, SensorEntity):
    """Base class for Ennatuurlijk sensors."""

    entity_description: EnnatuurlijkSensorEntityDescription

    def __init__(
        self,
        coordinator: EnnatuurlijkCoordinator,
        entry,
        description: EnnatuurlijkSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, entry, description)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if not self.entity_description.data_key:
            return None

        data = getattr(self.coordinator, self.entity_description.data_key)
        today = datetime.now().date()

        if self.entity_description.value_fn:
            value = self.entity_description.value_fn(data, today)
            _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {value}")
            return value

        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.entity_description.data_key:
            return {}

        data = getattr(self.coordinator, self.entity_description.data_key)
        today = datetime.now().date()
        name = self.name or ""

        if self.entity_description.attributes_fn:
            attrs = self.entity_description.attributes_fn(data, today, name)
            _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
            return attrs

        return {}


class EnnatuurlijkBinarySensor(EnnatuurlijkEntity, BinarySensorEntity):
    """Base class for Ennatuurlijk binary sensors."""

    entity_description: EnnatuurlijkBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: EnnatuurlijkCoordinator,
        entry,
        description: EnnatuurlijkBinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry, description)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if not self.entity_description.data_key:
            return False

        data = getattr(self.coordinator, self.entity_description.data_key)

        if self.entity_description.is_on_fn:
            value = self.entity_description.is_on_fn(data)
            _LOGGER.debug(f"[{self._attr_unique_id}] State computed: {value}")
            return value

        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.entity_description.data_key:
            return {}

        data = getattr(self.coordinator, self.entity_description.data_key)

        if self.entity_description.attributes_fn:
            attrs = self.entity_description.attributes_fn(data)
            _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
            return attrs

        return {}

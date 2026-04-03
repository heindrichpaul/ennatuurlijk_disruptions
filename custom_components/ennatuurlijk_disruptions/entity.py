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


@dataclass(frozen=True)
class EnnatuurlijkSensorEntityDescription(SensorEntityDescription):
    """Describes Ennatuurlijk sensor entity."""

    value_fn: Callable[[dict, date], str | None] | None = None
    attributes_fn: Callable[[dict, date, str], dict] | None = None
    data_key: str | None = None  # Key for coordinator data


@dataclass(frozen=True)
class EnnatuurlijkBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Ennatuurlijk binary sensor entity."""

    is_on_fn: Callable[[dict], bool] | None = None
    attributes_fn: Callable[[dict], dict] | None = None
    data_key: str | None = None  # Key for coordinator data


class EnnatuurlijkEntity(CoordinatorEntity):
    """Base class for Ennatuurlijk entities."""

    @property
    def has_entity_name(self) -> bool:
        return True

    def __init__(
        self,
        coordinator: EnnatuurlijkCoordinator,
        subentry,
        description: SensorEntityDescription | BinarySensorEntityDescription,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._subentry = subentry
        # Use subentry data for unique_id and device info
        self._attr_unique_id = f"{DOMAIN}_{subentry.unique_id}_{description.key}"
        # Device info for subentry (each location is a separate device)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, subentry.unique_id)},
            "name": f"Ennatuurlijk Disruptions {subentry.data.get('town', '')}",
            "manufacturer": "Ennatuurlijk",
            "model": "Disruption Monitor",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class EnnatuurlijkSensor(EnnatuurlijkEntity, SensorEntity):
    @property
    def has_entity_name(self) -> bool:
        return True

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
        # Ensure name is string
        name = str(self.name) if self.name is not None else ""

        if self.entity_description.attributes_fn:
            attrs = self.entity_description.attributes_fn(data, today, name)
            _LOGGER.debug(f"[{self._attr_unique_id}] Attributes: {attrs}")
            return attrs

        return {}


class EnnatuurlijkBinarySensor(EnnatuurlijkEntity, BinarySensorEntity):
    @property
    def has_entity_name(self) -> bool:
        return True

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

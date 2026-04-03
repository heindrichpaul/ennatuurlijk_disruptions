#!/usr/bin/env python3
"""Utility functions for Ennatuurlijk Disruptions integration."""

import re
import voluptuous as vol
from .const import (
    CONF_DAYS_TO_KEEP_SOLVED,
    CONF_CREATE_ALERT_SENSORS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DAYS_TO_KEEP_SOLVED,
    DEFAULT_CREATE_ALERT_SENSORS,
    DEFAULT_UPDATE_INTERVAL,
)


class PostalCodeValidator:
    """Utility class for Dutch postal code validation and normalization."""

    @staticmethod
    def normalize(postal_code: str) -> str:
        """Normalize postal code by removing spaces and uppercasing."""
        return postal_code.replace(" ", "").upper()

    @staticmethod
    def is_valid(postal_code: str) -> bool:
        """Check if postal code matches Dutch format 1234AB."""
        return bool(re.match(r"^\d{4}[A-Z]{2}$", postal_code))

    @staticmethod
    def validate_and_normalize(postal_code: str) -> tuple[str, bool]:
        """Normalize and validate postal code. Returns (normalized_code, is_valid)."""
        normalized = PostalCodeValidator.normalize(postal_code)
        is_valid = PostalCodeValidator.is_valid(normalized)
        return normalized, is_valid


class SchemaHelper:
    """Utility class for common form schema elements."""

    @staticmethod
    def get_common_options(defaults=None):
        """Get common configuration options schema elements."""
        if defaults is None:
            defaults = {}

        return {
            vol.Optional(
                CONF_DAYS_TO_KEEP_SOLVED,
                default=defaults.get(
                    CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                ),
            ): int,
            vol.Optional(
                CONF_CREATE_ALERT_SENSORS,
                default=defaults.get(
                    CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
                ),
            ): bool,
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): int,
        }

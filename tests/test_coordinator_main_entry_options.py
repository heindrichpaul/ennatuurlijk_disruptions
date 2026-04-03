#!/usr/bin/env python3
"""Test coordinator main entry options inheritance."""

import pytest
from datetime import timedelta

from custom_components.ennatuurlijk_disruptions.coordinator import (
    EnnatuurlijkCoordinator,
    _get_update_interval_minutes,
)
from custom_components.ennatuurlijk_disruptions.const import (
    CONF_UPDATE_INTERVAL,
    CONF_DAYS_TO_KEEP_SOLVED,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_DAYS_TO_KEEP_SOLVED,
)


class MockConfigEntry:
    """Mock a main config entry with options."""

    def __init__(self, options=None, data=None):
        self.options = options or {}
        self.data = data or {}


class MockConfigSubentry:
    """Mock a config subentry."""

    def __init__(self, data=None):
        self.data = data or {}
        # Subentries don't have options attribute


@pytest.mark.asyncio
async def test_coordinator_inherits_main_entry_options(hass):
    """Test that coordinator inherits options from main entry."""
    # Create main entry with options
    main_entry = MockConfigEntry(
        options={
            CONF_UPDATE_INTERVAL: 30,
            CONF_DAYS_TO_KEEP_SOLVED: 21,
        },
        data={"name": "Ennatuurlijk Disruptions"},
    )

    # Create subentry with only location data
    subentry = MockConfigSubentry(
        data={
            "name": "Test Location",
            "town": "Utrecht",
            "postal_code": "3511AB",
        }
    )

    # Create coordinator with main entry reference
    coordinator = EnnatuurlijkCoordinator(hass, subentry, main_entry)

    # Test that coordinator reads from main entry options
    assert coordinator.days_to_keep_solved == 21
    assert coordinator.update_interval == timedelta(minutes=30)


@pytest.mark.asyncio
async def test_get_update_interval_with_main_entry(hass):
    """Test _get_update_interval_minutes with main entry."""
    # Create main entry with options
    main_entry = MockConfigEntry(options={CONF_UPDATE_INTERVAL: 45})

    # Create subentry without update interval
    subentry = MockConfigSubentry(data={"town": "Amsterdam", "postal_code": "1000AA"})

    # Should use main entry option
    interval = _get_update_interval_minutes(subentry, main_entry)
    assert interval == 45


@pytest.mark.asyncio
async def test_get_update_interval_fallback_to_default(hass):
    """Test _get_update_interval_minutes falls back to default."""
    # Create main entry without options
    main_entry = MockConfigEntry()

    # Create subentry without update interval
    subentry = MockConfigSubentry(data={"town": "Amsterdam", "postal_code": "1000AA"})

    # Should use default
    interval = _get_update_interval_minutes(subentry, main_entry)
    assert interval == DEFAULT_UPDATE_INTERVAL


@pytest.mark.asyncio
async def test_coordinator_without_main_entry_uses_defaults(hass):
    """Test coordinator fallback behavior when no main entry."""
    # Create subentry without options
    subentry = MockConfigSubentry(
        data={
            "name": "Test Location",
            "town": "Utrecht",
            "postal_code": "3511AB",
        }
    )

    # Create coordinator without main entry (backward compatibility)
    coordinator = EnnatuurlijkCoordinator(hass, subentry)

    # Should use defaults
    assert coordinator.days_to_keep_solved == DEFAULT_DAYS_TO_KEEP_SOLVED
    assert coordinator.update_interval == timedelta(minutes=DEFAULT_UPDATE_INTERVAL)


@pytest.mark.asyncio
async def test_coordinator_with_legacy_entry_options(hass):
    """Test coordinator with entry that has options (backward compatibility)."""
    # Create entry with options (old pattern)
    entry = MockConfigEntry(
        options={
            CONF_UPDATE_INTERVAL: 15,
            CONF_DAYS_TO_KEEP_SOLVED: 10,
        },
        data={
            "name": "Test Location",
            "town": "Utrecht",
            "postal_code": "3511AB",
        },
    )

    # Create coordinator without main entry
    coordinator = EnnatuurlijkCoordinator(hass, entry)

    # Should use entry options
    assert coordinator.days_to_keep_solved == 10
    assert coordinator.update_interval == timedelta(minutes=15)

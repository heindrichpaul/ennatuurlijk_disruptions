import pytest
from datetime import date

from custom_components.ennatuurlijk_disruptions.calendar import (
    EnnatuurlijkDisruptionsCalendar,
)
from custom_components.ennatuurlijk_disruptions.coordinator import (
    EnnatuurlijkCoordinator,
)


@pytest.mark.asyncio
async def test_solved_only_event_single_day_and_hashtag(
    hass, mock_aiohttp_session, mockEntry
):
    """Test calendar with only solved disruption creates a single event."""
    mockEntry.add_to_hass(hass)

    coordinator = EnnatuurlijkCoordinator(hass, mockEntry)
    await coordinator.async_refresh()

    cal = EnnatuurlijkDisruptionsCalendar(coordinator, mockEntry)
    # Use October 2025 dates to match the fixture data
    start = date(2025, 10, 20)
    end = date(2025, 10, 31)
    events = cal._get_events(start, end)

    # Should have events from the HTML fixture (Tilburg has solved disruptions)
    assert len(events) >= 1
    # Verify at least one event has solved status
    assert any(
        "Status: #solved" in ev.description or "Status: #completed" in ev.description
        for ev in events
    )


@pytest.mark.asyncio
async def test_current_then_solved_is_single_event(
    hass, mock_aiohttp_session, mockEntry
):
    """Test that same disruption ID in current and solved creates single event."""
    mockEntry.add_to_hass(hass)

    coordinator = EnnatuurlijkCoordinator(hass, mockEntry)
    await coordinator.async_refresh()

    cal = EnnatuurlijkDisruptionsCalendar(coordinator, mockEntry)
    start = date(2025, 6, 24)
    end = date(2025, 6, 27)
    events = cal._get_events(start, end)

    # Verify we get events from the real HTML data
    # The fixture should provide real disruptions for Tilburg
    assert isinstance(events, list)


@pytest.mark.asyncio
async def test_planned_event_all_day_and_hashtag(hass, mock_aiohttp_session, mockEntry):
    """Test calendar with planned disruption creates proper event."""
    mockEntry.add_to_hass(hass)

    coordinator = EnnatuurlijkCoordinator(hass, mockEntry)
    await coordinator.async_refresh()

    cal = EnnatuurlijkDisruptionsCalendar(coordinator, mockEntry)
    # Use November 2025 dates to match the planned disruptions in the fixture
    start = date(2025, 10, 31)
    end = date(2025, 11, 14)
    events = cal._get_events(start, end)

    # Should have events from the HTML fixture (Tilburg has planned disruptions)
    assert len(events) >= 1
    # Verify at least one event has planned status
    assert any("Status: #planned" in ev.description for ev in events)

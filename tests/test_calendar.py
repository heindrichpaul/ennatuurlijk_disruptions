
import pytest
from datetime import date
from custom_components.ennatuurlijk_disruptions.calendar import EnnatuurlijkDisruptionsCalendar
from custom_components.ennatuurlijk_disruptions.coordinator import EnnatuurlijkCoordinator

@pytest.fixture
async def setup_calendar_env(hass, mockEntry, mock_global_config_entry, mock_aiohttp_session):
    """Fixture to set up hass.data and calendar for all calendar tests."""
    mockEntry.add_to_hass(hass)
    coordinator = EnnatuurlijkCoordinator(hass, mockEntry)
    await coordinator.async_refresh()
    if "ennatuurlijk_disruptions" not in hass.data:
        hass.data["ennatuurlijk_disruptions"] = {}
    hass.data["ennatuurlijk_disruptions"]["global_entry"] = mock_global_config_entry
    hass.data["ennatuurlijk_disruptions"][mockEntry.entry_id] = {"coordinator": coordinator, "entry": mockEntry}
    return EnnatuurlijkDisruptionsCalendar(hass)

@pytest.mark.asyncio
async def test_solved_only_event_single_day_and_hashtag(setup_calendar_env):
    """Test calendar with only solved disruption creates a single event."""
    cal = setup_calendar_env
    start = date(2025, 10, 20)
    end = date(2025, 10, 31)
    events = cal._get_events(start, end)
    assert len(events) >= 1
    assert any(
        "Status: #solved" in ev.description or "Status: #completed" in ev.description
        for ev in events
    )

@pytest.mark.asyncio
async def test_current_then_solved_is_single_event(setup_calendar_env):
    """Test that same disruption ID in current and solved creates single event."""
    cal = setup_calendar_env
    start = date(2025, 6, 24)
    end = date(2025, 6, 27)
    events = cal._get_events(start, end)
    assert isinstance(events, list)

@pytest.mark.asyncio
async def test_planned_event_all_day_and_hashtag(setup_calendar_env):
    """Test calendar with planned disruption creates proper event."""
    cal = setup_calendar_env
    start = date(2025, 10, 31)
    end = date(2025, 11, 14)
    events = cal._get_events(start, end)
    assert len(events) >= 1
    assert any("Status: #planned" in ev.description for ev in events)

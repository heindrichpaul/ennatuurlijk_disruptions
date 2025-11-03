"""Direct tests for migration logic in __init__.py."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import custom_components.ennatuurlijk_disruptions.__init__ as integration

@pytest.fixture
def hass():
    # Minimal mock HomeAssistant with config_entries
    hass = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    hass.config_entries.async_update_entry = MagicMock()
    hass.config_entries.flow.async_init = AsyncMock()
    return hass

@pytest.mark.asyncio
async def test_migrate_v1_global_entry(hass):
    entry = SimpleNamespace(
        version=1,
        data={"is_global": True},
        options={},
        unique_id=None,
        entry_id="test-global",
    )
    result = await integration.async_migrate_entry(hass, entry)
    assert result is True
    hass.config_entries.async_update_entry.assert_any_call(entry, unique_id="ennatuurlijk_global")
    hass.config_entries.async_update_entry.assert_any_call(entry, version=2, data=entry.data, options=entry.options)

@pytest.mark.asyncio
async def test_migrate_v1_subentry_with_existing_global(hass):
    global_entry = SimpleNamespace(unique_id="ennatuurlijk_global", version=2, data={}, options={})
    hass.config_entries.async_entries.return_value = [global_entry]
    entry = SimpleNamespace(
        version=1,
        data={"postal_code": "1234AB"},
        options={},
        unique_id=None,
        entry_id="test-sub",
    )
    result = await integration.async_migrate_entry(hass, entry)
    assert result is True
    hass.config_entries.async_update_entry.assert_any_call(entry, unique_id="1234AB")
    hass.config_entries.async_update_entry.assert_any_call(entry, version=2, data=entry.data, options=entry.options)

@pytest.mark.asyncio
async def test_migrate_v1_subentry_migrates_v1_global_first(hass):
    v1_global = SimpleNamespace(
        version=1,
        data={"is_global": True},
        options={},
        unique_id=None,
        entry_id="test-global",
    )
    entry = SimpleNamespace(
        version=1,
        data={"postal_code": "5678CD"},
        options={},
        unique_id=None,
        entry_id="test-sub",
    )
    # First call: no global, returns [entry, v1_global]
    hass.config_entries.async_entries.side_effect = [[], [v1_global], [SimpleNamespace(unique_id="ennatuurlijk_global")]]
    with patch.object(integration, "async_migrate_entry", wraps=integration.async_migrate_entry) as migrate_patch:
        result = await integration.async_migrate_entry(hass, entry)
        assert result is True
        assert migrate_patch.call_count >= 1
    hass.config_entries.async_update_entry.assert_any_call(entry, unique_id="5678CD")
    hass.config_entries.async_update_entry.assert_any_call(entry, version=2, data=entry.data, options=entry.options)

@pytest.mark.asyncio
async def test_migrate_v1_subentry_creates_global_if_missing(hass):
    entry = SimpleNamespace(
        version=1,
        data={"postal_code": "9999ZZ", "days_to_keep_solved": 5, "update_interval": 42},
        options={},
        unique_id=None,
        entry_id="test-sub",
    )
    hass.config_entries.async_entries.return_value = []
    with patch.object(hass.config_entries.flow, "async_init", AsyncMock()) as flow_init:
        result = await integration.async_migrate_entry(hass, entry)
        assert result is True
        flow_init.assert_awaited_once()
    hass.config_entries.async_update_entry.assert_any_call(entry, unique_id="9999ZZ")
    hass.config_entries.async_update_entry.assert_any_call(entry, version=2, data=entry.data, options=entry.options)

@pytest.mark.asyncio
async def test_migrate_entry_already_migrated(hass):
    entry = SimpleNamespace(
        version=2,
        data={},
        options={},
        unique_id="ennatuurlijk_global",
        entry_id="already-migrated",
    )
    result = await integration.async_migrate_entry(hass, entry)
    assert result is True
    hass.config_entries.async_update_entry.assert_not_called()

"""Tests for the config flow."""

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ennatuurlijk_disruptions.config_flow import (
    EnnatuurlijkOptionsFlowHandler,
)
from custom_components.ennatuurlijk_disruptions.const import (
    DOMAIN,
    CONF_TOWN,
    CONF_POSTAL_CODE,
    CONF_CREATE_ALERT_SENSORS,
    CONF_DAYS_TO_KEEP_SOLVED,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CREATE_ALERT_SENSORS,
    DEFAULT_DAYS_TO_KEEP_SOLVED,
    DEFAULT_UPDATE_INTERVAL,
)
import pytest


"""
Fixtures and helpers for config flow tests.
All helpers/fixtures are DRY and reusable across tests.
"""



@pytest.fixture
async def global_config_entry(hass):
    """Create a global config entry and return it."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: DEFAULT_DAYS_TO_KEEP_SOLVED,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
        },
    )
    return hass.config_entries.async_entries(DOMAIN)[0]

@pytest.fixture
async def subentry(hass, global_config_entry):
    """Create a subentry for tests."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Entry",
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    return hass.config_entries.async_entries(DOMAIN)[-1]


    # Helper for config flow steps
async def create_subentry(
    hass, name, town, postal_code, days=None, alert=None, interval=None
):
    user_input = {
        CONF_NAME: name,
        CONF_TOWN: town,
        CONF_POSTAL_CODE: postal_code,
    }
    if days is not None:
        user_input[CONF_DAYS_TO_KEEP_SOLVED] = days
    if alert is not None:
        user_input[CONF_CREATE_ALERT_SENSORS] = alert
    if interval is not None:
        user_input[CONF_UPDATE_INTERVAL] = interval
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input=user_input)

    # Helper for options flow
async def run_options_flow(hass, entry, days=None, alert=None, interval=None, user_input=None):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    if user_input is None:
        user_input = {}
        if days is not None:
            user_input[CONF_DAYS_TO_KEEP_SOLVED] = days
        if alert is not None:
            user_input[CONF_CREATE_ALERT_SENSORS] = alert
        if interval is not None:
            user_input[CONF_UPDATE_INTERVAL] = interval
    return await hass.config_entries.options.async_configure(result["flow_id"], user_input=user_input)


async def test_user_flow_success(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    # Create global config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    # Add subentry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "add_subentry"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "1012AB",
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_CREATE_ALERT_SENSORS: True,
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Disruptions"
    assert result["data"] == {
        CONF_NAME: "Test Disruptions",
        CONF_TOWN: "Amsterdam",
        CONF_POSTAL_CODE: "1012AB",
    }
    assert result["options"] == {
        CONF_DAYS_TO_KEEP_SOLVED: 7,
        CONF_CREATE_ALERT_SENSORS: True,
        CONF_UPDATE_INTERVAL: 15,
    }


@pytest.mark.parametrize(
    "postal_code,expected",
    [
        ("3011 AB", "3011AB"),
        ("3511ab", "3511AB"),
        ("1234ABC", None),  # Invalid
        ("1234AB", "1234AB"),
    ],
)
@pytest.mark.asyncio
async def test_user_flow_postal_code_normalization(
    hass, enable_custom_integrations, mock_requests_get, global_config_entry, postal_code, expected
):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: postal_code,
        },
    )
    if expected is None:
        assert result.get("type") == FlowResultType.FORM
        assert result.get("errors") == {"postal_code": "invalid_postal_code"}
    else:
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        assert result.get("data")[CONF_POSTAL_CODE] == expected


async def test_user_flow_default_values(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, global_config_entry
):
    # Create global config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_UPDATE_INTERVAL: 120,
        },
    )
    # Add subentry with only required fields
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Minimal Config",
            CONF_TOWN: "Breda",
            CONF_POSTAL_CODE: "4811AA",
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["options"] == {
        CONF_DAYS_TO_KEEP_SOLVED: DEFAULT_DAYS_TO_KEEP_SOLVED,
        CONF_CREATE_ALERT_SENSORS: DEFAULT_CREATE_ALERT_SENSORS,
        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
    }


@pytest.mark.parametrize(
    "days,alert,interval",
    [
        (14, False, 20),
        (7, True, 15),
        (30, False, 60),
    ],
)
@pytest.mark.asyncio
async def test_options_flow_init_form(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry, days, alert, interval
):
    """Test the options flow displays the form and completes with various values."""
    entry = subentry
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    # Complete the options flow
    result = await run_options_flow(hass, entry, days=days, alert=alert, interval=interval)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_DAYS_TO_KEEP_SOLVED: days,
        CONF_CREATE_ALERT_SENSORS: alert,
        CONF_UPDATE_INTERVAL: interval,
    }



@pytest.mark.parametrize(
    "days,alert,interval",
    [
        (14, False, 20),
        (21, True, 30),
    ],
)
@pytest.mark.asyncio
async def test_options_flow_update(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry, days, alert, interval
):
    """Test updating options via options flow with various values."""
    entry = subentry
    result = await run_options_flow(hass, entry, days=days, alert=alert, interval=interval)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_DAYS_TO_KEEP_SOLVED: days,
        CONF_CREATE_ALERT_SENSORS: alert,
        CONF_UPDATE_INTERVAL: interval,
    }



@pytest.mark.asyncio
async def test_options_flow_uses_defaults(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, global_config_entry
):
    """Test that options flow uses default values when fields are omitted."""
    entry = await create_subentry(hass, "Test Entry", "Tilburg", "5045AB")
    entry = hass.config_entries.async_entries(DOMAIN)[-1]
    result = await run_options_flow(hass, entry, user_input={})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DAYS_TO_KEEP_SOLVED] == DEFAULT_DAYS_TO_KEEP_SOLVED
    assert result["data"][CONF_CREATE_ALERT_SENSORS] == DEFAULT_CREATE_ALERT_SENSORS
    assert result["data"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL


async def test_reconfigure_flow_shows_form(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry
):
    """Test that reconfigure flow shows a form with existing values and completes."""
    entry = subentry

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "reconfigure"

    # Complete reconfigure flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Entry",
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_CREATE_ALERT_SENSORS: True,
            CONF_UPDATE_INTERVAL: 15,
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"


async def test_reconfigure_flow_updates_entry(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry
):
    """Test reconfigure flow successfully updates the config entry."""
    entry = subentry

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    # Update entry with new values
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Updated Name",
            CONF_TOWN: "Den Haag",
            CONF_POSTAL_CODE: "2511AB",
            CONF_DAYS_TO_KEEP_SOLVED: 10,
            CONF_CREATE_ALERT_SENSORS: False,
            CONF_UPDATE_INTERVAL: 25,
        },
    )

    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    # Verify entry updated
    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert updated_entry is not None
    assert updated_entry.data[CONF_NAME] == "Updated Name"
    assert updated_entry.data[CONF_TOWN] == "Den Haag"
    assert updated_entry.data[CONF_POSTAL_CODE] == "2511AB"
    assert updated_entry.options[CONF_DAYS_TO_KEEP_SOLVED] == 10
    assert updated_entry.options[CONF_CREATE_ALERT_SENSORS] is False
    assert updated_entry.options[CONF_UPDATE_INTERVAL] == 25


async def test_reconfigure_flow_invalid_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry
):
    """Test reconfigure flow validates postal code and completes with valid input."""
    entry = subentry

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    # Submit invalid postal code
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "INVALID",
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {"postal_code": "invalid_postal_code"}

    # Fix postal code and complete flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "1012AB",
        },
    )

    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"


async def test_reconfigure_flow_invalid_entry_id(
    hass: HomeAssistant, enable_custom_integrations
):
    """Test reconfigure flow aborts when entry_id doesn't exist."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": "non_existent_id",
        },
    )

    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "entry_not_found"


async def test_reconfigure_uses_defaults_for_options(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test reconfigure flow uses default values for missing optional fields."""
    # Create global config entry (only global settings)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: DEFAULT_DAYS_TO_KEEP_SOLVED,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
        },
    )
    # Add subentry (minimal, uses defaults)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Entry",
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    entry = hass.config_entries.async_entries(DOMAIN)[-1]

    # Reconfigure with only required fields (uses defaults)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test",
            CONF_TOWN: "Eindhoven",
            CONF_POSTAL_CODE: "5611AA",
        },
    )
    assert result.get("type") == FlowResultType.ABORT

    # Verify default values used for options
    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert updated_entry is not None
    assert (
        updated_entry.options[CONF_DAYS_TO_KEEP_SOLVED] == DEFAULT_DAYS_TO_KEEP_SOLVED
    )
    assert (
        updated_entry.options[CONF_CREATE_ALERT_SENSORS] == DEFAULT_CREATE_ALERT_SENSORS
    )
    assert updated_entry.options[CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL


async def test_options_handler_config_entry_property(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get, subentry
):
    """Test that OptionsFlowHandler config_entry property works correctly."""

    handler = EnnatuurlijkOptionsFlowHandler(subentry)
    assert handler.config_entry == subentry
    assert handler.config_entry.entry_id == subentry.entry_id





async def test_user_flow_duplicate_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that duplicate postal codes are rejected."""
    # Create global config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_UPDATE_INTERVAL: 120,
        },
    )
    # Add first subentry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "First Entry",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    # Try to add duplicate subentry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Duplicate Entry",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "already_configured"


async def test_reconfigure_flow_duplicate_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that reconfiguring to a duplicate postal code is rejected."""
    # Create global config entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_UPDATE_INTERVAL: 120,
        },
    )
    # Add first subentry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "First Entry",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    # Add second subentry (different postal code)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "add_subentry"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Second Entry",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: "3011AB",
        },
    )
    entry2 = hass.config_entries.async_entries(DOMAIN)[-1]
    assert entry2 is not None
    # Try to reconfigure second entry to use first entry's postal code
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry2.entry_id},
    )
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "reconfigure"
    # Try to change to duplicate postal code (should abort)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Second Entry",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "already_configured"

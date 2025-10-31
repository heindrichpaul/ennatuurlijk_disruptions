"""Tests for the config flow."""

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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


async def test_user_flow_success(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test successful user flow with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Submit valid data
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


async def test_user_flow_postal_code_with_space(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that postal codes with spaces are normalized."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: "3011 AB",  # Space in postal code
            CONF_DAYS_TO_KEEP_SOLVED: 5,
            CONF_CREATE_ALERT_SENSORS: False,
            CONF_UPDATE_INTERVAL: 10,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POSTAL_CODE] == "3011AB"  # Space removed


async def test_user_flow_postal_code_lowercase(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that lowercase postal codes are converted to uppercase."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Utrecht",
            CONF_POSTAL_CODE: "3511ab",  # Lowercase letters
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POSTAL_CODE] == "3511AB"  # Uppercase


async def test_user_flow_invalid_postal_code_too_many_letters(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test validation error for postal code with too many letters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "1234ABC",  # Too many letters
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"postal_code": "invalid_postal_code"}

    # Fix the postal code and complete the flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Disruptions",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "1234AB",  # Valid postal code
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POSTAL_CODE] == "1234AB"


async def test_user_flow_default_values(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that default values are used when optional fields are omitted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Only provide required fields
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


async def test_options_flow_init_form(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test the options flow displays the form and completes."""
    entry = await _create_entry(hass, mock_requests_get)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Complete the options flow
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 14,
            CONF_CREATE_ALERT_SENSORS: False,
            CONF_UPDATE_INTERVAL: 20,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_DAYS_TO_KEEP_SOLVED: 14,
        CONF_CREATE_ALERT_SENSORS: False,
        CONF_UPDATE_INTERVAL: 20,
    }


async def test_options_flow_update(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test updating options via options flow."""
    # Create a config entry with initial options
    entry = await _create_entry(hass, mock_requests_get)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    # Update options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_DAYS_TO_KEEP_SOLVED: 14,
            CONF_CREATE_ALERT_SENSORS: False,
            CONF_UPDATE_INTERVAL: 20,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_DAYS_TO_KEEP_SOLVED: 14,
        CONF_CREATE_ALERT_SENSORS: False,
        CONF_UPDATE_INTERVAL: 20,
    }


async def test_options_flow_uses_defaults(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that options flow uses default values when fields are omitted."""
    # Create entry with minimal setup (will use defaults)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Entry",
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    # Submit form without changing anything - defaults should be used
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DAYS_TO_KEEP_SOLVED] == DEFAULT_DAYS_TO_KEEP_SOLVED
    assert result["data"][CONF_CREATE_ALERT_SENSORS] == DEFAULT_CREATE_ALERT_SENSORS
    assert result["data"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL


async def test_reconfigure_flow_shows_form(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that reconfigure flow shows a form with existing values and completes."""
    # First create an entry
    entry = await _create_entry(hass, mock_requests_get)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Complete the reconfigure flow
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
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test reconfigure flow successfully updates the config entry."""
    entry = await _create_entry(hass, mock_requests_get)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    # Update with new values
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

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify entry was updated
    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert updated_entry.data[CONF_NAME] == "Updated Name"
    assert updated_entry.data[CONF_TOWN] == "Den Haag"
    assert updated_entry.data[CONF_POSTAL_CODE] == "2511AB"
    assert updated_entry.options[CONF_DAYS_TO_KEEP_SOLVED] == 10
    assert updated_entry.options[CONF_CREATE_ALERT_SENSORS] is False
    assert updated_entry.options[CONF_UPDATE_INTERVAL] == 25


async def test_reconfigure_flow_invalid_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test reconfigure flow validates postal code and completes with valid input."""
    entry = await _create_entry(hass, mock_requests_get)

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

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"postal_code": "invalid_postal_code"}

    # Fix the postal code and complete the flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "1012AB",
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"


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

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "entry_not_found"


async def test_reconfigure_uses_defaults_for_options(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test reconfigure flow uses default values for missing optional fields."""
    # Create entry with minimal setup (will use defaults)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Entry",
            CONF_TOWN: "Tilburg",
            CONF_POSTAL_CODE: "5045AB",
        },
    )
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )

    # Only provide required fields
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test",
            CONF_TOWN: "Eindhoven",
            CONF_POSTAL_CODE: "5611AA",
        },
    )

    assert result["type"] == FlowResultType.ABORT

    # Verify default values were used for options
    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert (
        updated_entry.options[CONF_DAYS_TO_KEEP_SOLVED] == DEFAULT_DAYS_TO_KEEP_SOLVED
    )
    assert (
        updated_entry.options[CONF_CREATE_ALERT_SENSORS] == DEFAULT_CREATE_ALERT_SENSORS
    )
    assert updated_entry.options[CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL


async def test_options_handler_config_entry_property(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that OptionsFlowHandler config_entry property works correctly."""
    from custom_components.ennatuurlijk_disruptions.config_flow import (
        EnnatuurlijkOptionsFlowHandler,
    )

    entry = await _create_entry(hass, mock_requests_get)
    handler = EnnatuurlijkOptionsFlowHandler(entry)

    assert handler.config_entry == entry
    assert handler.config_entry.entry_id == entry.entry_id


# Helper function to create a test config entry
async def _create_entry(hass: HomeAssistant, mock_requests_get):
    """Create a test config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

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

    entry_id = result["result"].entry_id
    return hass.config_entries.async_get_entry(entry_id)


async def test_user_flow_duplicate_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that duplicate postal codes are rejected."""
    # Create first entry
    await _create_entry(hass, mock_requests_get)
    
    # Try to create another entry with the same postal code
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    
    # Submit duplicate postal code - should abort
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Duplicate Entry",
            CONF_TOWN: "Amsterdam",
            CONF_POSTAL_CODE: "5045AB",  # Same as first entry
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_CREATE_ALERT_SENSORS: True,
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow_duplicate_postal_code(
    hass: HomeAssistant, enable_custom_integrations, mock_requests_get
):
    """Test that reconfiguring to a duplicate postal code is rejected."""
    # Create first entry
    await _create_entry(hass, mock_requests_get)
    
    # Create second entry with different postal code
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Second Entry",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: "3011AB",
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_CREATE_ALERT_SENSORS: True,
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    entry2 = result["result"]
    
    # Try to reconfigure second entry to use first entry's postal code
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry2.entry_id},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    
    # Try to change to duplicate postal code - should abort
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Second Entry",
            CONF_TOWN: "Rotterdam",
            CONF_POSTAL_CODE: "5045AB",  # Same as first entry
            CONF_DAYS_TO_KEEP_SOLVED: 7,
            CONF_CREATE_ALERT_SENSORS: True,
            CONF_UPDATE_INTERVAL: 15,
        },
    )
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"

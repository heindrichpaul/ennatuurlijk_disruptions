import logging
from homeassistant import config_entries # type: ignore
from homeassistant.const import CONF_NAME # type: ignore
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE
import voluptuous as vol
import re

_LOGGER = logging.getLogger(__name__)

class EnnatuurlijkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        _LOGGER.debug("Initializing EnnatuurlijkConfigFlow")
        super().__init__()

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Starting async_step_user with input: %s", user_input)
        errors = {}
        if user_input is not None:
            # Validate postal code format (e.g., 4105TK)
            postal_code = user_input[CONF_POSTAL_CODE]
            if not re.match(r'^\d{4}[A-Z]{2}$', postal_code):
                errors["postal_code"] = "invalid_postal_code"
                _LOGGER.warning("Invalid postal code format: %s", postal_code)
            if not errors:
                _LOGGER.info("Creating config entry for %s, %s", user_input[CONF_TOWN], user_input[CONF_POSTAL_CODE])
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOWN: user_input[CONF_TOWN],
                        CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE]
                    }
                )

        _LOGGER.debug("Showing config form")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Ennatuurlijk Disruptions"): str,
                vol.Required(CONF_TOWN): str,
                vol.Required(CONF_POSTAL_CODE): str
            }),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        _LOGGER.debug("Starting async_step_reconfigure with input: %s, context: %s", user_input, self.context)
        # Check if config_entry_id is available, fall back to context
        entry_id = self.context.get("entry_id") if "entry_id" in self.context else None
        if not entry_id:
            _LOGGER.error("No config_entry_id or entry_id available in context for reconfigure step")
            return self.async_abort(reason="entry_not_found")

        # Fetch the existing config entry
        config_entry = self.hass.config_entries.async_get_entry(entry_id)
        if config_entry is None:
            _LOGGER.error("No config entry found for reconfigure step, entry_id: %s", entry_id)
            return self.async_abort(reason="entry_not_found")

        errors = {}
        if user_input is not None:
            # Validate postal code format
            postal_code = user_input[CONF_POSTAL_CODE]
            if not re.match(r'^\d{4}[A-Z]{2}$', postal_code):
                errors["postal_code"] = "invalid_postal_code"
                _LOGGER.warning("Invalid postal code format during reconfigure: %s", postal_code)
            if not errors:
                _LOGGER.info("Updating config entry for %s, %s", user_input[CONF_TOWN], user_input[CONF_POSTAL_CODE])
                return self.async_update_reload_and_abort(
                    config_entry,
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOWN: user_input[CONF_TOWN],
                        CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE]
                    }
                )

        # Pre-fill form with existing values
        _LOGGER.debug("Showing reconfigure form with existing values: %s", config_entry.data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=config_entry.data.get(CONF_NAME, "Ennatuurlijk Disruptions")): str,
                vol.Required(CONF_TOWN, default=config_entry.data.get(CONF_TOWN)): str,
                vol.Required(CONF_POSTAL_CODE, default=config_entry.data.get(CONF_POSTAL_CODE)): str
            }),
            errors=errors
        )
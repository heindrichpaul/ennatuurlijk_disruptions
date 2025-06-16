#!/usr/bin/env python3
"""
Config flow component for Ennatuurlijk Disruptions
Author: Heindrich Paul
"""

from homeassistant import config_entries # type: ignore
from homeassistant.const import CONF_NAME # type: ignore
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE, _LOGGER, CONF_CREATE_ALERT_SENSORS,CONF_DAYS_TO_KEEP_SOLVED,DEFAULT_CREATE_ALERT_SENSORS,DEFAULT_DAYS_TO_KEEP_SOLVED
import voluptuous as vol
import re

class EnnatuurlijkOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._config_entry = config_entry  # Use private attribute, do not set config_entry directly

    @property
    def config_entry(self):
        # Provide a property for backward compatibility if needed
        return self._config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_DAYS_TO_KEEP_SOLVED: user_input.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED),
                    CONF_CREATE_ALERT_SENSORS: user_input.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)
                },
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_DAYS_TO_KEEP_SOLVED, default=self._config_entry.options.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED)): int,
                vol.Optional(CONF_CREATE_ALERT_SENSORS, default=self._config_entry.options.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)): bool
            }),
            errors=errors,
        )

class EnnatuurlijkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        _LOGGER.debug("Initializing EnnatuurlijkConfigFlow")
        super().__init__()

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Starting async_step_user with input: %s", user_input)
        errors = {}
        if user_input is not None:
            town = user_input[CONF_TOWN]
            postal_code = user_input[CONF_POSTAL_CODE].replace(" ", "").upper()
            # Accept both '1234AB' and '1234 AB' formats
            if not re.match(r'^\d{4}[A-Z]{2}$', postal_code):
                errors["postal_code"] = "invalid_postal_code"
                _LOGGER.warning("Invalid postal code format: %s", postal_code)
            if not errors:
                _LOGGER.info("Creating config entry for %s, %s", user_input[CONF_TOWN], user_input[CONF_POSTAL_CODE])
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOWN: town,
                        CONF_POSTAL_CODE: postal_code
                    },
                    options={
                        CONF_DAYS_TO_KEEP_SOLVED: user_input.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED),
                        CONF_CREATE_ALERT_SENSORS: user_input.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)
                    }
                )

        _LOGGER.debug("Showing config form")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Ennatuurlijk Disruptions"): str,
                vol.Required(CONF_TOWN): str,
                vol.Required(CONF_POSTAL_CODE): str,
                vol.Optional(CONF_DAYS_TO_KEEP_SOLVED, default=DEFAULT_DAYS_TO_KEEP_SOLVED): int,
                vol.Optional(CONF_CREATE_ALERT_SENSORS, default=DEFAULT_CREATE_ALERT_SENSORS): bool
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
                    },
                    options={
                        CONF_DAYS_TO_KEEP_SOLVED: user_input.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED),
                        CONF_CREATE_ALERT_SENSORS: user_input.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)
                    }
                )

        # Pre-fill form with existing values
        _LOGGER.debug("Showing reconfigure form with existing values: %s", config_entry.data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=config_entry.data.get(CONF_NAME, "Ennatuurlijk Disruptions")): str,
                vol.Required(CONF_TOWN, default=config_entry.data.get(CONF_TOWN)): str,
                vol.Required(CONF_POSTAL_CODE, default=config_entry.data.get(CONF_POSTAL_CODE)): str,
                vol.Optional(CONF_DAYS_TO_KEEP_SOLVED, default=config_entry.options.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED)): int,
                vol.Optional(CONF_CREATE_ALERT_SENSORS, default=config_entry.options.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)): bool
            }),
            errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EnnatuurlijkOptionsFlowHandler(config_entry)
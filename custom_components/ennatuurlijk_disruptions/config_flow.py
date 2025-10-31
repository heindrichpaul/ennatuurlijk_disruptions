#!/usr/bin/env python3
"""Config flow for Ennatuurlijk Disruptions integration."""

from homeassistant import config_entries  # type: ignore
from homeassistant.const import CONF_NAME  # type: ignore
from homeassistant.config_entries import ConfigFlow
from .const import (
    DOMAIN,
    CONF_TOWN,
    CONF_POSTAL_CODE,
    _LOGGER,
    CONF_CREATE_ALERT_SENSORS,
    CONF_DAYS_TO_KEEP_SOLVED,
    DEFAULT_CREATE_ALERT_SENSORS,
    DEFAULT_DAYS_TO_KEEP_SOLVED,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
import voluptuous as vol
import re


class EnnatuurlijkOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._config_entry = (
            config_entry  # Use private attribute, do not set config_entry directly
        )

    @property
    def config_entry(self):
    # Property for backward compatibility
        return self._config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_DAYS_TO_KEEP_SOLVED: user_input.get(
                        CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                    ),
                    CONF_CREATE_ALERT_SENSORS: user_input.get(
                        CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
                    ),
                    CONF_UPDATE_INTERVAL: user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                },
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DAYS_TO_KEEP_SOLVED,
                        default=self._config_entry.options.get(
                            CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                        ),
                    ): int,
                    vol.Optional(
                        CONF_CREATE_ALERT_SENSORS,
                        default=self._config_entry.options.get(
                            CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): int,
                }
            ),
            errors=errors,
        )



class EnnatuurlijkConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self):
        _LOGGER.debug("Initializing EnnatuurlijkConfigFlow (global+subentry)")
        super().__init__()
        self._global_entry = None

    async def async_step_user(self, user_input=None):
    # Global config entry step
        errors = {}
        if user_input is not None:
            # Only one global config entry allowed
            await self.async_set_unique_id("ennatuurlijk_global")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Ennatuurlijk Disruptions (Global Settings)",
                data={
                    CONF_DAYS_TO_KEEP_SOLVED: user_input.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED),
                    CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                },
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DAYS_TO_KEEP_SOLVED, default=DEFAULT_DAYS_TO_KEEP_SOLVED): int,
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
                }
            ),
            errors=errors,
        )

    async def async_step_add_subentry(self, user_input=None):
    # Subentry step (postal code/town)
        errors = {}
        if user_input is not None:
            town = user_input[CONF_TOWN]
            postal_code = user_input[CONF_POSTAL_CODE].replace(" ", "").upper()
            name = user_input.get(CONF_NAME, f"Ennatuurlijk Disruptions {town}")
            days_to_keep_solved = user_input.get(CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED)
            create_alert_sensors = user_input.get(CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS)
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            if not re.match(r"^\d{4}[A-Z]{2}$", postal_code):
                errors["postal_code"] = "invalid_postal_code"
            if not errors:
                await self.async_set_unique_id(postal_code)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_TOWN: town,
                        CONF_POSTAL_CODE: postal_code,
                    },
                    options={
                        CONF_DAYS_TO_KEEP_SOLVED: days_to_keep_solved,
                        CONF_CREATE_ALERT_SENSORS: create_alert_sensors,
                        CONF_UPDATE_INTERVAL: update_interval,
                    },
                )
        return self.async_show_form(
            step_id="add_subentry",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Ennatuurlijk Disruptions"): str,
                    vol.Required(CONF_TOWN): str,
                    vol.Required(CONF_POSTAL_CODE): str,
                    vol.Optional(CONF_DAYS_TO_KEEP_SOLVED, default=DEFAULT_DAYS_TO_KEEP_SOLVED): int,
                    vol.Optional(CONF_CREATE_ALERT_SENSORS, default=DEFAULT_CREATE_ALERT_SENSORS): bool,
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
                }
            ),
            errors=errors,
        )


    async def async_step_reconfigure(self, user_input=None):
        _LOGGER.debug(
            "Starting async_step_reconfigure with input: %s, context: %s",
            user_input,
            self.context,
        )
    # Get config_entry_id from context
        entry_id = self.context.get("entry_id") if "entry_id" in self.context else None
        if not entry_id:
            _LOGGER.error(
                "No config_entry_id or entry_id available in context for reconfigure step"
            )
            return self.async_abort(reason="entry_not_found")

    # Fetch the config entry
        config_entry = self.hass.config_entries.async_get_entry(entry_id)
        if config_entry is None:
            _LOGGER.error(
                "No config entry found for reconfigure step, entry_id: %s", entry_id
            )
            return self.async_abort(reason="entry_not_found")

        errors = {}
        if user_input is not None:
            # Validate postal code
            postal_code = user_input[CONF_POSTAL_CODE]
            if not re.match(r"^\d{4}[A-Z]{2}$", postal_code):
                errors["postal_code"] = "invalid_postal_code"
                _LOGGER.warning(
                    "Invalid postal code format during reconfigure: %s", postal_code
                )

            if not errors:
                # Check for duplicate postal code
                if postal_code != config_entry.data.get(CONF_POSTAL_CODE):
                    await self.async_set_unique_id(postal_code)
                    self._abort_if_unique_id_configured()

                _LOGGER.info(
                    "Updating config entry for %s, %s",
                    user_input[CONF_TOWN],
                    user_input[CONF_POSTAL_CODE],
                )
                # Update unique_id if postal code changed
                self.hass.config_entries.async_update_entry(
                    config_entry, unique_id=postal_code
                )

                return self.async_update_reload_and_abort(
                    config_entry,
                    reason="reconfigure_successful",
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOWN: user_input[CONF_TOWN],
                        CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE],
                    },
                    options={
                        CONF_DAYS_TO_KEEP_SOLVED: user_input.get(
                            CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                        ),
                        CONF_CREATE_ALERT_SENSORS: user_input.get(
                            CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
                        ),
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    },
                )

    # Pre-fill form with current values
        _LOGGER.debug(
            "Showing reconfigure form with existing values: %s", config_entry.data
        )
    return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=config_entry.data.get(
                            CONF_NAME, "Ennatuurlijk Disruptions"
                        ),
                    ): str,
                    vol.Required(
                        CONF_TOWN, default=config_entry.data.get(CONF_TOWN)
                    ): str,
                    vol.Required(
                        CONF_POSTAL_CODE,
                        default=config_entry.data.get(CONF_POSTAL_CODE),
                    ): str,
                    vol.Optional(
                        CONF_DAYS_TO_KEEP_SOLVED,
                        default=config_entry.options.get(
                            CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                        ),
                    ): int,
                    vol.Optional(
                        CONF_CREATE_ALERT_SENSORS,
                        default=config_entry.options.get(
                            CONF_CREATE_ALERT_SENSORS, DEFAULT_CREATE_ALERT_SENSORS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
    return EnnatuurlijkOptionsFlowHandler(config_entry)

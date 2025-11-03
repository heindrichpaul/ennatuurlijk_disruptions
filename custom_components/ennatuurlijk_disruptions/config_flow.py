#!/usr/bin/env python3
"""Config flow for Ennatuurlijk Disruptions integration."""

from homeassistant import config_entries  # type: ignore
from homeassistant.const import CONF_NAME  # type: ignore
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
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
from .utils import PostalCodeValidator, SchemaHelper
import voluptuous as vol


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
                SchemaHelper.get_common_options(self._config_entry.options)
            ),
            errors=errors,
        )


class EnnatuurlijkConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def _is_duplicate_postal_code(
        self, postal_code: str, exclude_entry_id: "str | None" = None
    ) -> bool:
        """Check if an entry with this postal code already exists, excluding a given entry_id if provided."""
        for entry in self._async_current_entries():
            if exclude_entry_id and entry.entry_id == exclude_entry_id:
                continue
            if entry.unique_id == postal_code:
                return True
        return False

    def __init__(self):
        _LOGGER.debug("Initializing EnnatuurlijkConfigFlow")
        super().__init__()

    async def async_step_user(self, user_input=None):
        """Handle user step: create main integration entry."""
        # Check if main entry already exists
        for entry in self._async_current_entries():
            if not entry.data.get("postal_code"):  # Main entry has no postal_code
                return self.async_abort(reason="already_configured")

        errors = {}
        if user_input is not None:
            # Create main integration entry with common options
            return self.async_create_entry(
                title="Ennatuurlijk Disruptions",
                data={"name": "Ennatuurlijk Disruptions"},
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

        # Show form for common options
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(SchemaHelper.get_common_options()),
            errors=errors,
        )

    async def async_step_migration(self, user_input=None):
        """Handle migration step for creating main entry from existing data."""
        if user_input is None:
            # Use defaults for migration
            user_input = {
                CONF_DAYS_TO_KEEP_SOLVED: DEFAULT_DAYS_TO_KEEP_SOLVED,
                CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            }

        # Create main integration entry for migration scenario
        return self.async_create_entry(
            title="Ennatuurlijk Disruptions",
            data={"name": "Ennatuurlijk Disruptions"},
            options={
                CONF_DAYS_TO_KEEP_SOLVED: user_input.get(
                    CONF_DAYS_TO_KEEP_SOLVED, DEFAULT_DAYS_TO_KEEP_SOLVED
                ),
                CONF_UPDATE_INTERVAL: user_input.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                ),
            },
        )

    async def async_step_add_subentry(self, user_input=None):
        """Handle adding a subentry (location)."""
        _LOGGER.debug("Starting async_step_add_subentry with input: %s", user_input)

        if user_input is not None:
            # Validate postal code
            postal_code, is_valid = PostalCodeValidator.validate_and_normalize(
                user_input.get(CONF_POSTAL_CODE, "")
            )

            if not is_valid:
                return self.async_show_form(
                    step_id="add_subentry",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_NAME): str,
                            vol.Required(CONF_TOWN): str,
                            vol.Required(CONF_POSTAL_CODE): str,
                            **SchemaHelper.get_common_options(),
                        }
                    ),
                    errors={"postal_code": "invalid_postal_code"},
                )

            # Check for duplicate postal code
            for existing_entry in self.hass.config_entries.async_entries(DOMAIN):
                if existing_entry.unique_id == postal_code:
                    return self.async_abort(reason="already_configured")

            # Create subentry
            await self.async_set_unique_id(postal_code)
            return self.async_create_entry(
                title=f"{user_input[CONF_TOWN]} - {postal_code}",
                data={
                    "name": user_input[CONF_NAME],
                    "town": user_input[CONF_TOWN],
                    "postal_code": postal_code,
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

        return self.async_show_form(
            step_id="add_subentry",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_TOWN): str,
                    vol.Required(CONF_POSTAL_CODE): str,
                    **SchemaHelper.get_common_options(),
                }
            ),
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        """Return subentries supported by this integration."""
        return {"location": LocationSubentryFlowHandler}

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
            # Validate and normalize postal code
            postal_code, is_valid = PostalCodeValidator.validate_and_normalize(
                user_input[CONF_POSTAL_CODE]
            )
            if not is_valid:
                errors["postal_code"] = "invalid_postal_code"
                _LOGGER.warning(
                    "Invalid postal code format during reconfigure: %s", postal_code
                )

            if not errors:
                # Check for duplicate postal code among other entries (exclude self)
                if self._is_duplicate_postal_code(
                    postal_code, exclude_entry_id=config_entry.entry_id
                ):
                    return self.async_abort(reason="already_configured")

                # Update unique_id if postal code changed
                if postal_code != config_entry.data.get(CONF_POSTAL_CODE):
                    await self.async_set_unique_id(postal_code)

                _LOGGER.info(
                    "Updating config entry for %s, %s",
                    user_input[CONF_TOWN],
                    user_input[CONF_POSTAL_CODE],
                )
                self.hass.config_entries.async_update_entry(
                    config_entry, unique_id=postal_code
                )

                return self.async_update_reload_and_abort(
                    config_entry,
                    reason="reconfigure_successful",
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TOWN: user_input[CONF_TOWN],
                        CONF_POSTAL_CODE: postal_code,
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

        # Build complete schema
        schema_dict = {
            vol.Required(
                CONF_NAME,
                default=config_entry.data.get(CONF_NAME, "Ennatuurlijk Disruptions"),
            ): str,
            vol.Required(CONF_TOWN, default=config_entry.data.get(CONF_TOWN)): str,
            vol.Required(
                CONF_POSTAL_CODE,
                default=config_entry.data.get(CONF_POSTAL_CODE),
            ): str,
            **SchemaHelper.get_common_options(config_entry.options),
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EnnatuurlijkOptionsFlowHandler(config_entry)


class LocationSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying locations."""

    def _is_duplicate_postal_code(self, postal_code: str) -> bool:
        """Check if a subentry with this postal code already exists."""
        main_entry = self._get_entry()
        for subentry in main_entry.subentries.values():
            if subentry.unique_id == postal_code:
                return True
        return False

    async def async_step_user(self, user_input=None) -> SubentryFlowResult:
        """Add a new location subentry."""
        errors = {}

        if user_input is not None:
            town = user_input[CONF_TOWN]
            postal_code, is_valid = PostalCodeValidator.validate_and_normalize(
                user_input[CONF_POSTAL_CODE]
            )
            name = user_input.get(CONF_NAME, f"Ennatuurlijk Disruptions {town}")

            if not is_valid:
                errors["postal_code"] = "invalid_postal_code"

            if not errors and self._is_duplicate_postal_code(postal_code):
                return self.async_abort(reason="already_configured")

            if not errors:
                return self.async_create_entry(
                    title=f"{town} {postal_code}",
                    data={
                        CONF_NAME: name,
                        CONF_TOWN: town,
                        CONF_POSTAL_CODE: postal_code,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Ennatuurlijk Disruptions"): str,
                    vol.Required(CONF_TOWN): str,
                    vol.Required(CONF_POSTAL_CODE): str,
                }
            ),
            errors=errors,
        )

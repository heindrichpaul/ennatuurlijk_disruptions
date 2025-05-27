from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN, CONF_TOWN, CONF_POSTAL_CODE
import voluptuous as vol

class EnnatuurlijkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_TOWN: user_input[CONF_TOWN],
                    CONF_POSTAL_CODE: user_input[CONF_POSTAL_CODE]
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Ennatuurlijk Disruptions"): str,
                vol.Required(CONF_TOWN): str,
                vol.Required(CONF_POSTAL_CODE): str
            })
        )
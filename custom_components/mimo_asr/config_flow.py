"""Config flow for MIMO ASR integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import openai

from .const import DOMAIN, CONF_BASE_URL, DEFAULT_BASE_URL, CONF_LANGUAGE, DEFAULT_LANGUAGE

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): str,
    vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(["auto", "zh", "en"]),
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    try:
        client = openai.AsyncOpenAI(
            api_key=data[CONF_API_KEY],
            base_url=data[CONF_BASE_URL]
        )
        # 测试连接
        await client.models.list()
        return {"title": "MIMO ASR"}
    except Exception as err:
        raise InvalidAuth from err

class MimoAsrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MIMO ASR."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""

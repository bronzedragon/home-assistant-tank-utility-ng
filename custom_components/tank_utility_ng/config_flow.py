from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.helpers import selector
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed
from .const import DOMAIN, CONF_DEVICES

_LOGGER = logging.getLogger(__name__)

class TankUtilityNGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return TankUtilityNGOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                from .api import TankUtilityClient
                client = TankUtilityClient(self.hass, user_input)
                token = await client.async_authenticate()
                _LOGGER.debug("Authenticated successfully (token length=%s).", len(token) if token else None)
                user_input[CONF_DEVICES] = await client.async_list_devices()
                _LOGGER.debug("Discovered devices: %s", user_input[CONF_DEVICES])
            except ConfigEntryAuthFailed as err:
                _LOGGER.warning("Auth failed: %s", err)
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.exception("Connection/setup failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"tank_utility_ng_{user_input[CONF_EMAIL]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Tank Utility NG", data=user_input)
        schema = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input):
        await self.async_set_unique_id(f"tank_utility_ng_{user_input[CONF_EMAIL]}")
        self._abort_if_unique_id_configured()
        if CONF_DEVICES not in user_input:
            from .api import TankUtilityClient
            client = TankUtilityClient(self.hass, user_input)
            await client.async_authenticate()
            user_input[CONF_DEVICES] = await client.async_list_devices()
        return self.async_create_entry(title="Tank Utility (Migrated)", data=user_input)

class TankUtilityNGOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        from .const import (
            CONF_TEMP_UNIT_MODE, CONF_CAPACITY_UNIT_MODE, CONF_REFILL_PERCENT_THRESHOLD,
            CONF_REFILL_GALLON_MIN, CONF_UPDATE_INTERVAL_HOURS, DEFAULT_TEMP_UNIT_MODE,
            DEFAULT_CAPACITY_UNIT_MODE, DEFAULT_REFILL_PERCENT_THRESHOLD,
            DEFAULT_REFILL_GALLON_MIN, DEFAULT_UPDATE_INTERVAL_HOURS,
        )
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        opts = self.config_entry.options
        schema = vol.Schema({
            vol.Required(CONF_UPDATE_INTERVAL_HOURS, default=opts.get(CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS)): selector.NumberSelector(selector.NumberSelectorConfig(min=1,max=24,step=1,mode=selector.NumberSelectorMode.BOX,unit_of_measurement="h")),
            vol.Required(CONF_TEMP_UNIT_MODE, default=opts.get(CONF_TEMP_UNIT_MODE, DEFAULT_TEMP_UNIT_MODE)): selector.SelectSelector(selector.SelectSelectorConfig(options=[selector.SelectOptionDict(value="auto",label="Auto"),selector.SelectOptionDict(value="C",label="°C"),selector.SelectOptionDict(value="F",label="°F")],mode=selector.SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_CAPACITY_UNIT_MODE, default=opts.get(CONF_CAPACITY_UNIT_MODE, DEFAULT_CAPACITY_UNIT_MODE)): selector.SelectSelector(selector.SelectSelectorConfig(options=[selector.SelectOptionDict(value="auto",label="Auto"),selector.SelectOptionDict(value="gal",label="Gallons"),selector.SelectOptionDict(value="L",label="Liters")],mode=selector.SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_REFILL_PERCENT_THRESHOLD, default=opts.get(CONF_REFILL_PERCENT_THRESHOLD, DEFAULT_REFILL_PERCENT_THRESHOLD)): selector.NumberSelector(selector.NumberSelectorConfig(min=0.0,max=100.0,step=0.5,mode=selector.NumberSelectorMode.BOX,unit_of_measurement="%")),
            vol.Required(CONF_REFILL_GALLON_MIN, default=opts.get(CONF_REFILL_GALLON_MIN, DEFAULT_REFILL_GALLON_MIN)): selector.NumberSelector(selector.NumberSelectorConfig(min=0.0,max=5000.0,step=1.0,mode=selector.NumberSelectorMode.BOX,unit_of_measurement="gal")),
        })
        return self.async_show_form(step_id="init", data_schema=schema)

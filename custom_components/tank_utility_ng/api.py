from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_BASE, ENDPOINT_TOKEN, ENDPOINT_DEVICES

_LOGGER = logging.getLogger(__name__)

def _maybe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None

class TankUtilityClient:
    def __init__(self, hass, data: dict[str, Any]):
        self.hass = hass
        self.email = data.get("email")
        self.password = data.get("password")
        self._token: str | None = data.get("token")
        self._session = async_get_clientsession(hass)

    async def async_authenticate(self) -> str:
        auth = aiohttp.BasicAuth(self.email, self.password)
        url = f"{API_BASE}{ENDPOINT_TOKEN}"
        _LOGGER.debug("Requesting token from %s", url)

        async with self._session.get(url, auth=auth) as resp:
            body_text = await resp.text()
            _LOGGER.debug(
                "Token response status=%s content_type=%s body_prefix=%s",
                resp.status,
                resp.content_type,
                body_text[:80],
            )

            if resp.status in (401, 403):
                raise ConfigEntryAuthFailed("Invalid credentials")
            resp.raise_for_status()

            js = _maybe_json(body_text)
            if isinstance(js, dict) and js.get("token"):
                self._token = js["token"]
                return self._token

            token = body_text.strip().strip('"').strip("'")
            if not token:
                raise RuntimeError("No token in response")
            self._token = token
            return token

    async def _ensure_token(self) -> str:
        if self._token:
            return self._token
        return await self.async_authenticate()

    async def async_list_devices(self) -> list[str]:
        token = await self._ensure_token()
        url = f"{API_BASE}{ENDPOINT_DEVICES}?token={token}"
        _LOGGER.debug("Listing devices from %s", url)

        async with self._session.get(url) as resp:
            body_text = await resp.text()
            _LOGGER.debug(
                "Devices response status=%s content_type=%s body_prefix=%s",
                resp.status,
                resp.content_type,
                body_text[:120],
            )

            if resp.status in (401, 403):
                self._token = None
                raise ConfigEntryAuthFailed("Token expired")
            resp.raise_for_status()

            js = _maybe_json(body_text)
            if isinstance(js, list):
                return [str(x) for x in js]

            if isinstance(js, dict):
                devices = js.get("devices") or js.get("deviceIds") or []
                if isinstance(devices, list):
                    return [str(x) for x in devices]

            raise RuntimeError("Unexpected devices response format")

    async def async_get_device(self, device_id: str) -> dict[str, Any]:
        token = await self._ensure_token()
        url = f"{API_BASE}{ENDPOINT_DEVICES}/{device_id}?token={token}"
        _LOGGER.debug("Fetching device %s from %s", device_id, url)

        async with self._session.get(url) as resp:
            body_text = await resp.text()
            _LOGGER.debug(
                "Device response status=%s content_type=%s body_prefix=%s",
                resp.status,
                resp.content_type,
                body_text[:120],
            )

            if resp.status in (401, 403):
                self._token = None
                raise ConfigEntryAuthFailed("Token expired")
            resp.raise_for_status()

            # TankUtility sometimes returns JSON with content-type text/plain.
            js = _maybe_json(body_text)
            if isinstance(js, dict):
                return js

            raise RuntimeError("Unexpected device response format")

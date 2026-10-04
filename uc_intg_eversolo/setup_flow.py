"""
Eversolo setup flow.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloSetupFlow(BaseSetupFlow[EversoloConfig]):
    """Single-screen setup. Problems are shown on the form with the typed values kept;
    Update starts from the saved values and keeps the device ID (entity IDs stay)."""

    def get_manual_entry_form(self, error: str = "", values: dict[str, Any] | None = None) -> RequestUserInput:
        saved = self.selected_config_entry
        values = values or {}

        def pick(key: str, default: Any) -> Any:
            if values.get(key) not in (None, ""):
                return values[key]
            return getattr(saved, key, default) if saved else default

        problem = [{
            "id": "error",
            "label": {"en": "Problem"},
            "field": {"label": {"value": {"en": error}}},
        }] if error else []
        return RequestUserInput(
            {"en": "Eversolo Setup"},
            problem + [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": str(pick("name", ""))}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": str(pick("host", ""))}},
                },
                {
                    "id": "port",
                    "label": {"en": "Port"},
                    "field": {"text": {"value": str(pick("port", "9529"))}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> EversoloConfig | RequestUserInput:
        saved = self.selected_config_entry
        host = "".join(str(input_values.get("host") or "").split())
        name = str(input_values.get("name") or "").strip()
        values = {**input_values, "host": host, "name": name}
        if not host:
            return self.get_manual_entry_form("Enter the Eversolo's IP address.", values)
        try:
            port = int(str(input_values.get("port") or 9529).strip())
        except ValueError:
            return self.get_manual_entry_form("The port must be a number (default 9529).", values)

        # Updating keeps the device ID so entity IDs and activities stay intact.
        identifier = saved.identifier if saved else f"eversolo_{host.replace('.', '_')}_{port}"
        test_config = EversoloConfig(identifier=identifier, name=name, host=host, port=port, model="DMP-A6")
        test_device = EversoloDevice(test_config)
        _LOG.info("Testing connection to %s:%s", host, port)
        try:
            # A real request: connect() itself never fails (the device may simply be off).
            music_state = await asyncio.wait_for(
                test_device._api_request("/ZidooMusicControl/v2/getState", timeout=8.0), timeout=10.0
            )
            model_info = await test_device.get_device_model()
            test_device._model_info = model_info or {}
            detected_model = test_device.model_name or "DMP-A6"
            mac = None
            if isinstance(music_state, dict):
                mac = (music_state.get("deviceInfo") or {}).get("net_mac")
            if not mac and isinstance(model_info, dict):
                mac = model_info.get("net_mac")
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.info("Setup test of %s:%s failed: %s", host, port, err)
            return self.get_manual_entry_form(
                f"No answer from an Eversolo at {host}:{port}. Check the IP address and that the "
                "Eversolo is switched on and on the same network as the Remote.",
                values,
            )
        finally:
            try:
                await test_device.close_connection()
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        _LOG.info("Detected model: %s", detected_model)
        final_config = EversoloConfig(
            identifier=identifier,
            name=name or f"Eversolo {detected_model}",
            host=host,
            port=port,
            model=detected_model,
            mac_address=mac or (saved.mac_address if saved else None),
        )
        _LOG.info("Setup complete: %s:%s (Model: %s)", host, port, detected_model)
        return final_config

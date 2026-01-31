"""
Eversolo setup flow for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloSetupFlow(BaseSetupFlow[EversoloConfig]):
    """Setup flow for Eversolo integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        """Define manual entry fields."""
        return RequestUserInput(
            {"en": "Eversolo Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "port",
                    "label": {"en": "Port"},
                    "field": {"text": {"value": "9529"}},
                },
                {
                    "id": "model",
                    "label": {"en": "Device Model"},
                    "field": {
                        "dropdown": {
                            "value": "DMP-A6",
                            "items": [
                                {
                                    "id": "DMP-A6",
                                    "label": {"en": "DMP-A6 (Music Streamer with HDMI & Knob)"}
                                },
                                {
                                    "id": "DMP-A10",
                                    "label": {"en": "DMP-A10 (DAC/Preamp - No HDMI/Knob)"}
                                },
                            ],
                        }
                    },
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> EversoloConfig | RequestUserInput:
        """
        Validate connection and create config.
        Called after user provides info.
        """
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("IP address is required")

        port = int(input_values.get("port", 9529))
        name = input_values.get("name", f"Eversolo ({host})").strip()
        model = input_values.get("model", "DMP-A6")

        try:
            test_config = EversoloConfig(
                identifier=f"eversolo_{host.replace('.', '_')}_{port}",
                name=name,
                host=host,
                port=port,
                model=model,
            )

            _LOG.info("Testing connection to %s:%s", host, port)

            test_device = EversoloDevice(test_config)
            connected = await asyncio.wait_for(test_device.connect(), timeout=10.0)
            await test_device.disconnect()

            if not connected:
                raise ValueError(f"Failed to connect to {host}:{port}")

            _LOG.info("Successfully validated connection to %s:%s", host, port)
            return test_config

        except asyncio.TimeoutError:
            raise ValueError(
                f"Connection timeout to {host}:{port}\n"
                "Please verify device is powered on and accessible"
            ) from None
        except Exception as err:
            raise ValueError(f"Setup failed: {err}") from err

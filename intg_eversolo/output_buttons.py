"""
Eversolo Output Selection Button entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.button import Button

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloOutputButton(Button):
    """Button entity for selecting a specific output."""

    def __init__(
        self,
        device_config: EversoloConfig,
        device: EversoloDevice,
        output_tag: str,
        output_name: str,
    ):
        """Initialize output button."""
        self._device = device
        self._output_tag = output_tag
        self._output_name = output_name

        entity_id = f"button.{device_config.identifier}_output_{output_tag}"
        entity_name = f"{device_config.name} Output: {output_name}"

        super().__init__(
            entity_id,
            entity_name,
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: Button, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle button press command."""
        _LOG.info("[%s] Selecting output: %s", self.id, self._output_name)

        try:
            # Check if this output is available on the device
            if self._output_name not in self._device.outputs.values():
                _LOG.warning(
                    "[%s] Output '%s' not available on this device (available: %s)",
                    self.id,
                    self._output_name,
                    list(self._device.outputs.values()),
                )
                return StatusCodes.NOT_IMPLEMENTED

            success = await self._device.select_output(self._output_name)
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
        except Exception as err:
            _LOG.error("[%s] Output selection error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

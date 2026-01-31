"""
Eversolo Select entities for VU and Spectrum mode selection.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, Select, States

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloVUModeSelect(Select):
    """VU Meter mode selector."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize VU mode selector."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}.vu_mode"

        super().__init__(
            entity_id,
            f"{device_config.name} VU Mode",
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.CURRENT_OPTION: "",
                Attributes.OPTIONS: [],
            },
            cmd_handler=self.handle_command,
        )

        # Note: Options will be populated when device provides mode list
        # For now, entity will work with empty options until implemented

    async def _update_options(self):
        """Fetch VU mode options from device."""
        try:
            modes = await self._device.get_vu_modes()
            if modes:
                options = [mode.get("name", f"Mode {i}") for i, mode in enumerate(modes)]
                self.attributes[Attributes.OPTIONS] = options
                self.attributes[Attributes.STATE] = States.ON
        except Exception as err:
            _LOG.error("[%s] Failed to fetch VU modes: %s", self.id, err)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.SELECT:
                if params and "option" in params:
                    option = params["option"]
                    # Find index of selected option
                    options = self.attributes.get(Attributes.OPTIONS, [])
                    if option in options:
                        index = options.index(option)
                        success = await self._device.set_vu_mode(index)
                        if success:
                            self.attributes[Attributes.CURRENT_OPTION] = option
                        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                    return StatusCodes.BAD_REQUEST
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR


class EversoloSpectrumModeSelect(Select):
    """Spectrum Analyzer mode selector."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize spectrum mode selector."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}.spectrum_mode"

        super().__init__(
            entity_id,
            f"{device_config.name} Spectrum Mode",
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.CURRENT_OPTION: "",
                Attributes.OPTIONS: [],
            },
            cmd_handler=self.handle_command,
        )

        # Note: Options will be populated when device provides mode list
        # For now, entity will work with empty options until implemented

    async def _update_options(self):
        """Fetch spectrum mode options from device."""
        try:
            modes = await self._device.get_spectrum_modes()
            if modes:
                options = [mode.get("name", f"Mode {i}") for i, mode in enumerate(modes)]
                self.attributes[Attributes.OPTIONS] = options
                self.attributes[Attributes.STATE] = States.ON
        except Exception as err:
            _LOG.error("[%s] Failed to fetch spectrum modes: %s", self.id, err)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.SELECT:
                if params and "option" in params:
                    option = params["option"]
                    # Find index of selected option
                    options = self.attributes.get(Attributes.OPTIONS, [])
                    if option in options:
                        index = options.index(option)
                        success = await self._device.set_spectrum_mode(index)
                        if success:
                            self.attributes[Attributes.CURRENT_OPTION] = option
                        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                    return StatusCodes.BAD_REQUEST
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

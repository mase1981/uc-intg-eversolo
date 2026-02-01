"""
Eversolo Select entities for input/output/display mode selection.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Features, Select, States

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloInputSelect(Select):
    """Select entity for input source selection."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize select entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}_input"
        entity_name = f"{device_config.name} Input Source"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: "",
            Attributes.OPTIONS: [],
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        _LOG.info("[%s] Input select entity initialized", self.id)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                source_name = params["option"]
                success = await self._device.select_source(source_name)
                if success:
                    await self._device.poll_device()  # Immediate update
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR


class EversoloVUModeSelect(Select):
    """Select entity for VU meter display mode."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize select entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}_vu_mode"
        entity_name = f"{device_config.name} VU Meter Mode"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: "",
            Attributes.OPTIONS: [],
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        self._vu_modes: list[dict] = []
        _LOG.info("[%s] VU Mode select entity initialized", self.id)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                mode_name = params["option"]

                # Find the mode index by title
                mode_index = None
                for mode in self._vu_modes:
                    if mode.get("title") == mode_name:
                        mode_index = mode.get("index")
                        break

                if mode_index is not None:
                    success = await self._device.set_vu_mode(mode_index)
                    if success:
                        await self._device.poll_device()  # Immediate update
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning("[%s] Unknown VU mode: %s", self.id, mode_name)
                    return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _fetch_vu_modes(self) -> None:
        """Fetch available VU modes from device."""
        self._vu_modes = await self._device.get_vu_modes()


class EversoloSpectrumModeSelect(Select):
    """Select entity for spectrum analyzer display mode."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize select entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}_spectrum_mode"
        entity_name = f"{device_config.name} Spectrum Mode"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: "",
            Attributes.OPTIONS: [],
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        self._spectrum_modes: list[dict] = []
        _LOG.info("[%s] Spectrum Mode select entity initialized", self.id)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle select commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                mode_name = params["option"]

                # Find the mode index by title
                mode_index = None
                for mode in self._spectrum_modes:
                    if mode.get("title") == mode_name:
                        mode_index = mode.get("index")
                        break

                if mode_index is not None:
                    success = await self._device.set_spectrum_mode(mode_index)
                    if success:
                        await self._device.poll_device()  # Immediate update
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                else:
                    _LOG.warning("[%s] Unknown spectrum mode: %s", self.id, mode_name)
                    return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

    async def _fetch_spectrum_modes(self) -> None:
        """Fetch available spectrum modes from device."""
        self._spectrum_modes = await self._device.get_spectrum_modes()

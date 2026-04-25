"""
Eversolo select entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, select
from ucapi_framework import SelectEntity

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloInputSelect(SelectEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"select.{device_config.identifier}.input"
        super().__init__(
            entity_id,
            f"{device_config.name} Input Source",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: ["Initializing..."],
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                select.Attributes.STATE: select.States.UNAVAILABLE,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: [],
            })
            return
        options = list(self._device.sources.values())
        current = self._device.get_current_source()
        self.update({
            select.Attributes.STATE: select.States.ON if current else select.States.UNAVAILABLE,
            select.Attributes.CURRENT_OPTION: current or "",
            select.Attributes.OPTIONS: options,
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == "select_option" and params and "option" in params:
            success = await self._device.select_source(params["option"])
            if success:
                await self._device.poll_device()
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
        return StatusCodes.NOT_IMPLEMENTED


class EversoloVUModeSelect(SelectEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"select.{device_config.identifier}.vu_mode"
        super().__init__(
            entity_id,
            f"{device_config.name} VU Meter Mode",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: ["Initializing..."],
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                select.Attributes.STATE: select.States.UNAVAILABLE,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: [],
            })
            return
        modes = self._device.vu_modes
        options = [m.get("title", f"Mode {m.get('index', '?')}") for m in modes]
        self.update({
            select.Attributes.STATE: select.States.ON if options else select.States.UNAVAILABLE,
            select.Attributes.CURRENT_OPTION: options[0] if options else "",
            select.Attributes.OPTIONS: options,
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == "select_option" and params and "option" in params:
            mode_name = params["option"]
            for mode in self._device.vu_modes:
                if mode.get("title") == mode_name:
                    success = await self._device.set_vu_mode(mode.get("index", 0))
                    if success:
                        await self._device.poll_device()
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            _LOG.warning("[%s] Unknown VU mode: %s", self.id, mode_name)
            return StatusCodes.BAD_REQUEST
        return StatusCodes.NOT_IMPLEMENTED


class EversoloSpectrumModeSelect(SelectEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"select.{device_config.identifier}.spectrum_mode"
        super().__init__(
            entity_id,
            f"{device_config.name} Spectrum Mode",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: ["Initializing..."],
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                select.Attributes.STATE: select.States.UNAVAILABLE,
                select.Attributes.CURRENT_OPTION: "",
                select.Attributes.OPTIONS: [],
            })
            return
        modes = self._device.spectrum_modes
        options = [m.get("title", f"Mode {m.get('index', '?')}") for m in modes]
        self.update({
            select.Attributes.STATE: select.States.ON if options else select.States.UNAVAILABLE,
            select.Attributes.CURRENT_OPTION: options[0] if options else "",
            select.Attributes.OPTIONS: options,
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == "select_option" and params and "option" in params:
            mode_name = params["option"]
            for mode in self._device.spectrum_modes:
                if mode.get("title") == mode_name:
                    success = await self._device.set_spectrum_mode(mode.get("index", 0))
                    if success:
                        await self._device.poll_device()
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            _LOG.warning("[%s] Unknown spectrum mode: %s", self.id, mode_name)
            return StatusCodes.BAD_REQUEST
        return StatusCodes.NOT_IMPLEMENTED


def create_selects(config: EversoloConfig, device: EversoloDevice) -> list:
    return [
        EversoloInputSelect(config, device),
        EversoloVUModeSelect(config, device),
        EversoloSpectrumModeSelect(config, device),
    ]

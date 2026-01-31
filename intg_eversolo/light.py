"""
Eversolo Light entities for brightness control.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.light import Attributes, Commands, Features, Light, States

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloDisplayBrightnessLight(Light):
    """Display brightness control as Light entity."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize display brightness light."""
        self._device = device
        self._device_config = device_config

        entity_id = f"light.{device_config.identifier}.display_brightness"

        super().__init__(
            entity_id,
            f"{device_config.name} Display Brightness",
            [Features.ON_OFF, Features.DIM],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.BRIGHTNESS: 0,
            },
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: Light, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle light commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.ON:
                # Turn on with optional brightness parameter
                if params and "brightness" in params:
                    # Convert 0-255 to 0-115
                    brightness_255 = int(params["brightness"])
                    brightness_115 = int((brightness_255 / 255) * 115)
                    success = await self._device.set_display_brightness(brightness_115)
                else:
                    # Turn on to max brightness
                    success = await self._device.set_display_brightness(115)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.OFF:
                # Turn off (brightness 0)
                success = await self._device.set_display_brightness(0)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.TOGGLE:
                # Toggle between off and max
                current = self.attributes.get(Attributes.BRIGHTNESS, 0)
                if current == 0:
                    success = await self._device.set_display_brightness(115)
                else:
                    success = await self._device.set_display_brightness(0)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR


class EversoloKnobBrightnessLight(Light):
    """Knob brightness control as Light entity."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize knob brightness light."""
        self._device = device
        self._device_config = device_config

        entity_id = f"light.{device_config.identifier}.knob_brightness"

        super().__init__(
            entity_id,
            f"{device_config.name} Knob Brightness",
            [Features.ON_OFF, Features.DIM],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.BRIGHTNESS: 0,
            },
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: Light, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle light commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.ON:
                # Turn on with optional brightness parameter
                if params and "brightness" in params:
                    # Already 0-255 scale
                    brightness = int(params["brightness"])
                    success = await self._device.set_knob_brightness(brightness)
                else:
                    # Turn on to max brightness
                    success = await self._device.set_knob_brightness(255)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.OFF:
                # Turn off (brightness 0)
                success = await self._device.set_knob_brightness(0)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.TOGGLE:
                # Toggle between off and max
                current = self.attributes.get(Attributes.BRIGHTNESS, 0)
                if current == 0:
                    success = await self._device.set_knob_brightness(255)
                else:
                    success = await self._device.set_knob_brightness(0)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

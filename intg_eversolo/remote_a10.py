"""
Eversolo Remote entity for DMP-A10 (DAC/Preamp - No HDMI/Knob).

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Attributes, Features, Remote

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloRemoteA10(Remote):
    """Remote entity for Eversolo DMP-A10 without HDMI or knob brightness."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize remote entity."""
        self._device = device
        self._device_config = device_config

        entity_id = f"remote.{device_config.identifier}"
        entity_name = f"{device_config.name} Remote"

        features = [Features.SEND_CMD]
        attributes = {Attributes.STATE: "UNKNOWN"}

        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            cmd_handler=self.handle_command,
        )

        self._update_options()
        _LOG.info("[%s] Remote entity initialized", self.id)

    def _update_options(self) -> None:
        """Update remote UI options with static pages."""
        self.options = {
            "simple_commands": [],  # No simple commands, only UI pages
            "button_mapping": [],  # No button mapping
            "user_interface": {"pages": self._get_ui_pages()},
        }

    def _get_ui_pages(self) -> list[dict]:
        """Return UI pages for remote control."""
        return [
            {
                "page_id": "playback",
                "name": "Playback",
                "grid": {"width": 3, "height": 3},
                "items": [
                    {"type": "icon", "icon": "uc:prev", "command": {"cmd_id": "PREVIOUS"}, "location": {"x": 0, "y": 0}},
                    {"type": "icon", "icon": "uc:play", "command": {"cmd_id": "PLAY"}, "location": {"x": 1, "y": 0}},
                    {"type": "icon", "icon": "uc:next", "command": {"cmd_id": "NEXT"}, "location": {"x": 2, "y": 0}},
                    {"type": "icon", "icon": "uc:shuffle", "command": {"cmd_id": "SHUFFLE"}, "location": {"x": 0, "y": 1}},
                    {"type": "icon", "icon": "uc:pause", "command": {"cmd_id": "PAUSE"}, "location": {"x": 1, "y": 1}},
                    {"type": "icon", "icon": "uc:repeat", "command": {"cmd_id": "REPEAT"}, "location": {"x": 2, "y": 1}},
                    {"type": "icon", "icon": "uc:backward", "command": {"cmd_id": "REWIND"}, "location": {"x": 0, "y": 2}},
                    {"type": "icon", "icon": "uc:stop", "command": {"cmd_id": "STOP"}, "location": {"x": 1, "y": 2}},
                    {"type": "icon", "icon": "uc:forward", "command": {"cmd_id": "FAST_FORWARD"}, "location": {"x": 2, "y": 2}},
                ],
            },
            {
                "page_id": "volume",
                "name": "Volume",
                "grid": {"width": 3, "height": 2},
                "items": [
                    {"type": "icon", "icon": "uc:minus", "command": {"cmd_id": "VOLUME_DOWN"}, "location": {"x": 0, "y": 0}},
                    {"type": "icon", "icon": "uc:mute", "command": {"cmd_id": "MUTE"}, "location": {"x": 1, "y": 0}},
                    {"type": "icon", "icon": "uc:plus", "command": {"cmd_id": "VOLUME_UP"}, "location": {"x": 2, "y": 0}},
                    {"type": "text", "text": "Vol -10", "command": {"cmd_id": "VOLUME_DOWN_10"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "Unmute", "command": {"cmd_id": "UNMUTE"}, "location": {"x": 1, "y": 1}},
                    {"type": "text", "text": "Vol +10", "command": {"cmd_id": "VOLUME_UP_10"}, "location": {"x": 2, "y": 1}},
                ],
            },
            {
                "page_id": "outputs",
                "name": "Audio Outputs",
                "grid": {"width": 2, "height": 2},
                "items": [
                    {"type": "text", "text": "RCA", "command": {"cmd_id": "OUTPUT_RCA"}, "location": {"x": 0, "y": 0}},
                    {"type": "text", "text": "XLR", "command": {"cmd_id": "OUTPUT_XLR"}, "location": {"x": 1, "y": 0}},
                    {"type": "text", "text": "OPT/COAX", "command": {"cmd_id": "OUTPUT_SPDIF"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "XLR/RCA", "command": {"cmd_id": "OUTPUT_XLRRCA"}, "location": {"x": 1, "y": 1}},
                ],
            },
            {
                "page_id": "brightness",
                "name": "Display",
                "grid": {"width": 2, "height": 2},
                "items": [
                    {"type": "text", "text": "Display -", "command": {"cmd_id": "DISPLAY_DIM"}, "location": {"x": 0, "y": 0}},
                    {"type": "text", "text": "Display +", "command": {"cmd_id": "DISPLAY_BRIGHT"}, "location": {"x": 1, "y": 0}},
                    {"type": "text", "text": "Display Off", "command": {"cmd_id": "DISPLAY_OFF"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "Display On", "command": {"cmd_id": "DISPLAY_ON"}, "location": {"x": 1, "y": 1}},
                ],
            },
        ]

    async def handle_command(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle remote commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        # Extract actual command from send_cmd params
        if cmd_id == "send_cmd" and params and "command" in params:
            cmd_id = params["command"]
            _LOG.debug("[%s] Extracted command: %s", self.id, cmd_id)

        try:
            # Playback commands
            if cmd_id == "PLAY":
                success = await self._device.play_pause()
            elif cmd_id == "PAUSE":
                success = await self._device.play_pause()
            elif cmd_id == "STOP":
                success = await self._device.play_pause()
            elif cmd_id == "NEXT":
                success = await self._device.next_track()
            elif cmd_id == "PREVIOUS":
                success = await self._device.previous_track()
            elif cmd_id == "SHUFFLE":
                _LOG.warning("[%s] SHUFFLE not supported by device", self.id)
                return StatusCodes.NOT_IMPLEMENTED
            elif cmd_id == "REPEAT":
                _LOG.warning("[%s] REPEAT not supported by device", self.id)
                return StatusCodes.NOT_IMPLEMENTED
            elif cmd_id == "REWIND":
                _LOG.warning("[%s] REWIND not supported by device", self.id)
                return StatusCodes.NOT_IMPLEMENTED
            elif cmd_id == "FAST_FORWARD":
                _LOG.warning("[%s] FAST_FORWARD not supported by device", self.id)
                return StatusCodes.NOT_IMPLEMENTED

            # Volume commands
            elif cmd_id == "VOLUME_UP":
                success = await self._device.volume_up()
            elif cmd_id == "VOLUME_DOWN":
                success = await self._device.volume_down()
            elif cmd_id == "VOLUME_UP_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(min(100, current + 10))
            elif cmd_id == "VOLUME_DOWN_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(max(0, current - 10))
            elif cmd_id == "MUTE":
                success = await self._device.mute()
            elif cmd_id == "UNMUTE":
                success = await self._device.unmute()

            # Output selection commands (dynamic based on available outputs)
            elif cmd_id.startswith("OUTPUT_"):
                tag = cmd_id.replace("OUTPUT_", "")
                success = await self._device.select_output_by_tag(tag)

            # Brightness commands
            elif cmd_id == "DISPLAY_BRIGHT":
                current = await self._device.get_display_brightness() or 0
                success = await self._device.set_display_brightness(min(115, current + 10))
            elif cmd_id == "DISPLAY_DIM":
                current = await self._device.get_display_brightness() or 0
                success = await self._device.set_display_brightness(max(0, current - 10))
            elif cmd_id == "DISPLAY_OFF":
                success = await self._device.turn_screen_off()
            elif cmd_id == "DISPLAY_ON":
                success = await self._device.turn_screen_on()
            elif cmd_id == "KNOB_BRIGHT":
                current = await self._device.get_knob_brightness() or 0
                success = await self._device.set_knob_brightness(min(255, current + 20))
            elif cmd_id == "KNOB_DIM":
                current = await self._device.get_knob_brightness() or 0
                success = await self._device.set_knob_brightness(max(0, current - 20))

            else:
                _LOG.warning("[%s] Unknown command: %s", self.id, cmd_id)
                return StatusCodes.NOT_IMPLEMENTED

            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

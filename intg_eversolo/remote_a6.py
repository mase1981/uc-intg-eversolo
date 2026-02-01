"""
Eversolo Remote entity for DMP-A6 (Music Streamer with HDMI & Knob).

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


class EversoloRemoteA6(Remote):
    """Remote entity for Eversolo DMP-A6 with HDMI and knob brightness."""

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
                "grid": {"width": 3, "height": 2},
                "items": [
                    {"type": "icon", "icon": "uc:prev", "command": {"cmd_id": "PREVIOUS"}, "location": {"x": 0, "y": 0}},
                    {"type": "icon", "icon": "uc:play-pause", "command": {"cmd_id": "PLAY_PAUSE"}, "location": {"x": 1, "y": 0}},
                    {"type": "icon", "icon": "uc:next", "command": {"cmd_id": "NEXT"}, "location": {"x": 2, "y": 0}},
                    {"type": "icon", "icon": "uc:power-on", "command": {"cmd_id": "POWER_TOGGLE"}, "location": {"x": 1, "y": 1}},
                ],
            },
            {
                "page_id": "volume",
                "name": "Volume",
                "grid": {"width": 3, "height": 2},
                "items": [
                    {"type": "icon", "icon": "uc:minus", "command": {"cmd_id": "VOLUME_DOWN"}, "location": {"x": 0, "y": 0}},
                    {"type": "icon", "icon": "uc:mute", "command": {"cmd_id": "MUTE_TOGGLE"}, "location": {"x": 1, "y": 0}},
                    {"type": "icon", "icon": "uc:plus", "command": {"cmd_id": "VOLUME_UP"}, "location": {"x": 2, "y": 0}},
                    {"type": "text", "text": "Vol -10", "command": {"cmd_id": "VOLUME_DOWN_10"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "Vol +10", "command": {"cmd_id": "VOLUME_UP_10"}, "location": {"x": 2, "y": 1}},
                ],
            },
            {
                "page_id": "outputs",
                "name": "Audio Outputs",
                "grid": {"width": 3, "height": 3},
                "items": [
                    {"type": "text", "text": "RCA", "command": {"cmd_id": "OUTPUT_RCA"}, "location": {"x": 0, "y": 0}},
                    {"type": "text", "text": "XLR", "command": {"cmd_id": "OUTPUT_XLR"}, "location": {"x": 1, "y": 0}},
                    {"type": "text", "text": "HDMI", "command": {"cmd_id": "OUTPUT_HDMI"}, "location": {"x": 2, "y": 0}},
                    {"type": "text", "text": "USB DAC", "command": {"cmd_id": "OUTPUT_USB"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "OPT/COAX", "command": {"cmd_id": "OUTPUT_SPDIF"}, "location": {"x": 1, "y": 1}},
                    {"type": "text", "text": "XLR/RCA", "command": {"cmd_id": "OUTPUT_XLRRCA"}, "location": {"x": 2, "y": 1}},
                    {"type": "text", "text": "IIS", "command": {"cmd_id": "OUTPUT_IIS"}, "location": {"x": 0, "y": 2}},
                ],
            },
            {
                "page_id": "brightness",
                "name": "Brightness",
                "grid": {"width": 2, "height": 3},
                "items": [
                    {"type": "text", "text": "Display -", "command": {"cmd_id": "DISPLAY_DIM"}, "location": {"x": 0, "y": 0}},
                    {"type": "text", "text": "Display +", "command": {"cmd_id": "DISPLAY_BRIGHT"}, "location": {"x": 1, "y": 0}},
                    {"type": "text", "text": "Display Off", "command": {"cmd_id": "DISPLAY_OFF"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "Display On", "command": {"cmd_id": "DISPLAY_ON"}, "location": {"x": 1, "y": 1}},
                    {"type": "text", "text": "Knob -", "command": {"cmd_id": "KNOB_DIM"}, "location": {"x": 0, "y": 2}},
                    {"type": "text", "text": "Knob +", "command": {"cmd_id": "KNOB_BRIGHT"}, "location": {"x": 1, "y": 2}},
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
            if cmd_id == "PLAY_PAUSE":
                success = await self._device.play_pause()
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "NEXT":
                success = await self._device.next_track()
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "PREVIOUS":
                success = await self._device.previous_track()
                if success:
                    await self._device.poll_device()  # Immediate update

            # Power control
            elif cmd_id == "POWER_TOGGLE":
                # If device is reachable, turn it off; otherwise try to wake it
                success = await self._device.power_off()

            # Volume commands
            elif cmd_id == "VOLUME_UP":
                success = await self._device.volume_up()
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "VOLUME_DOWN":
                success = await self._device.volume_down()
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "VOLUME_UP_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(min(100, current + 10))
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "VOLUME_DOWN_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(max(0, current - 10))
                if success:
                    await self._device.poll_device()  # Immediate update
            elif cmd_id == "MUTE_TOGGLE":
                if self._device.get_muted():
                    success = await self._device.unmute()
                else:
                    success = await self._device.mute()
                if success:
                    await self._device.poll_device()  # Immediate update

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

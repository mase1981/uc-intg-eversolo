"""
Eversolo remote entities with model-specific UI pages.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, remote
from ucapi_framework import RemoteEntity

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)

SIMPLE_COMMANDS = [
    "OUTPUT_RCA", "OUTPUT_XLR", "OUTPUT_HDMI", "OUTPUT_USB",
    "OUTPUT_IIS", "OUTPUT_SPDIF", "OUTPUT_XLRRCA",
    "DISPLAY_ON", "DISPLAY_OFF",
    "PLAY_PAUSE", "NEXT", "PREVIOUS", "POWER_TOGGLE",
    "VOLUME_UP", "VOLUME_DOWN", "MUTE_TOGGLE",
]


class _EversoloRemoteBase(RemoteEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"remote.{device_config.identifier}"
        entity_name = f"{device_config.name} Remote"

        super().__init__(
            entity_id,
            entity_name,
            [remote.Features.SEND_CMD],
            {remote.Attributes.STATE: "UNKNOWN"},
            cmd_handler=self._handle_command,
            simple_commands=SIMPLE_COMMANDS,
            button_mapping=self._get_button_mapping(),
            ui_pages=self._get_ui_pages(),
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({remote.Attributes.STATE: "OFF"})
            return
        self.update({remote.Attributes.STATE: "ON"})

    def _get_button_mapping(self) -> list:
        return []

    def _get_ui_pages(self) -> list[dict]:
        raise NotImplementedError

    def _playback_page(self) -> dict:
        return {
            "page_id": "playback",
            "name": "Playback",
            "grid": {"width": 3, "height": 2},
            "items": [
                {"type": "icon", "icon": "uc:prev", "command": {"cmd_id": "PREVIOUS"}, "location": {"x": 0, "y": 0}},
                {"type": "icon", "icon": "uc:play-pause", "command": {"cmd_id": "PLAY_PAUSE"}, "location": {"x": 1, "y": 0}},
                {"type": "icon", "icon": "uc:next", "command": {"cmd_id": "NEXT"}, "location": {"x": 2, "y": 0}},
                {"type": "icon", "icon": "uc:power-on", "command": {"cmd_id": "POWER_TOGGLE"}, "location": {"x": 1, "y": 1}},
            ],
        }

    def _volume_page(self) -> dict:
        return {
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
        }

    def _brightness_page_with_knob(self) -> dict:
        return {
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
        }

    def _brightness_page_no_knob(self) -> dict:
        return {
            "page_id": "brightness",
            "name": "Display",
            "grid": {"width": 2, "height": 2},
            "items": [
                {"type": "text", "text": "Display -", "command": {"cmd_id": "DISPLAY_DIM"}, "location": {"x": 0, "y": 0}},
                {"type": "text", "text": "Display +", "command": {"cmd_id": "DISPLAY_BRIGHT"}, "location": {"x": 1, "y": 0}},
                {"type": "text", "text": "Display Off", "command": {"cmd_id": "DISPLAY_OFF"}, "location": {"x": 0, "y": 1}},
                {"type": "text", "text": "Display On", "command": {"cmd_id": "DISPLAY_ON"}, "location": {"x": 1, "y": 1}},
            ],
        }

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == "send_cmd" and params and "command" in params:
            cmd_id = params["command"]

        try:
            success = True
            poll_after = False

            # Playback
            if cmd_id == "PLAY_PAUSE":
                success = await self._device.play_pause()
                poll_after = True
            elif cmd_id == "NEXT":
                success = await self._device.next_track()
                poll_after = True
            elif cmd_id == "PREVIOUS":
                success = await self._device.previous_track()
                poll_after = True
            elif cmd_id == "POWER_TOGGLE":
                success = await self._device.power_off()

            # Volume
            elif cmd_id == "VOLUME_UP":
                success = await self._device.volume_up()
                poll_after = True
            elif cmd_id == "VOLUME_DOWN":
                success = await self._device.volume_down()
                poll_after = True
            elif cmd_id == "VOLUME_UP_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(min(100, current + 10))
                poll_after = True
            elif cmd_id == "VOLUME_DOWN_10":
                current = self._device.get_volume() or 0
                success = await self._device.set_volume(max(0, current - 10))
                poll_after = True
            elif cmd_id == "MUTE_TOGGLE":
                if self._device.get_muted():
                    success = await self._device.unmute()
                else:
                    success = await self._device.mute()
                poll_after = True

            # Output selection
            elif cmd_id.startswith("OUTPUT_"):
                tag = cmd_id.replace("OUTPUT_", "")
                success = await self._device.select_output_by_tag(tag)

            # Brightness
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
                return StatusCodes.NOT_IMPLEMENTED

            if poll_after and success:
                await self._device.poll_device()
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR


class EversoloRemoteA6(_EversoloRemoteBase):
    """DMP-A6: Has HDMI + Knob."""

    def _get_ui_pages(self) -> list[dict]:
        return [
            self._playback_page(),
            self._volume_page(),
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
            self._brightness_page_with_knob(),
        ]


class EversoloRemoteA8(_EversoloRemoteBase):
    """DMP-A8: Has Knob, no HDMI."""

    def _get_ui_pages(self) -> list[dict]:
        return [
            self._playback_page(),
            self._volume_page(),
            {
                "page_id": "outputs",
                "name": "Audio Outputs",
                "grid": {"width": 3, "height": 2},
                "items": [
                    {"type": "text", "text": "RCA", "command": {"cmd_id": "OUTPUT_RCA"}, "location": {"x": 0, "y": 0}},
                    {"type": "text", "text": "XLR", "command": {"cmd_id": "OUTPUT_XLR"}, "location": {"x": 1, "y": 0}},
                    {"type": "text", "text": "IIS", "command": {"cmd_id": "OUTPUT_IIS"}, "location": {"x": 2, "y": 0}},
                    {"type": "text", "text": "OPT/COAX", "command": {"cmd_id": "OUTPUT_SPDIF"}, "location": {"x": 0, "y": 1}},
                    {"type": "text", "text": "XLR/RCA", "command": {"cmd_id": "OUTPUT_XLRRCA"}, "location": {"x": 1, "y": 1}},
                ],
            },
            self._brightness_page_with_knob(),
        ]


class EversoloRemoteA10(_EversoloRemoteBase):
    """DMP-A10: No HDMI, no Knob."""

    def _get_ui_pages(self) -> list[dict]:
        return [
            self._playback_page(),
            self._volume_page(),
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
            self._brightness_page_no_knob(),
        ]


def create_remote(config: EversoloConfig, device: EversoloDevice):
    model = config.model or "DMP-A6"
    if "A8" in model:
        return EversoloRemoteA8(config, device)
    elif "A10" in model:
        return EversoloRemoteA10(config, device)
    return EversoloRemoteA6(config, device)

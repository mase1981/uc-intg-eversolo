"""
Eversolo Media Player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.media_player import (
    Attributes,
    Commands,
    DeviceClasses,
    Features,
    MediaPlayer,
    States,
)
from ucapi_framework import DeviceEvents

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloMediaPlayer(MediaPlayer):
    """Media player entity for Eversolo."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"media_player.{device_config.identifier}"

        super().__init__(
            entity_id,
            device_config.name,
            [
                Features.ON_OFF,
                Features.VOLUME,
                Features.VOLUME_UP_DOWN,
                Features.MUTE_TOGGLE,
                Features.MUTE,
                Features.UNMUTE,
                Features.PLAY_PAUSE,
                Features.NEXT,
                Features.PREVIOUS,
                Features.SEEK,
                Features.MEDIA_TITLE,
                Features.MEDIA_ARTIST,
                Features.MEDIA_ALBUM,
                Features.MEDIA_DURATION,
                Features.MEDIA_POSITION,
                Features.MEDIA_IMAGE_URL,
                Features.MEDIA_TYPE,
                Features.SELECT_SOURCE,
            ],
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VOLUME: 0,
                Attributes.MUTED: False,
                Attributes.SOURCE: "",
                Attributes.SOURCE_LIST: [],
                Attributes.MEDIA_IMAGE_URL: "",
                Attributes.MEDIA_TYPE: "",
            },
            device_class=DeviceClasses.STREAMING_BOX,
            cmd_handler=self.handle_command,
        )

        _LOG.debug("[%s] >>> Subscribing to device UPDATE events", entity_id)
        self._device.events.on(DeviceEvents.UPDATE, self._on_device_update)
        _LOG.debug("[%s] >>> Successfully subscribed to device UPDATE events", entity_id)

    def _on_device_update(self, update: dict[str, Any] | None = None, **kwargs) -> None:
        """Handle device update events."""
        _LOG.debug("[%s] >>> Received UPDATE event from device", self.id)
        volume = self._device.get_volume()
        if volume is not None:
            self.attributes[Attributes.VOLUME] = volume

        self.attributes[Attributes.MUTED] = self._device.get_muted()

        state = self._device.get_state()
        if state == "IDLE":
            self.attributes[Attributes.STATE] = States.IDLE
        elif state == "PLAYING":
            self.attributes[Attributes.STATE] = States.PLAYING
        elif state == "PAUSED":
            self.attributes[Attributes.STATE] = States.PAUSED
        else:
            self.attributes[Attributes.STATE] = States.STANDBY

        current_source = self._device.get_current_source()
        if current_source:
            self.attributes[Attributes.SOURCE] = current_source

        if self._device.sources:
            self.attributes[Attributes.SOURCE_LIST] = list(
                self._device.sources.values()
            )

        # Media information - ALWAYS update to clear stale data
        media_info = self._device.get_media_info()

        # For media attributes, always set them (even if None/empty)
        # This ensures stale data is cleared when playback stops
        self.attributes[Attributes.MEDIA_TITLE] = media_info["title"] or ""
        self.attributes[Attributes.MEDIA_ARTIST] = media_info["artist"] or ""
        self.attributes[Attributes.MEDIA_ALBUM] = media_info["album"] or ""
        self.attributes[Attributes.MEDIA_IMAGE_URL] = media_info["image_url"] or ""
        self.attributes[Attributes.MEDIA_TYPE] = media_info["media_type"] or ""

        # Duration and position - use 0 as default instead of None
        self.attributes[Attributes.MEDIA_DURATION] = (
            int(media_info["duration"]) if media_info["duration"] else 0
        )
        self.attributes[Attributes.MEDIA_POSITION] = (
            int(media_info["position"]) if media_info["position"] else 0
        )

    async def handle_command(
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.OFF:
                success = await self._device.power_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME:
                if params and "volume" in params:
                    success = await self._device.set_volume(int(params["volume"]))
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.VOLUME_UP:
                success = await self._device.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._device.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE_TOGGLE:
                if self._device.get_muted():
                    success = await self._device.unmute()
                else:
                    success = await self._device.mute()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE:
                success = await self._device.mute()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.UNMUTE:
                success = await self._device.unmute()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.PLAY_PAUSE:
                success = await self._device.play_pause()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.NEXT:
                success = await self._device.next_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.PREVIOUS:
                success = await self._device.previous_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.SEEK:
                if params and "media_position" in params:
                    success = await self._device.seek(float(params["media_position"]))
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SELECT_SOURCE:
                if params and "source" in params:
                    success = await self._device.select_source(params["source"])
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.SELECT_SOUND_MODE:
                if params and "mode" in params:
                    success = await self._device.select_output(params["mode"])
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

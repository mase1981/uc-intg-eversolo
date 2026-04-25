"""
Eversolo media player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, media_player
from ucapi_framework import MediaPlayerEntity

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.TOGGLE,
    media_player.Features.VOLUME,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MUTE,
    media_player.Features.UNMUTE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.SEEK,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_ARTIST,
    media_player.Features.MEDIA_ALBUM,
    media_player.Features.MEDIA_DURATION,
    media_player.Features.MEDIA_POSITION,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.SELECT_SOURCE,
    media_player.Features.SELECT_SOUND_MODE,
]


class EversoloMediaPlayer(MediaPlayerEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"
        super().__init__(
            entity_id,
            device_config.name,
            FEATURES,
            {
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.VOLUME: 0,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.SOURCE: "",
                media_player.Attributes.SOURCE_LIST: [],
                media_player.Attributes.SOUND_MODE: "",
                media_player.Attributes.SOUND_MODE_LIST: [],
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "",
            },
            device_class=media_player.DeviceClasses.STREAMING_BOX,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                media_player.Attributes.STATE: media_player.States.OFF,
                media_player.Attributes.VOLUME: 0,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.SOURCE: "",
                media_player.Attributes.SOURCE_LIST: [],
                media_player.Attributes.SOUND_MODE: "",
                media_player.Attributes.SOUND_MODE_LIST: [],
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_ARTIST: "",
                media_player.Attributes.MEDIA_ALBUM: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "",
                media_player.Attributes.MEDIA_DURATION: 0,
                media_player.Attributes.MEDIA_POSITION: 0,
            })
            return

        state = self._device.get_state()
        if state == "IDLE":
            mp_state = media_player.States.ON
        elif state == "PLAYING":
            mp_state = media_player.States.PLAYING
        elif state == "PAUSED":
            mp_state = media_player.States.PAUSED
        else:
            mp_state = media_player.States.STANDBY

        volume = self._device.get_volume()
        media_info = self._device.get_media_info()

        self.update({
            media_player.Attributes.STATE: mp_state,
            media_player.Attributes.VOLUME: volume if volume is not None else 0,
            media_player.Attributes.MUTED: self._device.get_muted(),
            media_player.Attributes.SOURCE: self._device.get_current_source() or "",
            media_player.Attributes.SOURCE_LIST: list(self._device.sources.values()),
            media_player.Attributes.SOUND_MODE: self._device.get_current_output() or "",
            media_player.Attributes.SOUND_MODE_LIST: list(self._device.outputs.values()),
            media_player.Attributes.MEDIA_TITLE: media_info["title"] or "",
            media_player.Attributes.MEDIA_ARTIST: media_info["artist"] or "",
            media_player.Attributes.MEDIA_ALBUM: media_info["album"] or "",
            media_player.Attributes.MEDIA_IMAGE_URL: media_info["image_url"] or "",
            media_player.Attributes.MEDIA_TYPE: media_info["media_type"] or "",
            media_player.Attributes.MEDIA_DURATION: int(media_info["duration"]) if media_info["duration"] else 0,
            media_player.Attributes.MEDIA_POSITION: int(media_info["position"]) if media_info["position"] else 0,
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")
        try:
            match cmd_id:
                case media_player.Commands.ON:
                    success = await self._device.power_on()
                case media_player.Commands.OFF:
                    success = await self._device.power_off()
                case media_player.Commands.TOGGLE:
                    if self.attributes.get(media_player.Attributes.STATE) == media_player.States.OFF:
                        success = await self._device.power_on()
                    else:
                        success = await self._device.power_off()
                case media_player.Commands.VOLUME:
                    if params and "volume" in params:
                        success = await self._device.set_volume(int(params["volume"]))
                    else:
                        return StatusCodes.BAD_REQUEST
                case media_player.Commands.VOLUME_UP:
                    success = await self._device.volume_up()
                case media_player.Commands.VOLUME_DOWN:
                    success = await self._device.volume_down()
                case media_player.Commands.MUTE_TOGGLE:
                    if self._device.get_muted():
                        success = await self._device.unmute()
                    else:
                        success = await self._device.mute()
                case media_player.Commands.MUTE:
                    success = await self._device.mute()
                case media_player.Commands.UNMUTE:
                    success = await self._device.unmute()
                case media_player.Commands.PLAY_PAUSE:
                    success = await self._device.play_pause()
                case media_player.Commands.NEXT:
                    success = await self._device.next_track()
                case media_player.Commands.PREVIOUS:
                    success = await self._device.previous_track()
                case media_player.Commands.SEEK:
                    if params and "media_position" in params:
                        success = await self._device.seek(float(params["media_position"]))
                    else:
                        return StatusCodes.BAD_REQUEST
                case media_player.Commands.SELECT_SOURCE:
                    if params and "source" in params:
                        success = await self._device.select_source(params["source"])
                    else:
                        return StatusCodes.BAD_REQUEST
                case media_player.Commands.SELECT_SOUND_MODE:
                    if params and "mode" in params:
                        success = await self._device.select_output(params["mode"])
                    else:
                        return StatusCodes.BAD_REQUEST
                case _:
                    return StatusCodes.NOT_IMPLEMENTED

            if success:
                await self._device.poll_device()
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR

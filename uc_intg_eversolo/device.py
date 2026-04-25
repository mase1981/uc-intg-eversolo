"""
Eversolo device implementation.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import socket
from typing import Any

import aiohttp
from ucapi_framework import PollingDevice

from uc_intg_eversolo.config import EversoloConfig

_LOG = logging.getLogger(__name__)


class EversoloDevice(PollingDevice):

    def __init__(self, device_config: EversoloConfig, **kwargs):
        super().__init__(device_config, poll_interval=5, **kwargs)
        self._device_config = device_config
        self._session: aiohttp.ClientSession | None = None
        self._state_data: dict[str, Any] = {}
        self._sources: dict[str, str] = {}
        self._source_tags: dict[str, str] = {}
        self._outputs: dict[str, str] = {}
        self._output_tags: dict[str, str] = {}
        self._model_info: dict[str, Any] = {}
        self._previous_media_title: str | None = None
        self._end_of_track_poll_scheduled: bool = False
        self._vu_modes: list[dict] = []
        self._spectrum_modes: list[dict] = []

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address}:{self._device_config.port})"

    @property
    def state_data(self) -> dict[str, Any]:
        return self._state_data

    @property
    def sources(self) -> dict[str, str]:
        return self._sources

    @property
    def outputs(self) -> dict[str, str]:
        return self._outputs

    @property
    def model_info(self) -> dict[str, Any]:
        return self._model_info

    @property
    def model_name(self) -> str | None:
        return self._model_info.get("model")

    @property
    def vu_modes(self) -> list[dict]:
        return self._vu_modes

    @property
    def spectrum_modes(self) -> list[dict]:
        return self._spectrum_modes

    @property
    def device_reachable(self) -> bool:
        return self._state_data.get("device_reachable", False)

    async def _create_session(self) -> None:
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=60, connect=20, sock_read=30)
            connector = aiohttp.TCPConnector(
                limit=10, force_close=False, enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)

    async def establish_connection(self) -> aiohttp.ClientSession:
        _LOG.info("[%s] Establishing connection", self.log_id)
        await self._create_session()

        music_state = await self._api_request(
            "/ZidooMusicControl/v2/getState", timeout=15.0
        )
        _LOG.info("[%s] Connection established", self.log_id)

        if not self._device_config.mac_address:
            await self._fetch_and_store_mac_address(music_state)

        await self.poll_device()
        return self._session

    async def close_connection(self) -> None:
        if self._session:
            await self._session.close()
            await asyncio.sleep(0.25)
            self._session = None

    async def _api_request(
        self, endpoint: str, parse_json: bool = True, timeout: float = 20.0
    ) -> Any:
        if not self._session:
            await self._create_session()

        url = f"http://{self._device_config.host}:{self._device_config.port}{endpoint}"
        try:
            request_timeout = aiohttp.ClientTimeout(total=timeout)
            async with self._session.get(url, timeout=request_timeout) as response:
                response.raise_for_status()
                if parse_json:
                    return await response.json(content_type=None)
                return await response.read()
        except asyncio.TimeoutError:
            _LOG.error("[%s] Request timeout: %s", self.log_id, endpoint)
            raise
        except aiohttp.ClientError as err:
            _LOG.error("[%s] Request error: %s - %s", self.log_id, endpoint, err)
            raise
        except Exception as err:
            _LOG.error("[%s] Unexpected error: %s - %s", self.log_id, endpoint, err)
            raise

    async def poll_device(self) -> None:
        try:
            if not self._model_info:
                model_info = await self.get_device_model()
                if model_info:
                    self._model_info = model_info
                    _LOG.info("[%s] Model detected: %s", self.log_id, self.model_name or "Unknown")

            music_state = await self._api_request("/ZidooMusicControl/v2/getState", timeout=30.0)
            input_output_state = await self._api_request(
                "/ZidooMusicControl/v2/getInputAndOutputList", timeout=30.0
            )

            self._state_data["music_control_state"] = music_state
            self._state_data["device_reachable"] = True

            if input_output_state:
                self._state_data["input_output_state"] = input_output_state
                self._parse_sources(input_output_state)
                self._parse_outputs(input_output_state)

            # Fetch VU/Spectrum modes once
            if not self._vu_modes:
                self._vu_modes = await self._fetch_vu_modes()
            if not self._spectrum_modes:
                self._spectrum_modes = await self._fetch_spectrum_modes()

            # Track change detection
            current_title = music_state.get("title", "")
            playback_state = music_state.get("status", 0)
            is_playing = playback_state == 1

            if current_title and self._previous_media_title is not None:
                if current_title != self._previous_media_title and is_playing:
                    _LOG.info("[%s] Track changed: '%s' -> '%s'",
                              self.log_id, self._previous_media_title, current_title)
            self._previous_media_title = current_title

            # Schedule quick poll near end of track
            if is_playing:
                duration = music_state.get("duration", 0)
                position = music_state.get("playingTime", 0)
                if duration > 0 and position > 0:
                    remaining = duration - position
                    if 0 < remaining <= 5000 and not self._end_of_track_poll_scheduled:
                        self._end_of_track_poll_scheduled = True
                        asyncio.create_task(self._poll_after_delay(1.5))
                    elif remaining > 5000:
                        self._end_of_track_poll_scheduled = False

            self.push_update()

        except Exception as err:
            _LOG.warning("[%s] Device unreachable: %s", self.log_id, err)
            self._state_data["device_reachable"] = False
            self.push_update()

    async def _poll_after_delay(self, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        await self.poll_device()

    def _parse_sources(self, input_output_state: dict) -> None:
        sources = input_output_state.get("inputData", [])
        self._sources = {}
        self._source_tags = {}
        for source in sources:
            tag = source.get("tag", "").replace("/", "")
            name = source.get("name", "")
            if tag and name:
                self._sources[tag] = name
                self._source_tags[name] = tag

    def _parse_outputs(self, input_output_state: dict) -> None:
        outputs = input_output_state.get("outputData", [])
        self._outputs = {}
        self._output_tags = {}
        for output in outputs:
            if output.get("enable") is True:
                tag = output.get("tag", "").replace("/", "")
                name = output.get("name", "")
                if tag and name:
                    self._outputs[tag] = name
                    self._output_tags[name] = tag

    # State getters
    def get_volume(self) -> int | None:
        music_state = self._state_data.get("music_control_state", {})
        volume_data = music_state.get("volumeData", {})
        current_volume = volume_data.get("currenttVolume")
        max_volume = volume_data.get("maxVolume")
        if current_volume is not None and max_volume and max_volume > 0:
            return int((current_volume / max_volume) * 100)
        return None

    def get_muted(self) -> bool:
        music_state = self._state_data.get("music_control_state", {})
        return bool(music_state.get("volumeData", {}).get("isMute", False))

    def get_state(self) -> str:
        music_state = self._state_data.get("music_control_state", {})
        state = music_state.get("state", -1)
        if state == 0:
            return "IDLE"
        elif state == 3:
            return "PLAYING"
        elif state == 4:
            return "PAUSED"
        return "UNKNOWN"

    def get_current_source(self) -> str | None:
        input_output_state = self._state_data.get("input_output_state", {})
        input_index = input_output_state.get("inputIndex", -1)
        if 0 <= input_index < len(self._sources):
            return list(self._sources.values())[input_index]
        return None

    def get_current_output(self) -> str | None:
        input_output_state = self._state_data.get("input_output_state", {})
        output_index = input_output_state.get("outputIndex", -1)
        if 0 <= output_index < len(self._outputs):
            return list(self._outputs.values())[output_index]
        return None

    def get_media_info(self) -> dict[str, Any]:
        music_state = self._state_data.get("music_control_state", {})
        play_type = music_state.get("playType", None)

        info = {
            "title": None, "artist": None, "album": None,
            "image_url": None, "media_type": None,
            "duration": None, "position": None,
        }

        if play_type in [4, 6, 7]:
            audio_info = (
                music_state.get("everSoloPlayInfo", {})
                .get("everSoloPlayAudioInfo", {})
            )
            info["title"] = audio_info.get("songName")
            info["artist"] = audio_info.get("artistName")
            info["album"] = audio_info.get("albumName")
            info["image_url"] = (
                audio_info.get("albumUrl") or audio_info.get("albumArt") or
                audio_info.get("artwork") or audio_info.get("coverArt") or
                audio_info.get("image") or audio_info.get("thumb")
            )
            info["media_type"] = "MUSIC"
        elif play_type == 5:
            playing_music = music_state.get("playingMusic", {})
            info["title"] = playing_music.get("title")
            info["artist"] = playing_music.get("artist")
            info["album"] = playing_music.get("album")
            info["image_url"] = (
                playing_music.get("albumArt") or playing_music.get("albumArtBig") or
                playing_music.get("artwork") or playing_music.get("image") or
                playing_music.get("thumb") or playing_music.get("coverUrl")
            )
            info["media_type"] = "MUSIC"
        else:
            audio_info = (
                music_state.get("everSoloPlayInfo", {})
                .get("everSoloPlayAudioInfo", {})
            )
            playing_music = music_state.get("playingMusic", {})
            info["title"] = playing_music.get("title") or audio_info.get("songName")
            info["artist"] = playing_music.get("artist") or audio_info.get("artistName")
            info["album"] = playing_music.get("album") or audio_info.get("albumName")
            info["image_url"] = (
                playing_music.get("albumArt") or playing_music.get("albumArtBig") or
                playing_music.get("artwork") or audio_info.get("albumUrl") or
                audio_info.get("albumArt") or audio_info.get("artwork")
            )
            info["media_type"] = "MUSIC"

        duration = music_state.get("duration", 0)
        if duration > 0:
            info["duration"] = duration / 1000
        position = music_state.get("position", 0)
        if position >= 0:
            info["position"] = position / 1000

        return info

    # Commands
    async def power_off(self) -> bool:
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setPowerOption?tag=poweroff", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Power off failed: %s", self.log_id, err)
            return False

    async def power_on(self) -> bool:
        mac_address = self._device_config.mac_address
        if not mac_address:
            _LOG.error("[%s] No MAC address for WakeOnLAN", self.log_id)
            return False
        try:
            mac_clean = mac_address.replace(":", "").replace("-", "")
            mac_bytes = bytes.fromhex(mac_clean)
            magic_packet = b'\xff' * 6 + mac_bytes * 16
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, ('<broadcast>', 9))
            sock.close()
            _LOG.info("[%s] WakeOnLAN sent to %s", self.log_id, mac_address)
            return True
        except Exception as err:
            _LOG.error("[%s] WakeOnLAN failed: %s", self.log_id, err)
            return False

    async def set_volume(self, volume: int) -> bool:
        music_state = self._state_data.get("music_control_state", {})
        max_volume = music_state.get("volumeData", {}).get("maxVolume", 100)
        device_volume = int((volume / 100) * max_volume)
        try:
            await self._api_request(
                f"/ZidooMusicControl/v2/setDevicesVolume?volume={device_volume}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set volume failed: %s", self.log_id, err)
            return False

    async def volume_up(self) -> bool:
        try:
            await self._api_request(
                "/ControlCenter/RemoteControl/sendkey?key=Key.VolumeUp", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Volume up failed: %s", self.log_id, err)
            return False

    async def volume_down(self) -> bool:
        try:
            await self._api_request(
                "/ControlCenter/RemoteControl/sendkey?key=Key.VolumeDown", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Volume down failed: %s", self.log_id, err)
            return False

    async def mute(self) -> bool:
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setMuteVolume?isMute=1", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Mute failed: %s", self.log_id, err)
            return False

    async def unmute(self) -> bool:
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setMuteVolume?isMute=0", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Unmute failed: %s", self.log_id, err)
            return False

    async def play_pause(self) -> bool:
        try:
            await self._api_request("/ZidooMusicControl/v2/playOrPause", parse_json=False)
            return True
        except Exception as err:
            _LOG.error("[%s] Play/pause failed: %s", self.log_id, err)
            return False

    async def next_track(self) -> bool:
        try:
            await self._api_request("/ZidooMusicControl/v2/playNext", parse_json=False)
            return True
        except Exception as err:
            _LOG.error("[%s] Next track failed: %s", self.log_id, err)
            return False

    async def previous_track(self) -> bool:
        try:
            await self._api_request("/ZidooMusicControl/v2/playLast", parse_json=False)
            return True
        except Exception as err:
            _LOG.error("[%s] Previous track failed: %s", self.log_id, err)
            return False

    async def seek(self, position: float) -> bool:
        position_ms = int(position * 1000)
        try:
            await self._api_request(
                f"/ZidooMusicControl/v2/seekTo?time={position_ms}", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Seek failed: %s", self.log_id, err)
            return False

    async def select_source(self, source: str) -> bool:
        tag = self._source_tags.get(source)
        if not tag:
            _LOG.error("[%s] Unknown source: %s", self.log_id, source)
            return False
        try:
            index = list(self._sources.keys()).index(tag)
            await self._api_request(
                f"/ZidooMusicControl/v2/setInputList?tag={tag}&index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Select source failed: %s", self.log_id, err)
            return False

    async def select_output(self, output: str) -> bool:
        tag = self._output_tags.get(output)
        if not tag:
            _LOG.error("[%s] Unknown output: %s", self.log_id, output)
            return False
        try:
            index = list(self._outputs.keys()).index(tag)
            await self._api_request(
                f"/ZidooMusicControl/v2/setOutInputList?tag={tag}&index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Select output failed: %s", self.log_id, err)
            return False

    async def select_output_by_tag(self, tag: str) -> bool:
        matched_tag = None
        for output_tag in self._outputs.keys():
            if output_tag.upper() == tag.upper():
                matched_tag = output_tag
                break
        if not matched_tag:
            _LOG.warning("[%s] Output tag '%s' not available (available: %s)",
                         self.log_id, tag, list(self._outputs.keys()))
            return False
        try:
            index = list(self._outputs.keys()).index(matched_tag)
            await self._api_request(
                f"/ZidooMusicControl/v2/setOutInputList?tag={matched_tag}&index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Select output by tag failed: %s", self.log_id, err)
            return False

    async def _fetch_and_store_mac_address(self, music_state: dict | None = None) -> None:
        try:
            mac = None
            if music_state:
                mac = music_state.get("deviceInfo", {}).get("net_mac")
            if not mac:
                device_model = await self.get_device_model()
                if device_model:
                    mac = device_model.get("net_mac")
            if mac:
                if self.update_config(mac_address=mac):
                    _LOG.info("[%s] MAC address persisted: %s", self.log_id, mac)
                else:
                    self._device_config.mac_address = mac
                    _LOG.info("[%s] MAC address captured (in-memory): %s", self.log_id, mac)
            else:
                _LOG.warning("[%s] Could not fetch MAC address", self.log_id)
        except Exception as err:
            _LOG.error("[%s] Failed to fetch MAC address: %s", self.log_id, err)

    # Display brightness
    async def get_display_brightness(self) -> int | None:
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getScreenBrightness"
            )
            return result.get("currentValue") if result else None
        except Exception as err:
            _LOG.error("[%s] Get display brightness failed: %s", self.log_id, err)
            return None

    async def set_display_brightness(self, brightness: int) -> bool:
        try:
            brightness = max(0, min(115, brightness))
            await self._api_request(
                f"/SystemSettings/displaySettings/setScreenBrightness?index={brightness}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set display brightness failed: %s", self.log_id, err)
            return False

    # Knob brightness
    async def get_knob_brightness(self) -> int | None:
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getKnobBrightness"
            )
            return result.get("currentValue") if result else None
        except Exception as err:
            _LOG.error("[%s] Get knob brightness failed: %s", self.log_id, err)
            return None

    async def set_knob_brightness(self, brightness: int) -> bool:
        try:
            brightness = max(0, min(255, brightness))
            await self._api_request(
                f"/SystemSettings/displaySettings/setKnobBrightness?index={brightness}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set knob brightness failed: %s", self.log_id, err)
            return False

    # VU/Spectrum modes
    async def _fetch_vu_modes(self) -> list[dict]:
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getVUModeList"
            )
            return result.get("data", []) if result else []
        except Exception as err:
            _LOG.error("[%s] Get VU modes failed: %s", self.log_id, err)
            return []

    async def set_vu_mode(self, index: int) -> bool:
        try:
            await self._api_request(
                f"/SystemSettings/displaySettings/setVUMode?index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set VU mode failed: %s", self.log_id, err)
            return False

    async def _fetch_spectrum_modes(self) -> list[dict]:
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getSpPlayModeList"
            )
            return result.get("data", []) if result else []
        except Exception as err:
            _LOG.error("[%s] Get spectrum modes failed: %s", self.log_id, err)
            return []

    async def set_spectrum_mode(self, index: int) -> bool:
        try:
            await self._api_request(
                f"/SystemSettings/displaySettings/setSpPlayModeList?index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set spectrum mode failed: %s", self.log_id, err)
            return False

    # Screen control
    async def turn_screen_on(self) -> bool:
        try:
            await self._api_request(
                "/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.ON",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Turn screen on failed: %s", self.log_id, err)
            return False

    async def turn_screen_off(self) -> bool:
        try:
            await self._api_request(
                "/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.OFF",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Turn screen off failed: %s", self.log_id, err)
            return False

    async def cycle_screen_mode(self, show_spectrum: bool = False) -> bool:
        try:
            await self._api_request(
                f"/ZidooMusicControl/v2/changVUDisplay?openType={int(show_spectrum)}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Cycle screen mode failed: %s", self.log_id, err)
            return False

    async def get_device_model(self) -> dict | None:
        try:
            result = await self._api_request("/ZidooControlCenter/getModel")
            return result if result else None
        except Exception as err:
            _LOG.error("[%s] Get device model failed: %s", self.log_id, err)
            return None

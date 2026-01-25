"""
Eversolo device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

import aiohttp
from ucapi_framework import DeviceEvents, PollingDevice

from intg_eversolo.config import EversoloConfig

_LOG = logging.getLogger(__name__)


class EversoloDevice(PollingDevice):
    """Eversolo device implementation using PollingDevice."""

    def __init__(self, device_config: EversoloConfig, **kwargs):
        # Eversolo devices are slow to respond - use 5 second poll interval
        super().__init__(device_config, poll_interval=5, **kwargs)
        self._device_config = device_config
        self._session: aiohttp.ClientSession | None = None
        self._state_data: dict[str, Any] = {}
        self._sources: dict[str, str] = {}
        self._source_tags: dict[str, str] = {}
        self._outputs: dict[str, str] = {}
        self._output_tags: dict[str, str] = {}

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
    def poll_interval(self) -> float:
        """Polling interval in seconds - Eversolo devices are slow, use 5s."""
        return 5.0

    @property
    def state_data(self) -> dict[str, Any]:
        """Current device state data."""
        return self._state_data

    @property
    def sources(self) -> dict[str, str]:
        """Available input sources {tag: name}."""
        return self._sources

    @property
    def outputs(self) -> dict[str, str]:
        """Available outputs {tag: name}."""
        return self._outputs

    async def _create_session(self) -> None:
        """Create HTTP session with proper timeout and connector configuration."""
        if not self._session:
            # Configure timeouts - Eversolo devices are VERY slow to respond
            timeout = aiohttp.ClientTimeout(
                total=60,      # Total timeout for entire request
                connect=20,    # Timeout for connection establishment
                sock_read=30   # Timeout for reading from socket
            )

            # Configure TCP connector for better reliability
            connector = aiohttp.TCPConnector(
                limit=10,                      # Max simultaneous connections
                force_close=False,             # Reuse connections
                enable_cleanup_closed=True     # Clean up closed connections
            )

            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )

    async def establish_connection(self) -> bool:
        """Establish connection to device - required by PollingDevice."""
        _LOG.info("[%s] Establishing connection to Eversolo device", self.log_id)

        try:
            await self._create_session()

            # First connection might take longer - use generous timeout
            music_state = await self._api_request(
                "/ZidooMusicControl/v2/getState", timeout=15.0
            )

            if music_state:
                _LOG.info("[%s] Connection established successfully", self.log_id)
                return True

            _LOG.error("[%s] Failed to establish connection - no response", self.log_id)
            return False

        except Exception as err:
            _LOG.error("[%s] Connection failed: %s", self.log_id, err)
            await self.close_connection()
            return False

    async def close_connection(self) -> None:
        """Close connection - required by PollingDevice."""
        if self._session:
            await self._session.close()
            # Wait for connector to close properly
            await asyncio.sleep(0.25)
            self._session = None

    async def _api_request(
        self, endpoint: str, parse_json: bool = True, timeout: float = 20.0
    ) -> Any:
        """Make API request to device."""
        if not self._session:
            await self._create_session()

        url = f"http://{self._device_config.host}:{self._device_config.port}{endpoint}"

        try:
            # Use per-request timeout to override session defaults
            request_timeout = aiohttp.ClientTimeout(total=timeout)
            async with self._session.get(url, timeout=request_timeout) as response:
                response.raise_for_status()

                if parse_json:
                    return await response.json(content_type=None)
                else:
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
        """Poll device for current state."""
        _LOG.debug("[%s] >>> Polling device (interval: %s seconds)", self.log_id, self.poll_interval)
        try:
            # Use longer timeout for polling - Eversolo devices are very slow
            music_state = await self._api_request("/ZidooMusicControl/v2/getState", timeout=30.0)
            input_output_state = await self._api_request(
                "/ZidooMusicControl/v2/getInputAndOutputList", timeout=30.0
            )

            self._state_data["music_control_state"] = music_state

            if input_output_state:
                self._state_data["input_output_state"] = input_output_state
                self._parse_sources(input_output_state)
                self._parse_outputs(input_output_state)

            _LOG.debug("[%s] >>> Emitting UPDATE event", self.log_id)
            self.events.emit(DeviceEvents.UPDATE, update={})
            _LOG.debug("[%s] >>> Poll completed successfully", self.log_id)

        except Exception as err:
            _LOG.debug("[%s] Poll error: %s", self.log_id, err, exc_info=True)

    def _parse_sources(self, input_output_state: dict) -> None:
        """Parse and store available sources."""
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
        """Parse and store available outputs (only enabled ones)."""
        outputs = input_output_state.get("outputData", [])
        self._outputs = {}
        self._output_tags = {}

        # Filter only enabled outputs
        for output in outputs:
            if output.get("enable") == 1:
                tag = output.get("tag", "").replace("/", "")
                name = output.get("name", "")
                if tag and name:
                    self._outputs[tag] = name
                    self._output_tags[name] = tag

    def get_volume(self) -> int | None:
        """Get current volume level (0-100 scale)."""
        music_state = self._state_data.get("music_control_state", {})
        volume_data = music_state.get("volumeData", {})

        current_volume = volume_data.get("currenttVolume")
        max_volume = volume_data.get("maxVolume")

        if current_volume is not None and max_volume and max_volume > 0:
            return int((current_volume / max_volume) * 100)

        return None

    def get_muted(self) -> bool:
        """Get current mute state."""
        music_state = self._state_data.get("music_control_state", {})
        volume_data = music_state.get("volumeData", {})
        return bool(volume_data.get("isMute", False))

    def get_state(self) -> str:
        """Get current playback state."""
        music_state = self._state_data.get("music_control_state", {})
        state = music_state.get("state", -1)

        if state == 0:
            return "IDLE"
        elif state == 3:
            return "PLAYING"
        elif state == 4:
            return "PAUSED"
        else:
            return "UNKNOWN"

    def get_current_source(self) -> str | None:
        """Get current input source name."""
        input_output_state = self._state_data.get("input_output_state", {})
        input_index = input_output_state.get("inputIndex", -1)

        if input_index >= 0 and input_index < len(self._sources):
            return list(self._sources.values())[input_index]

        return None

    def get_current_output(self) -> str | None:
        """Get current output name."""
        input_output_state = self._state_data.get("input_output_state", {})
        output_index = input_output_state.get("outputIndex", -1)

        if output_index >= 0 and output_index < len(self._outputs):
            return list(self._outputs.values())[output_index]

        return None

    def get_media_info(self) -> dict[str, Any]:
        """Get current media information."""
        music_state = self._state_data.get("music_control_state", {})
        play_type = music_state.get("playType", None)

        info = {
            "title": None,
            "artist": None,
            "album": None,
            "image_url": None,
            "duration": None,
            "position": None,
        }

        if play_type in [4, 6]:
            audio_info = (
                music_state.get("everSoloPlayInfo", {})
                .get("everSoloPlayAudioInfo", {})
            )
            info["title"] = audio_info.get("songName")
            info["artist"] = audio_info.get("artistName")
            info["album"] = audio_info.get("albumName")

        elif play_type == 5:
            playing_music = music_state.get("playingMusic", {})
            info["title"] = playing_music.get("title")
            info["artist"] = playing_music.get("artist")
            info["album"] = playing_music.get("album")

        duration = music_state.get("duration", 0)
        if duration > 0:
            info["duration"] = duration / 1000

        position = music_state.get("position", 0)
        if position > 0:
            info["position"] = position / 1000

        return info

    async def power_off(self) -> bool:
        """Power off the device."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setPowerOption?tag=poweroff",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Power off failed: %s", self.log_id, err)
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set volume (0-100 scale)."""
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
        """Increase volume."""
        try:
            await self._api_request(
                "/ZidooControlCenter/RemoteControl/sendkey?key=Key.VolumeUp",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Volume up failed: %s", self.log_id, err)
            return False

    async def volume_down(self) -> bool:
        """Decrease volume."""
        try:
            await self._api_request(
                "/ZidooControlCenter/RemoteControl/sendkey?key=Key.VolumeDown",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Volume down failed: %s", self.log_id, err)
            return False

    async def mute(self) -> bool:
        """Mute audio."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setMuteVolume?isMute=1", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Mute failed: %s", self.log_id, err)
            return False

    async def unmute(self) -> bool:
        """Unmute audio."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/setMuteVolume?isMute=0", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Unmute failed: %s", self.log_id, err)
            return False

    async def play_pause(self) -> bool:
        """Toggle play/pause."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/playOrPause", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Play/pause failed: %s", self.log_id, err)
            return False

    async def next_track(self) -> bool:
        """Skip to next track."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/playNext", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Next track failed: %s", self.log_id, err)
            return False

    async def previous_track(self) -> bool:
        """Skip to previous track."""
        try:
            await self._api_request(
                "/ZidooMusicControl/v2/playLast", parse_json=False
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Previous track failed: %s", self.log_id, err)
            return False

    async def seek(self, position: float) -> bool:
        """Seek to position in seconds."""
        position_ms = int(position * 1000)
        try:
            await self._api_request(
                f"/ZidooMusicControl/v2/seekTo?time={position_ms}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Seek failed: %s", self.log_id, err)
            return False

    async def select_source(self, source: str) -> bool:
        """Select input source by name."""
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
        """Select output by name."""
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

"""
Eversolo device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import socket
from typing import Any

import aiohttp
from ucapi_framework import DeviceEvents, PollingDevice

from intg_eversolo.config import EversoloConfig

_LOG = logging.getLogger(__name__)


class EversoloDevice(PollingDevice):
    """Eversolo device implementation using PollingDevice."""

    def __init__(self, device_config: EversoloConfig, **kwargs):
        # Eversolo devices are VERY slow to respond - use 20 second poll interval to prevent overwhelming device
        super().__init__(device_config, poll_interval=20, **kwargs)
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

    async def establish_connection(self) -> aiohttp.ClientSession:
        """Establish connection to device - required by PollingDevice."""
        _LOG.info("[%s] Establishing connection to Eversolo device", self.log_id)

        await self._create_session()

        # First connection might take longer - use generous timeout
        music_state = await self._api_request(
            "/ZidooMusicControl/v2/getState", timeout=15.0
        )

        _LOG.info("[%s] Connection established successfully", self.log_id)

        # Auto-capture MAC address for WakeOnLAN if not already stored
        if not self._device_config.mac_address:
            await self._fetch_and_store_mac_address(music_state)

        # CRITICAL: Poll immediately after connection to populate state and make entities available
        # Without this, entities stay UNAVAILABLE for poll_interval seconds (20s)
        _LOG.info("[%s] Performing initial device poll", self.log_id)
        await self.poll_device()

        return self._session

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
        """Poll device for current state - fetches ALL device data like HA integration."""
        _LOG.debug("[%s] >>> Polling device (interval: %s seconds)", self.log_id, 20)
        try:
            # Fetch core state data (matches HA integration's async_get_data)
            music_state = await self._api_request("/ZidooMusicControl/v2/getState", timeout=30.0)
            input_output_state = await self._api_request(
                "/ZidooMusicControl/v2/getInputAndOutputList", timeout=30.0
            )

            self._state_data["music_control_state"] = music_state

            if input_output_state:
                self._state_data["input_output_state"] = input_output_state
                self._parse_sources(input_output_state)
                self._parse_outputs(input_output_state)

            # Fetch brightness data for light entities (matches HA integration)
            display_brightness = await self.get_display_brightness()
            knob_brightness = await self.get_knob_brightness()

            if display_brightness is not None:
                self._state_data["display_brightness"] = display_brightness
            if knob_brightness is not None:
                self._state_data["knob_brightness"] = knob_brightness

            # Notify each entity with Panasonic pattern: emit(UPDATE, entity_id, attributes)
            # Framework routes these to specific entities
            _LOG.debug("[%s] >>> Notifying entities of state update", self.log_id)
            self._notify_entities()
            _LOG.debug("[%s] >>> Poll completed successfully", self.log_id)

        except Exception as err:
            _LOG.error("[%s] Poll error: %s", self.log_id, err, exc_info=True)

    def _notify_entities(self) -> None:
        """Notify entities of state changes - Panasonic pattern with entity_id and attributes."""
        from ucapi.media_player import Attributes as MediaAttributes, States as MediaStates
        from ucapi.sensor import Attributes as SensorAttributes, States as SensorStates
        from ucapi.light import Attributes as LightAttributes, States as LightStates
        from ucapi.button import Attributes as ButtonAttributes, States as ButtonStates

        # Media Player Entity
        media_player_id = f"media_player.{self.identifier}"
        volume = self.get_volume()
        state = self.get_state()

        if state == "IDLE":
            mp_state = MediaStates.IDLE
        elif state == "PLAYING":
            mp_state = MediaStates.PLAYING
        elif state == "PAUSED":
            mp_state = MediaStates.PAUSED
        else:
            mp_state = MediaStates.STANDBY

        media_info = self.get_media_info()
        media_player_attrs = {
            MediaAttributes.STATE: mp_state,
            MediaAttributes.VOLUME: volume if volume is not None else 0,
            MediaAttributes.MUTED: self.get_muted(),
            MediaAttributes.SOURCE: self.get_current_source() or "",
            MediaAttributes.SOURCE_LIST: list(self.sources.values()) if self.sources else [],
            MediaAttributes.MEDIA_TITLE: media_info["title"] or "",
            MediaAttributes.MEDIA_ARTIST: media_info["artist"] or "",
            MediaAttributes.MEDIA_ALBUM: media_info["album"] or "",
            MediaAttributes.MEDIA_IMAGE_URL: media_info["image_url"] or "",
            MediaAttributes.MEDIA_TYPE: media_info["media_type"] or "",
            MediaAttributes.MEDIA_DURATION: int(media_info["duration"]) if media_info["duration"] else 0,
            MediaAttributes.MEDIA_POSITION: int(media_info["position"]) if media_info["position"] else 0,
        }
        self.events.emit(DeviceEvents.UPDATE, media_player_id, media_player_attrs)

        # Sensor: State
        state_sensor_id = f"sensor.{self.identifier}.state"
        if state == "UNKNOWN":
            state_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.UNAVAILABLE,
                SensorAttributes.VALUE: "Unknown"
            }
        else:
            state_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.ON,
                SensorAttributes.VALUE: state
            }
        self.events.emit(DeviceEvents.UPDATE, state_sensor_id, state_sensor_attrs)

        # Sensor: Source
        source_sensor_id = f"sensor.{self.identifier}.source"
        current_source = self.get_current_source()
        if current_source:
            source_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.ON,
                SensorAttributes.VALUE: current_source
            }
        else:
            source_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.UNAVAILABLE,
                SensorAttributes.VALUE: "Unknown"
            }
        self.events.emit(DeviceEvents.UPDATE, source_sensor_id, source_sensor_attrs)

        # Sensor: Volume
        volume_sensor_id = f"sensor.{self.identifier}.volume"
        if volume is not None:
            volume_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.ON,
                SensorAttributes.VALUE: volume,
                SensorAttributes.UNIT: "%"
            }
        else:
            volume_sensor_attrs = {
                SensorAttributes.STATE: SensorStates.UNAVAILABLE,
                SensorAttributes.VALUE: 0,
                SensorAttributes.UNIT: "%"
            }
        self.events.emit(DeviceEvents.UPDATE, volume_sensor_id, volume_sensor_attrs)

        # Light: Display Brightness - convert from 0-115 to 0-255 scale
        display_light_id = f"light.{self.identifier}.display_brightness"
        display_brightness_115 = self._state_data.get("display_brightness", 0)
        display_brightness_255 = int((display_brightness_115 / 115) * 255) if display_brightness_115 > 0 else 0
        # Only send brightness - let framework derive state
        # Framework doesn't accept OFF state for dimmable lights
        display_light_attrs = {
            LightAttributes.BRIGHTNESS: display_brightness_255
        }
        _LOG.info("[%s] Display brightness: %d/115 -> %d/255",
                  self.log_id, display_brightness_115, display_brightness_255)
        self.events.emit(DeviceEvents.UPDATE, display_light_id, display_light_attrs)

        # Light: Knob Brightness - already in 0-255 scale
        knob_light_id = f"light.{self.identifier}.knob_brightness"
        knob_brightness = self._state_data.get("knob_brightness", 0)
        # Only send brightness - let framework derive state
        knob_light_attrs = {
            LightAttributes.BRIGHTNESS: knob_brightness
        }
        _LOG.info("[%s] Knob brightness: %d/255",
                  self.log_id, knob_brightness)
        self.events.emit(DeviceEvents.UPDATE, knob_light_id, knob_light_attrs)

        # Buttons: Output selection - always AVAILABLE when connected
        _LOG.info("[%s] Updating button entities. Available outputs: %s", self.log_id, self.outputs)
        for output_tag in self.outputs.keys():
            # Convert to lowercase to match entity IDs created in driver.py
            button_id = f"button.{self.identifier}.output_{output_tag.lower()}"
            button_attrs = {
                ButtonAttributes.STATE: ButtonStates.AVAILABLE
            }
            _LOG.info("[%s] Emitting button update: %s -> %s", self.log_id, button_id, button_attrs)
            self.events.emit(DeviceEvents.UPDATE, button_id, button_attrs)

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
        # NOTE: API returns boolean true/false, not integer 1/0
        for output in outputs:
            if output.get("enable") is True:
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
        """Get current media information with comprehensive field extraction."""
        music_state = self._state_data.get("music_control_state", {})
        play_type = music_state.get("playType", None)

        info = {
            "title": None,
            "artist": None,
            "album": None,
            "image_url": None,
            "media_type": None,
            "duration": None,
            "position": None,
        }

        # playType 4, 6, or 7: Local/Network/DLNA playback
        if play_type in [4, 6, 7]:
            audio_info = (
                music_state.get("everSoloPlayInfo", {})
                .get("everSoloPlayAudioInfo", {})
            )
            info["title"] = audio_info.get("songName")
            info["artist"] = audio_info.get("artistName")
            info["album"] = audio_info.get("albumName")
            # Try multiple image field names
            info["image_url"] = (
                audio_info.get("albumUrl") or
                audio_info.get("albumArt") or
                audio_info.get("artwork") or
                audio_info.get("coverArt") or
                audio_info.get("image") or
                audio_info.get("thumb")
            )
            info["media_type"] = "MUSIC"

        # playType 5: Streaming services
        elif play_type == 5:
            playing_music = music_state.get("playingMusic", {})
            info["title"] = playing_music.get("title")
            info["artist"] = playing_music.get("artist")
            info["album"] = playing_music.get("album")
            # Try multiple image field names
            info["image_url"] = (
                playing_music.get("albumArt") or
                playing_music.get("albumArtBig") or
                playing_music.get("artwork") or
                playing_music.get("image") or
                playing_music.get("thumb") or
                playing_music.get("coverUrl")
            )
            info["media_type"] = "MUSIC"

        # Unknown playType: Fallback extraction
        else:
            if play_type is not None:
                _LOG.debug(
                    "[%s] Unsupported playType: %s, attempting fallback extraction",
                    self.log_id, play_type
                )

            audio_info = (
                music_state.get("everSoloPlayInfo", {})
                .get("everSoloPlayAudioInfo", {})
            )
            playing_music = music_state.get("playingMusic", {})

            # Prefer playingMusic if available, otherwise use audio_info
            info["title"] = (
                playing_music.get("title") or
                audio_info.get("songName")
            )
            info["artist"] = (
                playing_music.get("artist") or
                audio_info.get("artistName")
            )
            info["album"] = (
                playing_music.get("album") or
                audio_info.get("albumName")
            )

            # Try image from both structures
            info["image_url"] = (
                playing_music.get("albumArt") or
                playing_music.get("albumArtBig") or
                playing_music.get("artwork") or
                audio_info.get("albumUrl") or
                audio_info.get("albumArt") or
                audio_info.get("artwork")
            )

            info["media_type"] = "MUSIC"  # Default assumption

        # Extract duration and position (common to all playTypes)
        duration = music_state.get("duration", 0)
        if duration > 0:
            info["duration"] = duration / 1000  # Convert ms to seconds

        position = music_state.get("position", 0)
        if position >= 0:  # Position can be 0, so check >= not >
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
                "/ControlCenter/RemoteControl/sendkey?key=Key.VolumeUp",
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
                "/ControlCenter/RemoteControl/sendkey?key=Key.VolumeDown",
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
    async def _fetch_and_store_mac_address(self, music_state: dict | None = None) -> None:
        """
        Fetch MAC address from API and store in config for WakeOnLAN.
        MAC is in: get_state().deviceInfo.net_mac or get_device_model().net_mac
        """
        try:
            # Try to get from provided music_state first
            if music_state:
                mac = music_state.get("deviceInfo", {}).get("net_mac")
                if mac:
                    self._device_config.set_mac_address(mac)
                    _LOG.info("[%s] MAC address auto-captured and stored: %s", self.log_id, mac)
                    return

            # If not in music_state, fetch device model
            device_model = await self.get_device_model()
            if device_model:
                mac = device_model.get("net_mac")
                if mac:
                    self._device_config.set_mac_address(mac)
                    _LOG.info("[%s] MAC address fetched from device model: %s", self.log_id, mac)
                    return

            _LOG.warning("[%s] Could not fetch MAC address from device", self.log_id)

        except Exception as err:
            _LOG.error("[%s] Failed to fetch MAC address: %s", self.log_id, err)

    async def power_on(self) -> bool:
        """Power on device via Wake-on-LAN."""
        mac_address = self._device_config.mac_address

        if not mac_address:
            _LOG.error("[%s] No MAC address available for WakeOnLAN", self.log_id)
            return False

        try:
            # Format MAC address (handle both : and - separators)
            mac_clean = mac_address.replace(":", "").replace("-", "")
            mac_bytes = bytes.fromhex(mac_clean)

            # Build magic packet: FF FF FF FF FF FF + MAC*16
            magic_packet = b'\xff' * 6 + mac_bytes * 16

            # Broadcast magic packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, ('<broadcast>', 9))
            sock.close()

            _LOG.info("[%s] WakeOnLAN packet sent to %s", self.log_id, mac_address)
            return True

        except Exception as err:
            _LOG.error("[%s] WakeOnLAN failed: %s", self.log_id, err)
            return False

    # Display Brightness Control
    async def get_display_brightness(self) -> int | None:
        """Get display brightness (0-115)."""
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getScreenBrightness"
            )
            if result and "currentIndex" in result:
                return result["currentIndex"]
            return None
        except Exception as err:
            _LOG.error("[%s] Get display brightness failed: %s", self.log_id, err)
            return None

    async def set_display_brightness(self, brightness: int) -> bool:
        """Set display brightness (0-115)."""
        try:
            # Clamp to valid range
            brightness = max(0, min(115, brightness))
            await self._api_request(
                f"/SystemSettings/displaySettings/setScreenBrightness?index={brightness}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set display brightness failed: %s", self.log_id, err)
            return False

    # Knob Brightness Control
    async def get_knob_brightness(self) -> int | None:
        """Get knob brightness (0-255)."""
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getKnobBrightness"
            )
            if result and "currentIndex" in result:
                return result["currentIndex"]
            return None
        except Exception as err:
            _LOG.error("[%s] Get knob brightness failed: %s", self.log_id, err)
            return None

    async def set_knob_brightness(self, brightness: int) -> bool:
        """Set knob brightness (0-255)."""
        try:
            # Clamp to valid range
            brightness = max(0, min(255, brightness))
            await self._api_request(
                f"/SystemSettings/displaySettings/setKnobBrightness?index={brightness}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set knob brightness failed: %s", self.log_id, err)
            return False

    # VU Mode Control
    async def get_vu_modes(self) -> list[dict]:
        """Get available VU meter modes."""
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getVUModeList"
            )
            return result.get("data", []) if result else []
        except Exception as err:
            _LOG.error("[%s] Get VU modes failed: %s", self.log_id, err)
            return []

    async def set_vu_mode(self, index: int) -> bool:
        """Set VU meter mode by index."""
        try:
            await self._api_request(
                f"/SystemSettings/displaySettings/setVUMode?index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set VU mode failed: %s", self.log_id, err)
            return False

    # Spectrum Mode Control
    async def get_spectrum_modes(self) -> list[dict]:
        """Get available spectrum analyzer modes."""
        try:
            result = await self._api_request(
                "/SystemSettings/displaySettings/getSpPlayModeList"
            )
            return result.get("data", []) if result else []
        except Exception as err:
            _LOG.error("[%s] Get spectrum modes failed: %s", self.log_id, err)
            return []

    async def set_spectrum_mode(self, index: int) -> bool:
        """Set spectrum analyzer mode by index."""
        try:
            await self._api_request(
                f"/SystemSettings/displaySettings/setSpPlayModeList?index={index}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Set spectrum mode failed: %s", self.log_id, err)
            return False

    # Screen Control
    async def turn_screen_on(self) -> bool:
        """Turn screen on explicitly."""
        try:
            await self._api_request(
                "/ControlCenter/RemoteControl/sendkey?key=Key.Screen.ON",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Turn screen on failed: %s", self.log_id, err)
            return False

    async def turn_screen_off(self) -> bool:
        """Turn screen off explicitly."""
        try:
            await self._api_request(
                "/ControlCenter/RemoteControl/sendkey?key=Key.Screen.OFF",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Turn screen off failed: %s", self.log_id, err)
            return False

    async def cycle_screen_mode(self, show_spectrum: bool = False) -> bool:
        """Cycle through VU/Spectrum display modes."""
        try:
            await self._api_request(
                f"/ZidooMusicControl/v2/changVUDisplay?openType={int(show_spectrum)}",
                parse_json=False,
            )
            return True
        except Exception as err:
            _LOG.error("[%s] Cycle screen mode failed: %s", self.log_id, err)
            return False

    # Device Info
    async def get_device_model(self) -> dict | None:
        """Get device model and info."""
        try:
            result = await self._api_request("/ZidooControlCenter/getModel")
            return result if result else None
        except Exception as err:
            _LOG.error("[%s] Get device model failed: %s", self.log_id, err)
            return None

    async def get_display_state(self) -> dict | None:
        """Get current display/power state."""
        try:
            result = await self._api_request("/ZidooMusicControl/v2/getPowerOption")
            return result if result else None
        except Exception as err:
            _LOG.error("[%s] Get display state failed: %s", self.log_id, err)
            return None

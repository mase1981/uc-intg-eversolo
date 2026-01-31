"""
Additional methods to add to EversoloDevice class.
These will be added to device.py at the end before the final closing.
"""

# Add these imports at the top of device.py:
# import socket

# Add these methods at the end of the EversoloDevice class (before the final closing):

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

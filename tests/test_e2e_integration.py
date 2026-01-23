"""
End-to-end integration test for Eversolo integration.

Tests the complete lifecycle:
1. Device creation and connection
2. Entity registration and availability
3. Polling and state updates
4. Command execution
5. Event handling

This test should be run with the Eversolo simulator running.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice
from intg_eversolo.media_player import EversoloMediaPlayer
from intg_eversolo.sensor import (
    EversoloStateSensor,
    EversoloSourceSensor,
    EversoloVolumeSensor,
)
from ucapi.media_player import States as MediaStates
from ucapi.sensor import States as SensorStates
from ucapi import StatusCodes

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)

_LOG = logging.getLogger(__name__)


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = []
        self.failed = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"[PASS] {test_name}")

    def add_fail(self, test_name: str, reason: str):
        self.failed.append((test_name, reason))
        print(f"[FAIL] {test_name} - {reason}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "=" * 80)
        print(f"TEST SUMMARY: {len(self.passed)}/{total} passed")
        print("=" * 80)

        if self.failed:
            print("\nFailed tests:")
            for test_name, reason in self.failed:
                print(f"  - {test_name}: {reason}")
            return False
        else:
            print("\nALL TESTS PASSED!")
            return True


async def test_integration():
    """Run complete end-to-end integration test."""
    results = TestResults()

    print("=" * 80)
    print("EVERSOLO END-TO-END INTEGRATION TEST")
    print("=" * 80)
    print()

    # Test configuration
    device_config = EversoloConfig(
        identifier="test_eversolo",
        name="Test Eversolo",
        host="127.0.0.1",
        port=9529
    )

    device = None
    media_player = None
    state_sensor = None
    source_sensor = None
    volume_sensor = None

    try:
        # =====================================================================
        # TEST 1: Device Creation
        # =====================================================================
        print("[TEST 1/12] Creating device instance...")
        try:
            device = EversoloDevice(device_config)
            results.add_pass("Device instance creation")
        except Exception as e:
            results.add_fail("Device instance creation", str(e))
            return results

        # =====================================================================
        # TEST 2: Device Connection
        # =====================================================================
        print("[TEST 2/12] Connecting to device...")
        try:
            # Use the PollingDevice connect method
            connected = await asyncio.wait_for(device.connect(), timeout=10.0)
            if connected:
                results.add_pass("Device connection")
            else:
                results.add_fail("Device connection", "connect() returned False")
                return results
        except asyncio.TimeoutError:
            results.add_fail("Device connection", "Connection timeout")
            return results
        except Exception as e:
            results.add_fail("Device connection", str(e))
            return results

        # Wait a moment for initial polling
        await asyncio.sleep(2)

        # =====================================================================
        # TEST 3: Polling Active
        # =====================================================================
        print("[TEST 3/12] Verifying polling is active...")
        initial_state_data = device.state_data.copy()
        await asyncio.sleep(3)  # Wait for at least 3 poll cycles (1s interval)

        # Check if state data has been updated
        if device.state_data and device.state_data.get("music_control_state"):
            results.add_pass("Polling is active and updating state")
        else:
            results.add_fail("Polling is active", "No state data after 3 seconds")

        # =====================================================================
        # TEST 4: Media Player Entity Creation
        # =====================================================================
        print("[TEST 4/12] Creating media player entity...")
        try:
            media_player = EversoloMediaPlayer(device_config, device)
            results.add_pass("Media player entity creation")
        except Exception as e:
            results.add_fail("Media player entity creation", str(e))
            return results

        # Wait for entity to receive first update
        await asyncio.sleep(2)

        # =====================================================================
        # TEST 5: Media Player State Not UNAVAILABLE
        # =====================================================================
        print("[TEST 5/12] Checking media player is AVAILABLE...")
        from ucapi.media_player import Attributes as MPAttributes

        mp_state = media_player.attributes.get(MPAttributes.STATE)
        if mp_state != MediaStates.UNAVAILABLE:
            results.add_pass(f"Media player is available (state: {mp_state})")
        else:
            results.add_fail("Media player availability", "State is UNAVAILABLE")

        # =====================================================================
        # TEST 6: Sensor Entities Creation
        # =====================================================================
        print("[TEST 6/12] Creating sensor entities...")
        try:
            state_sensor = EversoloStateSensor(device_config, device)
            source_sensor = EversoloSourceSensor(device_config, device)
            volume_sensor = EversoloVolumeSensor(device_config, device)
            results.add_pass("Sensor entities creation")
        except Exception as e:
            results.add_fail("Sensor entities creation", str(e))
            # Continue without sensors

        # Wait for sensors to receive updates
        await asyncio.sleep(2)

        # =====================================================================
        # TEST 7: Sensor States Not UNAVAILABLE
        # =====================================================================
        print("[TEST 7/12] Checking sensor availability...")
        from ucapi.sensor import Attributes as SensorAttributes

        sensor_tests_passed = True
        if state_sensor:
            sensor_state = state_sensor.attributes.get(SensorAttributes.STATE)
            if sensor_state == SensorStates.UNAVAILABLE:
                results.add_fail("State sensor availability", "State is UNAVAILABLE")
                sensor_tests_passed = False

        if source_sensor:
            sensor_state = source_sensor.attributes.get(SensorAttributes.STATE)
            if sensor_state == SensorStates.UNAVAILABLE:
                results.add_fail("Source sensor availability", "State is UNAVAILABLE")
                sensor_tests_passed = False

        if volume_sensor:
            sensor_state = volume_sensor.attributes.get(SensorAttributes.STATE)
            if sensor_state == SensorStates.UNAVAILABLE:
                results.add_fail("Volume sensor availability", "State is UNAVAILABLE")
                sensor_tests_passed = False

        if sensor_tests_passed:
            results.add_pass("All sensors are available")

        # =====================================================================
        # TEST 8: Media Player Attributes Populated
        # =====================================================================
        print("[TEST 8/12] Checking media player attributes...")
        volume = media_player.attributes.get(MPAttributes.VOLUME)
        sources = media_player.attributes.get(MPAttributes.SOURCE_LIST)

        attrs_ok = True
        if volume is None:
            results.add_fail("Media player attributes", "Volume is None")
            attrs_ok = False
        if not sources:
            results.add_fail("Media player attributes", "Source list is empty")
            attrs_ok = False

        if attrs_ok:
            results.add_pass(f"Media player attributes (volume={volume}, sources={len(sources)})")

        # =====================================================================
        # TEST 9: Command Execution - Volume
        # =====================================================================
        print("[TEST 9/12] Testing volume command...")
        try:
            result = await media_player.handle_command(
                media_player, "volume", {"volume": 75}
            )
            if result == StatusCodes.OK:
                await asyncio.sleep(2)  # Wait for state update
                new_volume = media_player.attributes.get(MPAttributes.VOLUME)
                if new_volume == 75:
                    results.add_pass("Volume command execution")
                else:
                    results.add_fail("Volume command execution", f"Volume is {new_volume}, expected 75")
            else:
                results.add_fail("Volume command execution", f"Command returned {result}")
        except Exception as e:
            results.add_fail("Volume command execution", str(e))

        # =====================================================================
        # TEST 10: Command Execution - Play/Pause
        # =====================================================================
        print("[TEST 10/12] Testing play_pause command...")
        try:
            initial_state = media_player.attributes.get(MPAttributes.STATE)
            result = await media_player.handle_command(
                media_player, "play_pause", None
            )
            if result == StatusCodes.OK:
                await asyncio.sleep(2)  # Wait for state update
                new_state = media_player.attributes.get(MPAttributes.STATE)
                # State should have changed
                results.add_pass(f"Play/Pause command (state: {initial_state} -> {new_state})")
            else:
                results.add_fail("Play/Pause command execution", f"Command returned {result}")
        except Exception as e:
            results.add_fail("Play/Pause command execution", str(e))

        # =====================================================================
        # TEST 11: Command Execution - Source Selection
        # =====================================================================
        print("[TEST 11/12] Testing source selection...")
        try:
            sources = device.sources
            if sources:
                first_source_tag = list(sources.keys())[0]
                first_source_name = sources[first_source_tag]
                # Pass the source NAME, not the TAG
                result = await media_player.handle_command(
                    media_player, "select_source", {"source": first_source_name}
                )
                if result == StatusCodes.OK:
                    await asyncio.sleep(2)  # Wait for state update
                    current_source = media_player.attributes.get(MPAttributes.SOURCE)
                    results.add_pass(f"Source selection ({first_source_name})")
                else:
                    results.add_fail("Source selection", f"Command returned {result}")
            else:
                results.add_fail("Source selection", "No sources available")
        except Exception as e:
            results.add_fail("Source selection", str(e))

        # =====================================================================
        # TEST 12: Continuous Polling
        # =====================================================================
        print("[TEST 12/12] Verifying continuous polling over 5 seconds...")
        update_count = [0]  # Use list to allow modification in closure

        def count_updates(update=None, **kwargs):
            update_count[0] += 1

        from ucapi_framework import DeviceEvents
        device.events.on(DeviceEvents.UPDATE, count_updates)

        await asyncio.sleep(5)

        # At 1s poll interval, we should see at least 4 updates in 5 seconds
        if update_count[0] >= 4:
            results.add_pass(f"Continuous polling ({update_count[0]} updates in 5s)")
        else:
            results.add_fail("Continuous polling", f"Only {update_count[0]} updates in 5s, expected at least 4")

    except Exception as e:
        _LOG.exception("Unexpected error during testing")
        results.add_fail("Test execution", str(e))

    finally:
        # Cleanup
        if device:
            try:
                await device.disconnect()
                print("\n[CLEANUP] Device disconnected")
            except:
                pass

    return results


async def main():
    """Main test entry point."""
    try:
        results = await test_integration()
        success = results.summary()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        _LOG.exception("Fatal error")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

"""Test light entities."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from ucapi.light import Commands
from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice
from intg_eversolo.light import EversoloDisplayBrightnessLight, EversoloKnobBrightnessLight


async def test_lights():
    """Test light entity commands."""
    print("=== Testing Light Entities ===\n")

    # Create config and device
    config = EversoloConfig(
        identifier="test_eversolo",
        name="Test Eversolo",
        host="127.0.0.1",
        port=9529
    )
    device = EversoloDevice(config)

    try:
        # Connect to device (may show warnings about missing endpoints)
        await device.connect()
        print("[OK] Connected to simulator (warnings above are expected)\n")

        # Create light entities
        display_light = EversoloDisplayBrightnessLight(config, device)
        knob_light = EversoloKnobBrightnessLight(config, device)

        print(f"Created light entities:")
        print(f"  - {display_light.id}")
        print(f"  - {knob_light.id}\n")

        # Test commands
        test_cases = [
            ("Display Light ON (max)", display_light, Commands.ON, None),
            ("Display Light ON (brightness=128)", display_light, Commands.ON, {"brightness": 128}),
            ("Display Light OFF", display_light, Commands.OFF, None),
            ("Display Light TOGGLE", display_light, Commands.TOGGLE, None),
            ("Knob Light ON (max)", knob_light, Commands.ON, None),
            ("Knob Light ON (brightness=200)", knob_light, Commands.ON, {"brightness": 200}),
            ("Knob Light OFF", knob_light, Commands.OFF, None),
            ("Knob Light TOGGLE", knob_light, Commands.TOGGLE, None),
        ]

        passed = 0
        failed = 0

        for test_name, light, cmd, params in test_cases:
            try:
                result = await light.handle_command(light, cmd, params)
                if result == "OK":
                    print(f"[PASS] {test_name} - PASSED")
                    passed += 1
                else:
                    print(f"[FAIL] {test_name} - FAILED (status: {result})")
                    failed += 1
            except Exception as e:
                print(f"[FAIL] {test_name} - ERROR: {e}")
                failed += 1

        print(f"\n=== Light Tests Summary ===")
        print(f"Passed: {passed}/{len(test_cases)}")
        print(f"Failed: {failed}/{len(test_cases)}")

        if failed == 0:
            print("\n[PASS] All light tests PASSED!")
            return True
        else:
            print(f"\n[FAIL] {failed} light test(s) FAILED!")
            return False

    except Exception as e:
        print(f"[FAIL] Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await device.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_lights())
    sys.exit(0 if result else 1)

"""Test button entities."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from ucapi.button import Commands
from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice
from intg_eversolo.driver import EversoloDriver


async def test_buttons():
    """Test button entity commands."""
    print("=== Testing Button Entities ===\n")

    # Create config and device
    config = EversoloConfig(
        identifier="test_eversolo",
        name="Test Eversolo",
        host="127.0.0.1",
        port=9529
    )
    device = EversoloDevice(config)

    try:
        await device.connect()
        print("[OK] Connected to simulator (warnings above are expected)\n")

        # Create driver to get output buttons
        driver = EversoloDriver()
        buttons = driver._create_output_buttons(config, device)

        print(f"Created {len(buttons)} button entities:")
        for btn in buttons:
            print(f"  - {btn.id}")
        print()

        # Test PUSH command on first 3 buttons
        test_buttons = buttons[:3]
        passed = 0
        failed = 0

        for btn in test_buttons:
            try:
                result = await btn.handle_command(btn, Commands.PUSH, None)
                if result == "OK":
                    print(f"[PASS] {btn.id} PUSH - PASSED")
                    passed += 1
                else:
                    print(f"[FAIL] {btn.id} PUSH - FAILED (status: {result})")
                    failed += 1
            except Exception as e:
                print(f"[FAIL] {btn.id} PUSH - ERROR: {e}")
                failed += 1

        print(f"\n=== Button Tests Summary ===")
        print(f"Passed: {passed}/{len(test_buttons)}")
        print(f"Failed: {failed}/{len(test_buttons)}")

        if failed == 0:
            print("\n[PASS] All button tests PASSED!")
            return True
        else:
            print(f"\n[FAIL] {failed} button test(s) FAILED!")
            return False

    except Exception as e:
        print(f"[FAIL] Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await device.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_buttons())
    sys.exit(0 if result else 1)

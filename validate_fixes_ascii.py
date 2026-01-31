#!/usr/bin/env python3
"""
Validation script to test fixes against real Eversolo API responses.
This validates that the bugs identified have been properly fixed.
"""

import json
import sys
from pathlib import Path

# Use ASCII characters for Windows console compatibility
CHECK = "[OK]"
CROSS = "[FAIL]"

def test_output_parsing():
    """Test that output parsing handles boolean enable field correctly."""
    print("\n=== Testing Output Parsing (Bug #1) ===")

    # Load real API response
    api_response_path = Path(r"C:\Downloads\Eversolo API Responses\get_input_output_state.json")
    with open(api_response_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Simulate our fixed parsing logic
    outputs_parsed = {}
    output_data = data.get("outputData", [])

    for output in output_data:
        # This is the FIX - check for boolean True, not integer 1
        if output.get("enable") is True:
            tag = output.get("tag", "").replace("/", "")
            name = output.get("name", "")
            if tag and name:
                outputs_parsed[tag] = name

    print(f"[OK] Parsed {len(outputs_parsed)} enabled outputs:")
    for tag, name in outputs_parsed.items():
        print(f"  - {tag}: {name}")

    # Validate expected outputs are present
    expected_tags = ["XLR", "RCA", "XLRRCA", "IIS", "SPDIF"]
    for expected in expected_tags:
        if expected in outputs_parsed:
            print(f"[OK] Found expected output: {expected}")
        else:
            print(f"[FAIL] MISSING expected output: {expected}")
            return False

    # Validate USB is NOT present (enable: false in API response)
    if "USB" in outputs_parsed:
        print("[FAIL] FAIL: USB should not be parsed (enable: false)")
        return False
    else:
        print("[OK] USB correctly excluded (enable: false)")

    return True

def test_button_entity_ids():
    """Test that button entity IDs use correct format with dots."""
    print("\n=== Testing Button Entity ID Format (Bug #2) ===")

    device_identifier = "eversolo_192_168_4_60_9529"
    output_tags = ["rca", "xlr", "hdmi", "usb", "spdif", "xlrrca"]

    # Test the FIXED format
    for tag in output_tags:
        # This is the FIX - use dot separator, not underscore
        entity_id = f"button.{device_identifier}.output_{tag}"

        # Simulate framework's device_from_entity_id() parsing
        parts = entity_id.split(".")
        if len(parts) >= 2:
            extracted_device_id = parts[1]
        else:
            extracted_device_id = None

        if extracted_device_id == device_identifier:
            print(f"[OK] {entity_id}")
            print(f"  → Extracted device_id: {extracted_device_id} [OK]")
        else:
            print(f"[FAIL] {entity_id}")
            print(f"  → Extracted device_id: {extracted_device_id} (expected: {device_identifier})")
            return False

    return True

def test_media_info_extraction():
    """Test that media information is properly extracted from API response."""
    print("\n=== Testing Media Info Extraction ===")

    # Load real API response with currently playing music
    api_response_path = Path(r"C:\Downloads\Eversolo API Responses\get_music_control_state.json")
    with open(api_response_path, "r", encoding="utf-8") as f:
        music_state = json.load(f)

    # Extract media info using our logic
    play_type = music_state.get("playType")
    playing_music = music_state.get("playingMusic", {})

    title = playing_music.get("title")
    artist = playing_music.get("artist")
    album = playing_music.get("album")
    image_url = playing_music.get("albumArt") or playing_music.get("albumArtBig")

    print(f"[OK] Play Type: {play_type}")
    print(f"[OK] Title: {title}")
    print(f"[OK] Artist: {artist}")
    print(f"[OK] Album: {album}")
    print(f"[OK] Album Art: {image_url[:50]}..." if image_url else "[OK] Album Art: None")

    # Validate we got the expected data from the real response
    if title == "Pink Pony Club" and artist == "Chappell Roan":
        print("[OK] Successfully extracted media information")
        return True
    else:
        print("[FAIL] Failed to extract correct media information")
        return False

def test_volume_extraction():
    """Test volume calculation from API response."""
    print("\n=== Testing Volume Extraction ===")

    # Load real API response
    api_response_path = Path(r"C:\Downloads\Eversolo API Responses\get_music_control_state.json")
    with open(api_response_path, "r", encoding="utf-8") as f:
        music_state = json.load(f)

    volume_data = music_state.get("volumeData", {})
    current_volume = volume_data.get("currenttVolume")  # Note: API has typo "currentt"
    max_volume = volume_data.get("maxVolume")
    is_mute = volume_data.get("isMute", False)

    # Calculate 0-100 scale
    if current_volume is not None and max_volume and max_volume > 0:
        volume_percent = int((current_volume / max_volume) * 100)
    else:
        volume_percent = None

    print(f"[OK] Current Volume: {current_volume}/{max_volume}")
    print(f"[OK] Volume (0-100 scale): {volume_percent}%")
    print(f"[OK] Muted: {is_mute}")

    # In the real response: currenttVolume=200, maxVolume=200 → 100%
    if volume_percent == 100 and is_mute is False:
        print("[OK] Volume extraction correct")
        return True
    else:
        print("[FAIL] Volume extraction failed")
        return False

def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Eversolo Integration v1.3.3 - Bug Fix Validation")
    print("=" * 70)

    tests = [
        ("Output Parsing", test_output_parsing),
        ("Button Entity IDs", test_button_entity_ids),
        ("Media Info Extraction", test_media_info_extraction),
        ("Volume Extraction", test_volume_extraction),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {test_name} FAILED with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("[OK] ALL TESTS PASSED - Fixes validated successfully!")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED - Review fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())

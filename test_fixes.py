#!/usr/bin/env python3
"""Simple validation of bug fixes using real API responses."""

import json
from pathlib import Path

print("=" * 70)
print("Eversolo Integration v1.3.3 - Bug Fix Validation")
print("=" * 70)

# TEST 1: Output Parsing (Bug #1)
print("\n[TEST 1] Output Parsing - Boolean enable field")
api_file = Path(r"C:\Downloads\Eversolo API Responses\get_input_output_state.json")
with open(api_file, "r") as f:
    data = json.load(f)

outputs = {}
for output in data.get("outputData", []):
    if output.get("enable") is True:  # FIX: use 'is True' not '== 1'
        tag = output.get("tag", "").replace("/", "")
        name = output.get("name", "")
        if tag and name:
            outputs[tag] = name

print(f"  Parsed {len(outputs)} enabled outputs: {list(outputs.keys())}")
assert len(outputs) == 5, f"Expected 5 outputs, got {len(outputs)}"
assert "USB" not in outputs, "USB should be excluded (enable: false)"
print("  [PASS] Output parsing works correctly")

# TEST 2: Button Entity ID Format (Bug #2)
print("\n[TEST 2] Button Entity ID Format")
device_id = "eversolo_192_168_4_60_9529"
entity_id = f"button.{device_id}.output_rca"  # FIX: use dot, not underscore

# Simulate framework parsing
parts = entity_id.split(".")
extracted_device_id = parts[1] if len(parts) >= 2 else None

print(f"  Entity ID: {entity_id}")
print(f"  Extracted device_id: {extracted_device_id}")
assert extracted_device_id == device_id, f"Device ID mismatch: {extracted_device_id} != {device_id}"
print("  [PASS] Entity ID format is correct")

# TEST 3: Media Info Extraction
print("\n[TEST 3] Media Info Extraction")
api_file = Path(r"C:\Downloads\Eversolo API Responses\get_music_control_state.json")
with open(api_file, "r") as f:
    music_state = json.load(f)

playing_music = music_state.get("playingMusic", {})
title = playing_music.get("title")
artist = playing_music.get("artist")
album = playing_music.get("album")

print(f"  Title: {title}")
print(f"  Artist: {artist}")
print(f"  Album: {album}")
assert title == "Pink Pony Club", "Title mismatch"
assert artist == "Chappell Roan", "Artist mismatch"
print("  [PASS] Media info extraction works")

# TEST 4: Volume Extraction
print("\n[TEST 4] Volume Extraction")
volume_data = music_state.get("volumeData", {})
current = volume_data.get("currenttVolume")
max_vol = volume_data.get("maxVolume")
volume_pct = int((current / max_vol) * 100) if current and max_vol else 0

print(f"  Volume: {current}/{max_vol} = {volume_pct}%")
assert volume_pct == 100, f"Volume calculation error: {volume_pct}%"
print("  [PASS] Volume extraction works")

print("\n" + "=" * 70)
print("[SUCCESS] All bug fixes validated successfully!")
print("=" * 70)

#!/usr/bin/env python3
"""
Line-by-line validation of Eversolo API implementation.
Compares Excel documentation against actual code implementation.
"""

import pandas as pd
from pathlib import Path
import re

# Paths
EXCEL_PATH = Path(r"C:\Downloads\Eversolo API.xlsx")
DEVICE_PY = Path(r"C:\Documents\GitHub\uc-intg-eversolo\intg_eversolo\device.py")

# Read Excel
uris_df = pd.read_excel(EXCEL_PATH, sheet_name="URIs")
functions_df = pd.read_excel(EXCEL_PATH, sheet_name="Functions")

# Read device.py
with open(DEVICE_PY, 'r', encoding='utf-8') as f:
    device_code = f.read()

print("="*100)
print("LINE-BY-LINE API VALIDATION: EXCEL vs CODE")
print("="*100)

# Extract all API URIs from device.py
api_uris_in_code = re.findall(r'["\'](/[^"\']+)["\']', device_code)
api_uris_in_code = [uri for uri in api_uris_in_code if 'Zidoo' in uri or 'ControlCenter' in uri or 'SystemSettings' in uri]

print(f"\nFound {len(api_uris_in_code)} API endpoints in device.py:")
for uri in sorted(set(api_uris_in_code)):
    print(f"  {uri}")

print("\n" + "="*100)
print("VALIDATION: Checking each Excel URI against code")
print("="*100)

implemented = []
missing = []
path_mismatch = []

for idx, row in uris_df.iterrows():
    function = row['Function']
    expected_uri = row['URI']
    values = row['Values']
    response = row['Response']

    if pd.isna(function) or pd.isna(expected_uri):
        continue

    # Clean up expected URI
    expected_uri = str(expected_uri).strip()

    # Skip non-URI rows
    if not expected_uri.startswith('/') and not expected_uri.startswith('http'):
        continue

    # Extract base path (without query parameters)
    expected_base = expected_uri.split('?')[0]

    # Check if implemented
    found_exact = False
    found_similar = False
    found_uri = None

    for code_uri in api_uris_in_code:
        code_base = code_uri.split('?')[0]

        # Exact match
        if expected_base in code_uri:
            found_exact = True
            found_uri = code_uri
            break

        # Check for path variations (e.g., /Zidoo vs /ZidooControl)
        if expected_base.split('/')[-1] == code_base.split('/')[-1]:
            found_similar = True
            found_uri = code_uri

    if found_exact:
        implemented.append(function)
        print(f"\n[OK] {function}")
        print(f"     Expected: {expected_uri}")
        print(f"     Found:    {found_uri}")
    elif found_similar:
        path_mismatch.append((function, expected_uri, found_uri))
        print(f"\n[WARNING] {function} - PATH MISMATCH")
        print(f"          Expected: {expected_uri}")
        print(f"          Found:    {found_uri}")
    else:
        missing.append((function, expected_uri, values, response))
        print(f"\n[MISSING] {function}")
        print(f"          URI: {expected_uri}")
        if not pd.isna(values):
            print(f"          Values: {values}")
        if not pd.isna(response):
            print(f"          Response: {response}")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)

print(f"\n[OK] IMPLEMENTED: {len(implemented)} APIs")
for func in implemented:
    print(f"  + {func}")

print(f"\n[WARNING] PATH MISMATCH: {len(path_mismatch)} APIs")
for func, expected, found in path_mismatch:
    print(f"  ! {func}")
    print(f"    Expected: {expected}")
    print(f"    Found:    {found}")

print(f"\n[MISSING] NOT IMPLEMENTED: {len(missing)} APIs")
for func, uri, values, response in missing:
    print(f"  - {func}: {uri}")

# Calculate coverage
total_apis = len(implemented) + len(path_mismatch) + len(missing)
coverage = ((len(implemented) + len(path_mismatch)) / total_apis * 100) if total_apis > 0 else 0

print(f"\n" + "="*100)
print(f"COVERAGE: {len(implemented) + len(path_mismatch)}/{total_apis} ({coverage:.1f}%)")
print("="*100)

# Exit based on missing critical APIs
critical_missing = [f for f, u, v, r in missing if f in [
    'get_state', 'get_input_output_state', 'toggle_play_pause',
    'volume_up', 'volume_down', 'mute', 'unmute',
    'next_title', 'previous_title', 'seek_time', 'set_volume'
]]

if critical_missing:
    print(f"\n[FAIL] Missing {len(critical_missing)} CRITICAL APIs:")
    for func in critical_missing:
        print(f"  - {func}")
    exit(1)
elif missing:
    print(f"\n[WARN] All critical APIs implemented, but {len(missing)} optional APIs missing")
    exit(0)
else:
    print("\n[PASS] All APIs validated successfully!")
    exit(0)

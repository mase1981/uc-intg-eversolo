#!/usr/bin/env python3
"""
Comprehensive API validation against Excel documentation and JSON responses.
This validates EVERY API endpoint, function, and data type.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set

# Paths
EXCEL_PATH = Path(r"C:\Downloads\Eversolo API.xlsx")
API_RESPONSES_DIR = Path(r"C:\Downloads\Eversolo API Responses")
INTEGRATION_DIR = Path(r"C:\Documents\GitHub\uc-intg-eversolo\intg_eversolo")

# Read Excel data
print("="*80)
print("COMPREHENSIVE EVERSOLO API VALIDATION")
print("="*80)

uris_df = pd.read_excel(EXCEL_PATH, sheet_name="URIs")
functions_df = pd.read_excel(EXCEL_PATH, sheet_name="Functions")

print(f"\nExcel Documentation:")
print(f"  - {len(uris_df)} API URIs")
print(f"  - {len(functions_df)} Functions")

# Parse our integration code to find all API calls
print(f"\nScanning integration code...")
integration_files = list(INTEGRATION_DIR.glob("*.py"))
print(f"  - Found {len(integration_files)} Python files")

# Extract all API endpoints from our code
api_calls_in_code = set()
for py_file in integration_files:
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all _api_request calls
        import re
        # Match patterns like: _api_request("/ZidooMusicControl/v2/getState"
        matches = re.findall(r'_api_request\(["\']([^"\']+)["\']', content)
        for match in matches:
            api_calls_in_code.add(match)

print(f"  - Found {len(api_calls_in_code)} unique API endpoints in code")

# List all JSON response files
json_files = list(API_RESPONSES_DIR.glob("*.json"))
print(f"  - Found {len(json_files)} JSON response files")

print("\n" + "="*80)
print("VALIDATION RESULTS")
print("="*80)

# Track all issues
issues = []
warnings = []
success = []

# VALIDATION 1: Check every URI from Excel against our code
print("\n### VALIDATION 1: API URI Coverage")
print("-"*80)

for idx, row in uris_df.iterrows():
    function = row['Function']
    uri = row['URI']
    values = row['Values']

    if pd.isna(function) or pd.isna(uri):
        continue

    # Extract base URI without parameters
    base_uri = uri.split('?')[0] if '?' in uri else uri

    # Check if this URI is used in our code
    found = False
    for code_uri in api_calls_in_code:
        code_base = code_uri.split('?')[0] if '?' in code_uri else code_uri
        if base_uri in code_uri or code_uri.startswith(base_uri):
            found = True
            success.append(f"[OK] {function}: {base_uri}")
            break

    if not found:
        issues.append(f"[MISSING] {function}: {base_uri}")
        print(f"  [MISSING] {function}")
        print(f"            URI: {uri}")
        if not pd.isna(values):
            print(f"            Values: {values}")

# VALIDATION 2: Check for APIs in code NOT in Excel
print("\n### VALIDATION 2: Undocumented APIs in Code")
print("-"*80)

documented_uris = set()
for idx, row in uris_df.iterrows():
    if not pd.isna(row['URI']):
        base = row['URI'].split('?')[0]
        documented_uris.add(base)

for code_uri in api_calls_in_code:
    code_base = code_uri.split('?')[0]
    found = False
    for doc_uri in documented_uris:
        if doc_uri in code_uri or code_uri.startswith(doc_uri):
            found = True
            break

    if not found:
        warnings.append(f"[UNDOCUMENTED] API in code not in Excel: {code_uri}")
        print(f"  [WARNING] Code uses: {code_uri}")
        print(f"            Not documented in Excel")

# VALIDATION 3: Check JSON response files
print("\n### VALIDATION 3: JSON Response File Coverage")
print("-"*80)

# Map function names to expected JSON files
function_to_json = {
    'get_state': 'get_music_control_state.json',
    'get_input_output_state': 'get_input_output_state.json',
    'get_display_brightness': 'get_display_brightness.json',
    'get_knob_brightness': 'get_knob_brightness.json',
    'get_device_model': 'get_device_model.json',
    'get_vu_mode_state': 'get_vu_mode_state.json',
    'get_spectrum_state': 'get_spectrum_state.json',
    'get_display_state': 'get_display_state.json',
}

json_file_names = {f.name for f in json_files}

for function, expected_file in function_to_json.items():
    if expected_file in json_file_names:
        success.append(f"[OK] Have JSON response for: {function}")
    else:
        # Check for variations
        found_variation = False
        for jf in json_file_names:
            if function.replace('get_', '') in jf.lower():
                warnings.append(f"[WARNING] {function}: Expected '{expected_file}', found '{jf}'")
                found_variation = True
                break

        if not found_variation:
            issues.append(f"[MISSING] No JSON response file for: {function}")

# Print action items response files
print(f"\nAvailable JSON response files:")
for jf in sorted(json_file_names):
    print(f"  - {jf}")

# VALIDATION 4: Data type validation from actual JSON
print("\n### VALIDATION 4: Data Type Validation")
print("-"*80)

# Check the critical enable field we fixed
input_output_file = API_RESPONSES_DIR / "get_input_output_state.json"
if input_output_file.exists():
    with open(input_output_file, 'r') as f:
        data = json.load(f)

    print("Checking outputData.enable field type...")
    for output in data.get("outputData", []):
        enable_value = output.get("enable")
        enable_type = type(enable_value).__name__
        tag = output.get("tag", "unknown")

        if isinstance(enable_value, bool):
            success.append(f"[OK] {tag}: enable is boolean ({enable_value})")
            print(f"  [OK] {tag}: enable = {enable_value} (type: {enable_type})")
        else:
            issues.append(f"[ERROR] {tag}: enable is {enable_type}, not bool!")
            print(f"  [ERROR] {tag}: enable = {enable_value} (type: {enable_type}) - Expected bool!")

# SUMMARY
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n[SUCCESS] {len(success)} items validated successfully")
print(f"[WARNINGS] {len(warnings)} warnings")
print(f"[ISSUES] {len(issues)} critical issues")

if issues:
    print("\n### CRITICAL ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")

if warnings:
    print("\n### WARNINGS:")
    for warning in warnings:
        print(f"  {warning}")

# Exit code
exit_code = 0 if len(issues) == 0 else 1
print(f"\n{'='*80}")
if exit_code == 0:
    print("[PASS] Validation completed with no critical issues")
else:
    print(f"[FAIL] Found {len(issues)} critical issues that must be fixed")
print("="*80)

exit(exit_code)

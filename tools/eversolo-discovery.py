#!/usr/bin/env python3
"""
Eversolo Device Discovery Script - Standalone Version
No external dependencies required (Python 3.7+ standard library only).

Discovers ALL device capabilities for comprehensive remote entity mapping.

Usage:
    python eversolo-discovery.py <device_ip>

Example:
    python eversolo-discovery.py 192.168.60.55

Author: Meir Miyara
Email: meir.miyara@gmail.com
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Optional

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_info(msg: str):
    """Print info message in yellow."""
    print(f"{Colors.YELLOW}ℹ{Colors.RESET} {msg}")

def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")

def fetch_json(url: str, timeout: int = 30) -> tuple[Optional[Any], int]:
    """Fetch JSON from URL using built-in urllib."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            return json.loads(data), response.getcode()
    except urllib.error.HTTPError as e:
        return None, e.code
    except urllib.error.URLError as e:
        return None, -1
    except json.JSONDecodeError:
        return None, -2
    except Exception as e:
        return None, -3

def test_endpoint(base_url: str, endpoint: str, description: str) -> tuple[Optional[Any], int]:
    """Test an API endpoint and print result."""
    url = f"{base_url}{endpoint}"
    print(f"  Testing: {description}")
    print(f"    URL: {endpoint}")
    data, status = fetch_json(url)

    if status == 200 and data:
        print_success(f"Response OK (status {status})")
        return data, status
    elif status == 404:
        print_info(f"Endpoint not found (404) - feature not supported")
        return None, status
    else:
        print_error(f"Failed (status {status})")
        return None, status

def discover_eversolo_device(host: str, port: int = 9529) -> dict[str, Any]:
    """Comprehensive discovery of Eversolo device capabilities."""

    print_section(f"EVERSOLO DEVICE DISCOVERY: {host}:{port}")

    report = {
        "discovery_info": {
            "host": host,
            "port": port,
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.0.0"
        },
        "device_info": {},
        "model_info": {},
        "capabilities": {
            "inputs": [],
            "outputs": [],
            "brightness": {},
            "display_modes": {},
            "remote_controls": {},
            "media_controls": {}
        },
        "api_endpoints": {},
        "test_results": {},
        "errors": []
    }

    base_url = f"http://{host}:{port}"

    # ========================================
    # 1. DEVICE MODEL & INFO
    # ========================================
    print_section("1. DEVICE MODEL & INFORMATION")

    data, status = test_endpoint(base_url, "/ZidooControlCenter/getModel", "Device Model")
    if data:
        report["model_info"] = data
        model = data.get("model", "Unknown")
        print(f"    Model: {Colors.BOLD}{model}{Colors.RESET}")
        print(f"    MAC: {data.get('net_mac', 'Unknown')}")
        print(f"    Firmware: {data.get('version', 'Unknown')}")

    # ========================================
    # 2. DEVICE STATE
    # ========================================
    print_section("2. DEVICE STATE")

    data, status = test_endpoint(base_url, "/ZidooMusicControl/v2/getState", "Music Control State")
    if data:
        report["device_info"]["music_state"] = data
        state = data.get("status", "Unknown")
        print(f"    Playback State: {state}")
        print(f"    Volume: {data.get('volumeData', {}).get('currenttVolume', 'Unknown')}")

    # ========================================
    # 3. INPUTS & OUTPUTS
    # ========================================
    print_section("3. INPUTS & OUTPUTS DISCOVERY")

    data, status = test_endpoint(base_url, "/ZidooMusicControl/v2/getInputAndOutputList", "Input/Output List")
    if data:
        # Parse Inputs
        input_data = data.get("inputData", [])
        report["capabilities"]["inputs"] = input_data
        print(f"\n  📥 INPUTS ({len(input_data)} found):")
        for inp in input_data:
            enabled = "✓" if not inp.get("isEdit", False) else "⚙"
            print(f"    {enabled} {inp.get('name'):20s} → Tag: {inp.get('tag')}")

        # Parse Outputs
        output_data = data.get("outputData", [])
        report["capabilities"]["outputs"] = output_data
        print(f"\n  📤 OUTPUTS ({len(output_data)} found):")
        for out in output_data:
            enabled = "✓" if out.get("enable", False) else "✗"
            print(f"    {enabled} {out.get('name'):20s} → Tag: {out.get('tag')}")

        # Current selections
        print(f"\n  Current Input Index: {data.get('inputIndex', -1)}")
        print(f"  Current Output Index: {data.get('outputIndex', -1)}")

    # ========================================
    # 4. BRIGHTNESS CONTROLS
    # ========================================
    print_section("4. BRIGHTNESS CONTROLS")

    # Display Brightness
    data, status = test_endpoint(base_url, "/SystemSettings/displaySettings/getScreenBrightness", "Display Brightness")
    if data:
        report["capabilities"]["brightness"]["display"] = data
        print(f"    Current: {data.get('currentValue', 'Unknown')}")
        print(f"    Range: {data.get('minValue', 0)} - {data.get('maxValue', 115)}")

    # Knob Brightness
    data, status = test_endpoint(base_url, "/SystemSettings/displaySettings/getKnobBrightness", "Knob Brightness")
    if data:
        report["capabilities"]["brightness"]["knob"] = data
        print(f"    Current: {data.get('currentValue', 'Unknown')}")
        print(f"    Range: {data.get('minValue', 0)} - {data.get('maxValue', 255)}")
        report["capabilities"]["brightness"]["knob_supported"] = True
    else:
        report["capabilities"]["brightness"]["knob_supported"] = False

    # ========================================
    # 5. DISPLAY MODES
    # ========================================
    print_section("5. DISPLAY MODES")

    # VU Meter Modes
    data, status = test_endpoint(base_url, "/SystemSettings/displaySettings/getVUModeList", "VU Meter Modes")
    if data:
        modes = data.get("data", [])
        report["capabilities"]["display_modes"]["vu_modes"] = modes
        print(f"  📊 VU Modes ({len(modes)} available):")
        for mode in modes:
            print(f"    • {mode.get('name', 'Unknown')} (Index: {mode.get('index', -1)})")

    # Spectrum Analyzer Modes
    data, status = test_endpoint(base_url, "/SystemSettings/displaySettings/getSpPlayModeList", "Spectrum Modes")
    if data:
        modes = data.get("data", [])
        report["capabilities"]["display_modes"]["spectrum_modes"] = modes
        print(f"  📈 Spectrum Modes ({len(modes)} available):")
        for mode in modes:
            print(f"    • {mode.get('name', 'Unknown')} (Index: {mode.get('index', -1)})")

    # ========================================
    # 6. REMOTE CONTROL KEYS TEST
    # ========================================
    print_section("6. REMOTE CONTROL KEYS (NON-INTRUSIVE)")

    print_info("Testing remote control key endpoints (read-only checks)")

    # Test key endpoints (without actually sending)
    remote_keys_to_test = [
        ("Key.Screen.ON", "Screen On"),
        ("Key.Screen.OFF", "Screen Off"),
        ("Key.VolumeUp", "Volume Up"),
        ("Key.VolumeDown", "Volume Down"),
        ("Key.Play", "Play"),
        ("Key.Pause", "Pause"),
        ("Key.Stop", "Stop"),
        ("Key.Next", "Next Track"),
        ("Key.Previous", "Previous Track"),
    ]

    report["capabilities"]["remote_controls"]["available_keys"] = []

    for key, description in remote_keys_to_test:
        # Just check endpoint structure - don't actually send
        endpoint = f"/ZidooControlCenter/RemoteControl/sendkey?key={key}"
        report["capabilities"]["remote_controls"]["available_keys"].append({
            "key": key,
            "description": description,
            "endpoint": endpoint
        })
        print(f"    • {description:20s} → {key}")

    # ========================================
    # 7. POWER OPTIONS
    # ========================================
    print_section("7. POWER & DISPLAY OPTIONS")

    data, status = test_endpoint(base_url, "/ZidooMusicControl/v2/getPowerOption", "Power Options")
    if data:
        report["capabilities"]["power_options"] = data
        options = data.get("data", [])
        print(f"  Power Options ({len(options)} available):")
        for opt in options:
            print(f"    • {opt.get('name', 'Unknown')} (Tag: {opt.get('tag', 'Unknown')})")

    data, status = test_endpoint(base_url, "/SystemSettings/displaySettings/getDisplayState", "Display State")
    if data:
        report["capabilities"]["display_state"] = data

    # ========================================
    # 8. AUDIO SETTINGS
    # ========================================
    print_section("8. AUDIO SETTINGS")

    # XLR Output Options
    data, status = test_endpoint(base_url, "/SystemSettings/audioSettings/getXlrOutputOption", "XLR Output Settings")
    if data:
        report["capabilities"]["audio_settings"] = report["capabilities"].get("audio_settings", {})
        report["capabilities"]["audio_settings"]["xlr"] = data

    # Subwoofer Settings
    data, status = test_endpoint(base_url, "/SystemSettings/audioSettings/getSubOutputOption", "Subwoofer Settings")
    if data:
        report["capabilities"]["audio_settings"] = report["capabilities"].get("audio_settings", {})
        report["capabilities"]["audio_settings"]["subwoofer"] = data

    # ========================================
    # 9. FEATURE DETECTION SUMMARY
    # ========================================
    print_section("9. FEATURE DETECTION SUMMARY")

    features = {
        "Model": report.get("model_info", {}).get("model", "Unknown"),
        "Knob Brightness": report["capabilities"]["brightness"].get("knob_supported", False),
        "VU Modes": len(report["capabilities"]["display_modes"].get("vu_modes", [])) > 0,
        "Spectrum Modes": len(report["capabilities"]["display_modes"].get("spectrum_modes", [])) > 0,
        "Input Count": len(report["capabilities"]["inputs"]),
        "Output Count": len(report["capabilities"]["outputs"]),
        "Enabled Outputs": len([o for o in report["capabilities"]["outputs"] if o.get("enable", False)])
    }

    print("\n  Detected Features:")
    for feature, value in features.items():
        status_icon = "✓" if value else "✗"
        print(f"    {status_icon} {feature}: {value}")

    # ========================================
    # 10. OUTPUT MAPPING FOR REMOTE ENTITY
    # ========================================
    print_section("10. REMOTE ENTITY BUTTON MAPPING")

    enabled_outputs = [o for o in report["capabilities"]["outputs"] if o.get("enable", False)]

    print(f"\n  Recommended Output Buttons for Remote Entity:")
    print(f"  {'Button Text':<15} {'Command ID':<20} {'API Tag':<15} {'Supported'}")
    print(f"  {'-'*70}")

    output_button_map = {
        "RCA": ("RCA", "OUTPUT_RCA"),
        "XLR": ("XLR", "OUTPUT_XLR"),
        "HDMI": ("HDMI", "OUTPUT_HDMI"),
        "USB": ("USB DAC", "OUTPUT_USB"),
        "SPDIF": ("OPT/COAX", "OUTPUT_SPDIF"),
        "XLRRCA": ("XLR/RCA", "OUTPUT_XLRRCA"),
        "IIS": ("IIS", "OUTPUT_IIS"),
    }

    enabled_tags = [o.get("tag") for o in enabled_outputs]
    report["capabilities"]["remote_entity_buttons"] = {}

    for tag, (button_text, cmd_id) in output_button_map.items():
        supported = tag in enabled_tags
        icon = "✓" if supported else "✗"
        print(f"  {button_text:<15} {cmd_id:<20} {tag:<15} {icon}")
        report["capabilities"]["remote_entity_buttons"][cmd_id] = {
            "text": button_text,
            "tag": tag,
            "supported": supported
        }

    # ========================================
    # SAVE REPORT
    # ========================================
    print_section("SAVING DISCOVERY REPORT")

    model_name = report.get("model_info", {}).get("model", "unknown").replace(" ", "_")
    filename = f"eversolo_discovery_{model_name}_{host.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_success(f"Report saved to: {filename}")
        print(f"\n  {Colors.BOLD}Next Steps:{Colors.RESET}")
        print(f"  1. Send this JSON file to the integration developer")
        print(f"  2. Repeat discovery for other Eversolo models (A6, A8, etc.)")
        print(f"  3. Integration will use this data for model-specific remote entities")
    except Exception as e:
        print_error(f"Failed to save report: {e}")
        return report

    print_section("DISCOVERY COMPLETE!")
    print(f"\n  Summary:")
    print(f"    Device: {features['Model']}")
    print(f"    Total Inputs: {features['Input Count']}")
    print(f"    Total Outputs: {features['Output Count']}")
    print(f"    Enabled Outputs: {features['Enabled Outputs']}")
    print(f"    Errors: {len(report['errors'])}")

    return report

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Error: Missing device IP address{Colors.RESET}")
        print(f"\nUsage: {sys.argv[0]} <device_ip> [port]")
        print(f"Example: {sys.argv[0]} 192.168.60.55")
        print(f"Example: {sys.argv[0]} 192.168.60.31 9529")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9529

    try:
        report = discover_eversolo_device(host, port)

        if report["errors"]:
            print(f"\n{Colors.YELLOW}⚠ Discovery completed with {len(report['errors'])} error(s):{Colors.RESET}")
            for error in report["errors"]:
                print(f"  • {error}")

        sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Discovery cancelled by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

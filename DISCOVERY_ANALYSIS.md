# Eversolo Model Discovery Analysis

## Summary

Complete capability analysis of DMP-A6 and DMP-A10 based on API discovery scripts.

**Discovery Date:** 2026-01-31
**Firmware Version:** v1.5.46 (both models)

---

## 🔍 Critical Differences

| Feature | DMP-A10 | DMP-A6 | Notes |
|---------|---------|--------|-------|
| **Model Type** | DAC/Preamp | Music Streamer | A10 is pure DAC, A6 has HDMI |
| **HDMI Output** | ❌ NO | ✅ YES | A6 only! |
| **Enabled Outputs** | 4 | 5 | A6 has additional HDMI |
| **Input Count** | 11 | 6 | A10 has duplicate inputs |
| **Knob Brightness** | API exists, **doesn't work** | ✅ Works | Hardware limitation on A10 |
| **DSP Settings** | ✅ Yes (`hasDspSetting: true`) | ❌ No | A10 only |
| **Subwoofer Settings** | ✅ Yes (`hasSubSetting: true`) | ❌ No | A10 only |
| **EQ Settings** | ❌ No | ✅ Yes | A6 only |

---

## 📤 Output Comparison

### DMP-A10 Enabled Outputs
```json
[
  {"name": "BAL-XLR", "tag": "XLR", "enable": true},
  {"name": "Analog-RCA", "tag": "RCA", "enable": true},
  {"name": "XLR/RCA", "tag": "XLRRCA", "enable": true},
  {"name": "OPT/COAX", "tag": "SPDIF", "enable": true},
  {"name": "USB DAC", "tag": "USB", "enable": false}
]
```
**Total Enabled:** 4

### DMP-A6 Enabled Outputs
```json
[
  {"name": "BAL-XLR", "tag": "XLR", "enable": true},
  {"name": "Analog-RCA", "tag": "RCA", "enable": true},
  {"name": "XLR/RCA", "tag": "XLRRCA", "enable": true},
  {"name": "HDMI", "tag": "HDMI", "enable": true},
  {"name": "OPT/COAX", "tag": "SPDIF", "enable": true},
  {"name": "USB DAC", "tag": "USB", "enable": false}
]
```
**Total Enabled:** 5

### Output Button Recommendations

**Common Outputs (Both Models):**
- ✅ RCA (Analog-RCA)
- ✅ XLR (BAL-XLR)
- ✅ XLR/RCA (Combined)
- ✅ OPT/COAX (SPDIF)

**A6 Only:**
- ✅ HDMI

**Not Supported:**
- ❌ USB DAC (disabled on both - requires USB device connected)
- ❌ IIS (doesn't exist on either model)

---

## 📥 Input Comparison

### DMP-A10 Inputs (11 total)
- Internal player
- Bluetooth In
- USB-B In
- **Optical 1 In** (tag: SPDIF)
- **Optical 2 In** (tag: SPDIF1)
- **Coaxial 1 In** (tag: RCA)
- **Coaxial 2 In** (tag: RCA0)
- ARC In (tag: EARC)
- **RCA 1 In** (tag: RCA_A)
- **RCA 2 In** (tag: RCA_A2)
- **XLR In** (tag: XLR_A)

### DMP-A6 Inputs (6 total)
- Internal player
- Bluetooth In
- USB-B In
- **Optical In** (tag: SPDIF)
- **Coaxial In** (tag: RCA)
- ARC In (tag: EARC)

**Note:** A10 has duplicate digital inputs (2x Optical, 2x Coaxial) and analog inputs (2x RCA, 1x XLR).

---

## 🎛️ Brightness Controls

### Display Brightness
- **Both Models:** ✅ Supported
- **Range:** 0-115
- **API:** `/SystemSettings/displaySettings/getScreenBrightness`
- **Set:** `/SystemSettings/displaySettings/setScreenBrightness?index=X`

### Knob Brightness
| Model | API Response | Actual Behavior |
|-------|--------------|-----------------|
| **DMP-A10** | ✅ Returns 200 | ❌ **No visual change** (hardware limitation) |
| **DMP-A6** | ✅ Returns 200 | ✅ **Works correctly** |

**Conclusion:** A10 API accepts knob brightness commands but hardware doesn't support it (DAC model has no knob LED).

---

## 🎨 Display Modes

### VU Meter Modes
- **A10:** 14 modes (index 0-13)
- **A6:** 13 modes (index 0-12)

### Spectrum Modes
- **Both:** 4 modes (index 0-3)

---

## 🎮 Remote Control Keys

**Common Keys (Both Models):**
```
Key.Screen.ON
Key.Screen.OFF
Key.VolumeUp
Key.VolumeDown
Key.Play
Key.Pause
Key.Stop
Key.Next
Key.Previous
```

**Endpoint:** `/ZidooControlCenter/RemoteControl/sendkey?key=<KEY>`

---

## 🔊 Audio Settings

### XLR Output Options (Both Models)
- DAC filter characteristics
- Volume balance
- Startup volume
- Volume step
- Volume protection
- Volume limit
- Volume passthrough mode
- XLR port polarity

### Subwoofer Settings (A10 Only)
- Sub ON/OFF
- Mode (Mixer/Crossover)
- Level (-15 to +15 dB)
- Crossover point (40-500Hz)
- Subwoofer delay
- Phase (0°/180°)

---

## 💡 Implementation Recommendations

### 1. Model Detection
```python
# Auto-detect from API
model_name = device.model_info.get("model")  # "DMP-A10" or "DMP-A6"
```

### 2. Model-Specific Remote Entity

**Approach:** Build remote entity buttons based on discovered capabilities.

```python
# Pseudo-code
if model_name == "DMP-A10":
    output_buttons = ["RCA", "XLR", "XLR/RCA", "OPT/COAX"]
    brightness_buttons = ["Display +/-", "Display Off/On"]  # No knob

elif model_name == "DMP-A6":
    output_buttons = ["RCA", "XLR", "XLR/RCA", "HDMI", "OPT/COAX"]
    brightness_buttons = ["Display +/-", "Display Off/On", "Knob +/-"]
```

### 3. Brightness Page Rules

**Display Controls (Both Models):**
- Display + (increase by 10)
- Display - (decrease by 10)
- Display Off (calls `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.OFF`)
- Display On (calls `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.ON`)

**Knob Controls (A6 Only):**
- Knob + (increase by 20)
- Knob - (decrease by 20)

### 4. Setup Flow Enhancement

**Add Model Selection:**
1. Auto-detect model from `/ZidooControlCenter/getModel`
2. Display detected model to user
3. Allow manual override if needed
4. Store model in config
5. Use model to build appropriate remote entity

---

## 🐛 Known Issues

### Issue 1: Display Off/On Behavior
**Symptom:** Display Off just dims (brightness 0) instead of turning screen completely off.
**Solution:** Use remote control keys instead of brightness API.

**Working Endpoints:**
- OFF: `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.OFF`
- ON: `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.ON`

### Issue 2: Knob Brightness on A10
**Symptom:** API accepts commands but nothing happens.
**Cause:** DMP-A10 is a DAC without knob LED hardware.
**Solution:** Hide knob buttons for A10 model.

### Issue 3: USB DAC Output Disabled
**Symptom:** USB DAC output exists but `enable: false`.
**Cause:** Requires USB device to be physically connected.
**Solution:** Keep button, show error if not available (expected behavior).

---

## 📋 Remote Entity Button Matrix

| Button | Command ID | DMP-A10 | DMP-A6 | API Tag |
|--------|-----------|---------|--------|---------|
| **Playback** |
| Previous | PREVIOUS | ✅ | ✅ | `play_pause()` |
| Play | PLAY | ✅ | ✅ | `play_pause()` |
| Next | NEXT | ✅ | ✅ | `next_track()` |
| Pause | PAUSE | ✅ | ✅ | `play_pause()` |
| Stop | STOP | ✅ | ✅ | `play_pause()` |
| **Volume** |
| Vol + | VOLUME_UP | ✅ | ✅ | `volume_up()` |
| Vol - | VOLUME_DOWN | ✅ | ✅ | `volume_down()` |
| Vol +10 | VOLUME_UP_10 | ✅ | ✅ | `set_volume(cur+10)` |
| Vol -10 | VOLUME_DOWN_10 | ✅ | ✅ | `set_volume(cur-10)` |
| Mute | MUTE | ✅ | ✅ | `mute()` |
| Unmute | UNMUTE | ✅ | ✅ | `unmute()` |
| **Outputs** |
| RCA | OUTPUT_RCA | ✅ | ✅ | `RCA` |
| XLR | OUTPUT_XLR | ✅ | ✅ | `XLR` |
| HDMI | OUTPUT_HDMI | ❌ | ✅ | `HDMI` |
| OPT/COAX | OUTPUT_SPDIF | ✅ | ✅ | `SPDIF` |
| XLR/RCA | OUTPUT_XLRRCA | ✅ | ✅ | `XLRRCA` |
| USB DAC | OUTPUT_USB | ⚠️ | ⚠️ | `USB` (disabled) |
| **Brightness** |
| Display + | DISPLAY_BRIGHT | ✅ | ✅ | Brightness +10 |
| Display - | DISPLAY_DIM | ✅ | ✅ | Brightness -10 |
| Display Off | DISPLAY_OFF | ✅ | ✅ | Screen OFF key |
| Display On | DISPLAY_ON | ✅ | ✅ | Screen ON key |
| Knob + | KNOB_BRIGHT | ❌ | ✅ | Knob +20 |
| Knob - | KNOB_DIM | ❌ | ✅ | Knob -20 |

**Legend:**
- ✅ Supported and working
- ❌ Not supported/doesn't work
- ⚠️ Exists but disabled (requires hardware)

---

## 🎯 Next Steps

1. ✅ Discovery scripts completed
2. ⬜ Add model detection to device.py (already implemented)
3. ⬜ Create model-specific remote entity builder
4. ⬜ Add model selection to setup flow
5. ⬜ Test on both A6 and A10
6. ⬜ Document model-specific features in README

---

## 📊 API Endpoint Reference

### Device Info
- `/ZidooControlCenter/getModel` - Device model, MAC, firmware
- `/ZidooMusicControl/v2/getState` - Playback state, volume, track info

### I/O Management
- `/ZidooMusicControl/v2/getInputAndOutputList` - All inputs/outputs with enable status
- `/ZidooMusicControl/v2/setOutInputList?tag=X&index=Y` - Select output

### Brightness
- `/SystemSettings/displaySettings/getScreenBrightness` - Get display brightness (0-115)
- `/SystemSettings/displaySettings/setScreenBrightness?index=X` - Set display brightness
- `/SystemSettings/displaySettings/getKnobBrightness` - Get knob brightness (0-255)
- `/SystemSettings/displaySettings/setKnobBrightness?index=X` - Set knob brightness

### Remote Control
- `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.ON` - Turn screen on
- `/ZidooControlCenter/RemoteControl/sendkey?key=Key.Screen.OFF` - Turn screen off
- `/ControlCenter/RemoteControl/sendkey?key=Key.VolumeUp` - Volume up
- `/ControlCenter/RemoteControl/sendkey?key=Key.VolumeDown` - Volume down

### Display Modes
- `/SystemSettings/displaySettings/getVUModeList` - Get VU meter modes
- `/SystemSettings/displaySettings/setVUMode?index=X` - Set VU mode
- `/SystemSettings/displaySettings/getSpPlayModeList` - Get spectrum modes
- `/SystemSettings/displaySettings/setSpPlayModeList?index=X` - Set spectrum mode

### Audio Settings
- `/SystemSettings/audioSettings/getXlrOutputOption` - XLR/RCA output settings
- `/SystemSettings/audioSettings/getSubOutputOption` - Subwoofer settings (A10 only)

---

## ✅ Conclusion

The discovery reveals significant differences between models that require conditional remote entity building:

1. **HDMI output** - A6 only
2. **Knob brightness** - A6 only (A10 hardware doesn't support it)
3. **Advanced features** - A10 has DSP/Sub, A6 has EQ

**Recommended Approach:**
- Auto-detect model during setup
- Build model-specific remote entity
- Hide unsupported buttons
- Provide clear user experience per model

**User Experience:**
- A6 users get full remote with HDMI and knob controls
- A10 users get DAC-focused remote without HDMI/knob
- Both get complete playback, volume, and display controls

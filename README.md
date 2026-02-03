# Eversolo Integration for Unfolded Circle Remote 2/3

Control your Eversolo music streamer directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player control, **real-time state monitoring**, and **complete HTTP API-based control**.

![Eversolo](https://img.shields.io/badge/Eversolo-Music%20Streamer-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-eversolo?style=flat-square)](https://github.com/mase1981/uc-intg-eversolo/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-eversolo?style=flat-square)](https://github.com/mase1981/uc-intg-eversolo/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-eversolo/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of Eversolo music streamers through the native HTTP API, delivering seamless integration with your Unfolded Circle Remote for complete music control.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **Media Player Control**

#### **Power Management**
- **Power Off** - Turn off the device
- **State Feedback** - Real-time power state monitoring
## NOTE: Eversolo devices do NOT support power on via IP, there is zero way for the integration to do so, this is NOT an integration issue. To power on the device you need to use IR or the original remote, IR codes can be found [here](https://github.com/mase1981/uc-intg-eversolo/blob/main/Custom%20-%20learned%20IR%20codes_Eversolo%20DMP-A6_codeset_2026-02-04.csv)

#### **Volume Control**
- **Volume Up/Down** - Precise volume adjustment
- **Set Volume** - Direct volume control (0-100 scale)
- **Volume Slider** - Visual volume control
- **Mute Toggle** - Quick mute/unmute
- **Mute/Unmute** - Explicit mute controls
- **Real-time Updates** - Instant volume feedback

#### **Source Selection**
Control all available input sources:
- **USB Input** - USB audio playback
- **Optical/Coaxial** - Digital audio inputs
- **Bluetooth** - Wireless audio streaming
- **Network** - Network streaming (Spotify, Tidal, etc.)
- **Custom Names** - Uses your configured input names

#### **Playback Control**
- **Play/Pause Toggle** - Control playback state
- **Next/Previous Track** - Navigate through tracks
- **Seek** - Jump to specific position in track
- **Real-time Position** - Current playback position

#### **Media Information**
- **Track Title** - Currently playing song
- **Artist Name** - Artist information
- **Album Name** - Album information
- **Duration** - Track length
- **Position** - Current playback position

### 📊 **Sensor Entities**

Real-time monitoring of device state:

- **State Sensor** - Current playback state (Playing, Paused, Idle)
- **Source Sensor** - Currently selected input source
- **Volume Sensor** - Current volume level percentage

### **Protocol Requirements**

- **Protocol**: Eversolo HTTP API
- **HTTP Port**: 9529 (default)
- **Network Access**: Device must be on same local network
- **Connection**: Periodic polling for state updates
- **Real-time Updates**: Regular polling for instant state changes

### **Network Requirements**

- **Local Network Access** - Integration requires same network as Eversolo device
- **HTTP Protocol** - HTTP API (port 9529)
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Firewall** - Must allow HTTP traffic

---

## 🎛️ **Model-Specific Features**

This integration supports multiple Eversolo models with **model-specific remote entities**. During setup, you'll select your device model to get optimized controls.

### Supported Models

| Model | Type | Description |
|-------|------|-------------|
| **DMP-A6** | Music Streamer | Full-featured streamer with HDMI output and knob LED |
| **DMP-A8** | DAC/Preamp | Hybrid DAC with knob LED, EQ, and extensive I/O options |
| **DMP-A10** | DAC/Preamp | High-end DAC with advanced DSP and subwoofer management |

### Feature Comparison

| Feature | DMP-A6 | DMP-A8 | DMP-A10 | Notes |
|---------|:------:|:------:|:-------:|-------|
| **Media Player** | ✅ | ✅ | ✅ | Full playback control |
| **Volume Control** | ✅ | ✅ | ✅ | Volume slider, up/down, mute |
| **Source Selection** | ✅ | ✅ | ✅ | All available inputs |
| **Sensors** | ✅ | ✅ | ✅ | State, source, volume, output |
| **Remote Entity** | ✅ | ✅ | ✅ | Model-specific button layout |
| | | | | |
| **Remote - Playback** | ✅ | ✅ | ✅ | Play, pause, stop, next, previous |
| **Remote - Volume** | ✅ | ✅ | ✅ | Vol +/-, mute, +10/-10 |
| **Remote - Display Controls** | ✅ | ✅ | ✅ | Display brightness +/-, off/on |
| **Remote - Knob Controls** | ✅ | ✅ | ❌ | Knob brightness (A6/A8 only) |
| | | | | |
| **Audio Outputs** | | | | |
| • RCA (Analog) | ✅ | ✅ | ✅ | Analog RCA output |
| • XLR (Balanced) | ✅ | ✅ | ✅ | Balanced XLR output |
| • XLR/RCA (Combined) | ✅ | ✅ | ✅ | Simultaneous XLR+RCA output |
| • HDMI | ✅ | ❌ | ❌ | **A6 only** - Digital video/audio |
| • IIS | ❌ | ✅ | ❌ | **A8 only** - I2S output |
| • OPT/COAX (Digital) | ✅ | ✅ | ✅ | Optical/Coaxial SPDIF |
| | | | | |
| **Advanced Features** | | | | |
| • DSP Settings | ❌ | ✅ | ✅ | **A8/A10** - Digital signal processing |
| • Subwoofer Management | ❌ | ✅ | ✅ | **A8/A10** - Sub output control |
| • EQ Settings | ❌ | ✅ | ❌ | **A8 only** - Equalizer |
| • DRC Settings | ❌ | ✅ | ❌ | **A8 only** - Dynamic range compression |
| • VU Meter Modes | ✅ | ✅ | ✅ | Multiple VU display styles |
| • Spectrum Modes | ✅ | ✅ | ✅ | Spectrum analyzer displays |

### Remote Entity Pages

**DMP-A6 Remote (4 pages):**
- 📀 **Playback** (3×3) - Play, pause, stop, next, previous, shuffle, repeat
- 🔊 **Volume** (3×2) - Up/down, mute/unmute, ±10
- 🔌 **Outputs** (3×3) - RCA, XLR, **HDMI**, OPT/COAX, XLR/RCA, USB DAC, IIS
- 💡 **Brightness** (2×3) - Display controls + **Knob brightness**

**DMP-A8 Remote (4 pages):**
- 📀 **Playback** (3×3) - Same as A6
- 🔊 **Volume** (3×2) - Same as A6
- 🔌 **Outputs** (3×2) - RCA, XLR, **IIS**, OPT/COAX, XLR/RCA *(No HDMI)*
- 💡 **Brightness** (2×3) - Display controls + **Knob brightness**

**DMP-A10 Remote (4 pages):**
- 📀 **Playback** (3×3) - Same as A6
- 🔊 **Volume** (3×2) - Same as A6
- 🔌 **Outputs** (2×2) - RCA, XLR, OPT/COAX, XLR/RCA *(No HDMI/IIS)*
- 💡 **Display** (2×2) - Display brightness only *(No knob controls)*

### Model Selection

During setup, you'll select your model from a dropdown:
- **DMP-A6 (Music Streamer with HDMI & Knob)** - Select for A6 models
- **DMP-A8 (DAC/Preamp with Knob - No HDMI)** - Select for A8 models
- **DMP-A10 (DAC/Preamp - No HDMI/Knob)** - Select for A10 models

The integration will automatically create the appropriate remote entity with model-specific buttons.

---

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-eversolo/releases) page
2. Download the latest `uc-intg-eversolo-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-eversolo:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-eversolo:
    image: ghcr.io/mase1981/uc-intg-eversolo:latest
    container_name: uc-intg-eversolo
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-eversolo --restart unless-stopped --network host -v eversolo-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-eversolo:latest
```

## Configuration

### Step 1: Prepare Your Eversolo Device

**IMPORTANT**: Eversolo device must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Check that device is connected to network (Ethernet or WiFi)
2. Note the IP address from device's network settings
3. Ensure device firmware is up to date
4. Verify HTTP API is accessible (enabled by default on port 9529)

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow HTTP traffic (port 9529)
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The Eversolo integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **Device Name**: Friendly name (e.g., "Living Room Eversolo")
- **IP Address**: Enter device IP (e.g., 192.168.1.100)
- **Port**: Default is 9529 (change only if needed)
- **Device Model**: Select your model (DMP-A6 or DMP-A10)
  - **DMP-A6**: Music Streamer with HDMI & Knob
  - **DMP-A10**: DAC/Preamp without HDMI/Knob
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies device connectivity
- HTTP connection established
- Setup fails if device unreachable

4. Integration will create entities:
   - **Media Player**: `media_player.eversolo_[device_name]`
   - **Sensors**: Multiple sensor entities for state monitoring

## Using the Integration

### Media Player Entity

The media player entity provides complete control:

- **Power Control**: Off with state feedback
- **Volume Control**: Volume slider (0-100)
- **Volume Buttons**: Up/Down with real-time feedback
- **Mute Control**: Toggle, Mute, Unmute
- **Source Selection**: Dropdown with all available inputs
- **Playback Control**: Play/Pause, Next, Previous, Seek
- **Media Info**: Current track, artist, album, duration, position

### Sensor Entities

| Sensor | Description |
|--------|-------------|
| State Sensor | Current playback state |
| Source Sensor | Currently selected input source |
| Volume Sensor | Current volume level percentage |

## Credits

- **Developer**: Meir Miyara
- **Eversolo**: High-performance music streamers and DACs
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: Eversolo HTTP API
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-eversolo/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Eversolo Support**: [Official Eversolo Support](https://www.eversolo.com/support)

---

**Made with ❤️ for the Unfolded Circle and Eversolo Communities**

**Thank You**: Meir Miyara

# Camera V2 OPI - Advanced Camera Display

A modern, dark-themed Phoebus OPI for controlling Area Detector cameras with a progressive plugin chain.

## Overview

Camera V2 is designed to handle the progressive processing chain defined in `adcamera2.yaml.j2`:

```
Camera (Raw) → ROI → Processing → Statistics → Overlay → TIFF Writer
                                                      ↓
                                            PVA Stream (image1)
```

## Quick Start

### Using the Wrapper (Recommended)

The easiest way to use Camera V2 is through the wrapper `CameraV2.bob`, which reads your configuration file and automatically sets all macros:

```bash
phoebus -resource "CameraV2.bob?CONFFILE=../../deploy/values.yaml&DID=main"
```

The wrapper:
1. Reads the YAML configuration file (CONFFILE macro)
2. Populates a camera dropdown with all available cameras
3. Automatically sets ROI_ENABLED, PROC_ENABLED, STATS_ENABLED, OVERLAY_ENABLED, TIFF_ENABLED, STREAM_ENABLED macros based on the IOC configuration
4. Loads the CameraV2_Main.bob with the correct macros

### Configuration File Format

The wrapper reads standard `values.yaml` files with this structure:

```yaml
epicsConfiguration:
  iocs:
    - name: "cam01"
      devgroup: cam          # Must be 'cam' to be recognized
      iocprefix: "LEL"
      template: "adcamera2"
      roi_enable: true       # Plugin enable flags
      proc_enable: true
      stats_enable: true
      overlay_enable: true
      tiff_enable: true
      stream_enable: false
      devices:
        - name: "SIM01"
```

### Direct Access (Without Wrapper)

You can also open CameraV2_Main.bob directly with all macros specified:

```bash
phoebus -resource "CameraV2_Main.bob?DEVICE=ELI-NP&CAM=Cam1&ROI_ENABLED=1&PROC_ENABLED=1&STATS_ENABLED=1&OVERLAY_ENABLED=0&TIFF_ENABLED=1&STREAM_ENABLED=1"
```

## Features

### 🎨 Modern Dark Theme
- Background: `rgb(30,34,42)` to `rgb(50,58,72)`
- Accent colors: Cyan, Green, Orange, Purple
- Rounded containers with subtle borders
- Clear visual hierarchy

### 📊 Processing Chain Visualization
- Visual chain indicator bar showing plugin status
- Color-coded LEDs for each plugin stage
- Dynamic visibility based on enabled plugins

### 🔧 Plugin Panels

| Panel | Purpose | Color Accent |
|-------|---------|--------------|
| **Acquire** | Start/Stop, Timing, Trigger | Green |
| **ROI** | Region selection, Binning | Blue |
| **Process** | Background, Flat Field, Scaling | Purple |
| **Stats** | Min/Max/Mean/Sigma, Centroid, Histogram | Orange |
| **Overlay** | Crosshairs, ROI Box, Annotations | Cyan |
| **Save** | TIFF file writing, Path config | Green |

### 📷 Dynamic Image Display
- Multi-source image widget (Raw, ROI, Processed, Overlay)
- Color bar and axis options
- Colormap selection
- Fullscreen mode

## Files

```
unicam-opi-v2/
├── CameraV2.bob                # Wrapper with config file loading
├── CameraV2_Main.bob           # Main display (1600x950)
├── CameraV2_ChainIndicator.bob # Processing chain status bar
├── CameraV2_AcquirePanel.bob   # Acquisition controls
├── CameraV2_ROIPanel.bob       # ROI configuration
├── CameraV2_ProcessPanel.bob   # NDProcess controls
├── CameraV2_StatsPanel.bob     # Statistics display
├── CameraV2_OverlayPanel.bob   # Overlay configuration
├── CameraV2_SavePanel.bob      # TIFF file saving
├── CameraV2_ImageDisplay.bob   # Multi-source image widget
├── CameraV2_QuickStats.bob     # Right sidebar quick stats
├── CameraV2_BottomStatus.bob   # Bottom status bar
├── CameraV2_ImageFullscreen.bob # Fullscreen image view
├── README.md                   # This file
└── Scripts/
    ├── LoadDeviceV2.py         # Script to load devices from config
    └── DeviceSelectV2.py       # Script to handle device selection
```

## Macros

### Wrapper Macros (CameraV2.bob)

| Macro | Description | Example |
|-------|-------------|---------|
| `CONFFILE` | Path to YAML configuration file | `../../deploy/values.yaml` |
| `GROUP` | Device group filter (default: cam) | `cam` |
| `DID` | Display instance ID (for multiple instances) | `main` |

### Main Display Macros (CameraV2_Main.bob)

| Macro | Description | Example |
|-------|-------------|---------|
| `DEVICE` | Device prefix | `ELI-NP` |
| `CAM` | Camera name | `Cam1` |
| `ROI_ENABLED` | ROI plugin enabled (0/1) | `1` |
| `PROC_ENABLED` | Process plugin enabled (0/1) | `1` |
| `STATS_ENABLED` | Stats plugin enabled (0/1) | `1` |
| `OVERLAY_ENABLED` | Overlay plugin enabled (0/1) | `1` |
| `TIFF_ENABLED` | TIFF writer enabled (0/1) | `1` |
| `STREAM_ENABLED` | PVA stream enabled (0/1) | `1` |

## PV Structure

### Camera Core
- `$(DEVICE):$(CAM):Acquire` - Start/Stop
- `$(DEVICE):$(CAM):AcquireTime` - Exposure time
- `$(DEVICE):$(CAM):ArrayRate_RBV` - Frame rate
- `$(DEVICE):$(CAM):ArrayCounter_RBV` - Frame counter

### Plugins
- `$(DEVICE):$(CAM):ROI1:EnableCallbacks` - ROI enable
- `$(DEVICE):$(CAM):Proc1:EnableCallbacks` - Process enable
- `$(DEVICE):$(CAM):Stats1:EnableCallbacks` - Stats enable
- `$(DEVICE):$(CAM):Over1:EnableCallbacks` - Overlay enable
- `$(DEVICE):$(CAM):TIFF1:EnableCallbacks` - TIFF writer enable
- `$(DEVICE):$(CAM):Pva1:EnableCallbacks` - PVA stream enable

### Image Arrays
- `$(DEVICE):$(CAM):image1:ArrayData` - Final processed image
- `$(DEVICE):$(CAM):ROI1:ArrayData` - ROI output
- `$(DEVICE):$(CAM):Proc1:ArrayData` - Processed output
- `$(DEVICE):$(CAM):Over1:ArrayData` - Overlay output

## Usage

### Opening the Display

From CS-Studio/Phoebus:
```
File → Open → CameraV2_Main.bob
```

With macros:
```bash
phoebus -resource "CameraV2_Main.bob?DEVICE=ELI-NP&CAM=Cam1"
```

### Dynamically Tuning Interface

The interface can be dynamically tuned based on which plugins are enabled in the IOC configuration. Pass the enable flags as macros:

```bash
phoebus -resource "CameraV2_Main.bob?DEVICE=ELI-NP&CAM=Cam1&ROI_ENABLED=1&PROC_ENABLED=1&STATS_ENABLED=1&OVERLAY_ENABLED=0&TIFF_ENABLED=1&STREAM_ENABLED=1"
```

Components will be hidden/shown based on these flags.

## Integration with adcamera2.yaml.j2

The OPI is designed to work with IOCs generated from the `adcamera2.yaml.j2` template:

```yaml
# Example camera definition
devices:
  cameras:
    - name: Cam1
      driver: aravis
      ip: 192.168.1.100
      roi_enable: true
      proc_enable: true
      stats_enable: true
      overlay_enable: false
      tiff_enable: true
      stream_enable: true
```

## Screenshots

The display features:
1. **Header** - Camera name, status LED, connection info
2. **Processing Chain Bar** - Visual pipeline status
3. **Tab Panel (Left)** - Control sections in tabs
4. **Image Area (Center)** - Live camera view with controls
5. **Quick Stats (Right)** - Real-time statistics sidebar
6. **Status Bar (Bottom)** - Frame counter, FPS, dimensions

## Requirements

- Phoebus 4.7+ or CS-Studio
- Area Detector 3.11+
- ADSupport plugins (ROI, Process, Stats, Overlay, FileTIFF)
- pvxs/pvAccessCPP for image streaming

## Author

Generated for the ELI-NP / INFN EPICS infrastructure project.

## License

Part of the epik8s-eli OPI collection.

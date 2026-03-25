# 🔌 Hardware Integration & Calibration Guide

## 🛠️ Hardware Requirements

| Component | Minimum | Recommended |
|:---|:---|:---|
| **Webcam** | 720p @ 30 FPS | 1080p @ 30 FPS (Autofocus) |
| **CPU** | Dual-core 2.5GHz | Quad-core 3.0GHz+ |
| **Lighting** | Static ambient light | Front-facing diffuse light |

---

## 🎯 Calibration Workflow

The system uses a **Homography-based mapping** to translate your gaze from the webcam frame to specific screen pixels.

### Steps to Perfect Calibration:
1. **Stabilize Head**: Sit in your natural operating position.
2. **Follow the Dot**: The GUI will present dots at various screen corners.
3. **Data Collection**: The system records the relationship between your iris position and the dot's screen coordinates.
4. **Validation**: A transformation matrix is generated and saved to `calibration.json`.

---

## 🖱️ Interaction Methods (Technician View)

| Action | Detection Logic | Technician Note |
|:---|:---|:---|
| **Move** | Head Yaw/Pitch + Iris Offset | Check `head_sensitivity` in config. |
| **Left Click** | EAR < 0.2 (Short Blink) | EAR = Eye Aspect Ratio. |
| **Right Click** | Dwell > 1.0s | Radius is configurable in `config.py`. |
| **Drag** | Pinch Gesture (Hand) | Thumb and Index tip distance < 50px. |

---

## 🔧 Troubleshooting for Technicians

> [!WARNING]
> **Cursor Drifting?**
> Check if the user is sitting too far. The Face Mesh loses precision beyond 1.5 meters.
> 
> **Clicks not Registering?**
> Monitor the "Confidence Score" in the TUI. If it's below 0.6, the environment is too dark.

### Log Inspection
All technical errors are logged to `kursorin.log`. Use `tail -f kursorin.log` for real-time diagnostics.

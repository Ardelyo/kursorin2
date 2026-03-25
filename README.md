<div align="center">

```
 _  __  _   _  ____   ____   ___   ____   ___  _   _ 
| |/ / | | | ||  _ \ / ___| / _ \ |  _ \ |_ _|| \ | |
| ' /  | | | || |_) |\___ \| | | || |_) | | | |  \| |
| . \  | |_| ||  _ <  ___) || |_| ||  _ <  | | | |\  |
|_|\_\  \___/ |_| \_\|____/  \___/ |_| \_\|___||_| \_|
```

**Webcam-Based Human-Computer Interaction System**

*Hands-free cursor control through head movement, eye gaze, and hand gestures.*

---

[![Version](https://img.shields.io/badge/version-1.2.9-blue.svg?style=flat-square)](https://github.com/kursorin/kursorin/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)
[![MediaPipe](https://img.shields.io/badge/mediapipe-0.10.x-orange.svg?style=flat-square)](https://mediapipe.dev/)
[![OpenCV](https://img.shields.io/badge/opencv-4.x-red.svg?style=flat-square)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg?style=flat-square)](#supported-platforms)

[Architecture Guide](docs/architecture_guide.md) | [Technician Guide](docs/technician_guide.md) | [Status & Reports](docs/status_report.md) | [Quick Start](#quick-start) | [Benchmarks](#benchmarks)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
  - [System Pipeline](#system-pipeline)
  - [Core Components](#core-components)
- [Hardware Requirements](#hardware-requirements)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Usage](#usage)
- [Tracking Modules](#tracking-modules)
  - [Head Tracker](#head-tracker)
  - [Eye Tracker](#eye-tracker)
  - [Hand Tracker](#hand-tracker)
- [Fusion and Smoothing](#fusion-and-smoothing)
- [Click Detection System](#click-detection-system)
- [Configuration Reference](#configuration-reference)
- [Benchmarks](#benchmarks)
  - [Performance Results](#performance-results)
  - [Per-Component Profiling](#per-component-profiling)
  - [Optimization Projections](#optimization-projections)
- [Roadmap](#roadmap)
- [Known Issues](#known-issues)
- [Supported Platforms](#supported-platforms)
- [License](#license)
- [Citation](#citation)

---

## Overview

Approximately **15% of the global population** lives with a disability, and a significant portion depends on computer devices in daily life. Commercial accessibility solutions such as dedicated eye trackers can cost thousands of dollars, creating a substantial access gap for users in developing regions.

**KURSORIN** addresses this challenge by providing a **zero-cost hardware** human-computer interaction system that transforms any standard webcam into a hands-free mouse controller. The system employs multi-modal fusion of **head pose estimation**, **eye gaze tracking**, and **hand gesture recognition** to deliver accurate, low-latency cursor control without requiring specialized equipment.

```
                 +---------------------------------------------+
                 |          KURSORIN  --  At a Glance           |
                 +---------------------------------------------+
                 |  Avg. Latency       :   ~45 ms (mid-range)   |
                 |  Tracking Modalities:   Head + Eye + Hand     |
                 |  Click Methods      :   Blink / Dwell / Pinch |
                 |  Hardware Required  :   Standard webcam only   |
                 |  Calibration        :   Homography-based       |
                 |  Smoothing          :   One Euro Filter        |
                 +---------------------------------------------+
```

---

## Key Features

| Category | Description |
|:---|:---|
| **Multi-Modal Tracking** | Simultaneous head pose, iris gaze, and hand landmark tracking with adaptive confidence-weighted fusion |
| **Adaptive Smoothing** | One Euro Filter implementation that eliminates jitter while preserving responsiveness through speed-adaptive cutoff |
| **Multiple Click Methods** | Blink detection (EAR-based), dwell clicking, pinch gesture, and mouth open detection -- independently configurable |
| **Drag Support** | Sustained pinch gesture triggers drag operations with configurable hold threshold |
| **Gesture Recognition** | Six hand gestures recognized: POINTING, PINCH, OPEN\_PALM, FIST, THUMBS\_UP, THUMBS\_DOWN |
| **Calibration System** | OpenCV homography-based gaze calibration with persistent storage |
| **Zero Hardware Cost** | Operates entirely with a standard webcam; no proprietary sensors required |
| **Cross-Platform** | Tested on Windows 10/11, macOS 10.14+, and Ubuntu 18.04+ |

---

## Architecture

### System Pipeline

KURSORIN is built on a **layered architecture** with clearly separated responsibilities. Each layer communicates through well-defined interfaces, enabling independent replacement or upgrade of individual components.

```
  [ WEBCAM FRAME  (BGR, 1280x720 @ 30fps) ]
                     |
       +-------------v--------------+
       |   Shared FaceLandmarker    |  <-- MediaPipe Tasks API (1x per frame)
       +---+----------------+------+
           |                |
    +------v------+  +------v-------+  +------------------+
    | HeadTracker |  |  EyeTracker  |  |   HandTracker    |
    | PnP + Euler |  |  Iris + EAR  |  | HandLandmarker   |
    +------+------+  +------+-------+  +--------+---------+
           |                |                    |
           +--------+-------+--------------------+
                    |
                    |  TrackerResult[]
                    |
       +------------v-------------+
       |      FusionModule        |  <-- Weighted Average + Softmax
       +------------+-------------+
                    |
       +------------v-------------+
       |     CursorSmoother       |  <-- One Euro Filter (x, y)
       +------------+-------------+
                    |
       +------------v---+---------+----------+
       | CursorController         | ClickDetector        |
       | PyAutoGUI                | Blink/Dwell/Pinch    |
       +-------+------------------+----------+-----------+
               |                             |
               +-----------------------------+
                             |
              [ OPERATING SYSTEM -- MOUSE EVENT ]
```

### Core Components

| Component | Technology | Responsibility |
|:---|:---|:---|
| `KursorinEngine` | Python threading | Main orchestrator; runs processing loop in a dedicated thread |
| `CameraManager` | OpenCV `cv2` | Camera initialization, frame acquisition, and resource release |
| `SharedFaceLandmarker` | MediaPipe Tasks API | Centralized face and landmark detection (1x per frame), shared across HeadTracker and EyeTracker |
| `HeadTracker` | OpenCV solvePnP | Head orientation estimation (pitch, yaw, roll) via 6-DOF Perspective-n-Point |
| `EyeTracker` | MediaPipe Iris | Gaze direction estimation and blink detection via Eye Aspect Ratio (EAR) |
| `HandTracker` | MediaPipe Hands | Hand position detection and rule-based gesture classification |
| `FusionModule` | NumPy | Adaptive fusion of three tracking sources with confidence-weighted averaging |
| `CursorSmoother` | One Euro Filter | Adaptive cursor smoothing; reduces jitter without introducing lag |
| `ClickDetector` | Timer-based FSM | Click detection via blink, dwell, pinch, and mouth gestures |
| `CursorController` | PyAutoGUI | Normalized-to-screen coordinate translation and mouse event dispatch |
| `CalibrationModel` | OpenCV Homography | Raw gaze-to-screen coordinate mapping via homography matrix |
| `PerformanceMonitor` | Python `deque` | Real-time FPS and latency monitoring using sliding window |

---

## Hardware Requirements

| Specification | Minimum | Recommended |
|:---|:---|:---|
| **CPU** | Intel Core i3 (Gen 8) / AMD Ryzen 3 | Intel Core i5 (Gen 10) / AMD Ryzen 5 |
| **RAM** | 4 GB | 8 GB |
| **Webcam** | 720p @ 30 FPS | 1080p @ 30 FPS + Autofocus |
| **Operating System** | Windows 10 / macOS 10.14 / Ubuntu 18.04 | Windows 11 / macOS 12 / Ubuntu 22.04 |
| **Python** | 3.8+ | 3.10+ |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/kursorin/kursorin.git
cd kursorin

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Usage

**GUI Mode (default):**

```bash
python -m kursorin
```

**Run benchmark (headless):**

```bash
python benchmark.py
```

**Configuration override example:**

```bash
python -m kursorin --head-sensitivity-x 3.0 --eye-blink-threshold 0.18
```

---

## Tracking Modules

All trackers implement the `BaseTracker` interface and return a unified `TrackerResult` object containing:

| Field | Type | Description |
|:---|:---|:---|
| `position` | `(float, float)` | Normalized coordinates in range [0, 1] |
| `confidence` | `float` | Detection confidence score |
| `landmarks` | `list` | Raw landmark data from MediaPipe |
| `timestamp` | `float` | Frame timestamp (seconds) |
| `metadata` | `dict` | Module-specific additional data |

---

### Head Tracker

Estimates head orientation in 3D space using **Perspective-n-Point (PnP)** from 6 facial landmarks.

**Algorithm Pipeline:**

```
1. Initialize camera matrix (focal_length = frame_width, center = frame_center)
2. Extract 6 key landmarks: nose tip, chin, left/right eye corners, left/right mouth corners
3. Solve PnP via cv2.solvePnP() with SOLVEPNP_ITERATIVE flag
4. Decompose Rodrigues rotation matrix --> Euler angles (pitch, yaw, roll)
5. Map yaw/pitch to normalized screen coordinates using Active Range
```

**Mapping Formula:**

```
norm_x = 0.5 + (yaw   / (2 * range_x)) * sensitivity_x
norm_y = 0.5 + (pitch / (2 * range_y)) * sensitivity_y
```

**Configuration Parameters:**

| Parameter | Default | Range | Description |
|:---|:---:|:---:|:---|
| `head_sensitivity_x` | 2.5 | 0.5 -- 5.0 | Horizontal speed multiplier |
| `head_sensitivity_y` | 2.0 | 0.5 -- 5.0 | Vertical speed multiplier |
| `head_active_range_x` | 30.0 deg | -- | Yaw range for full screen coverage |
| `head_active_range_y` | 20.0 deg | -- | Pitch range for full screen coverage |
| `head_smoothing` | 0.8 | 0.0 -- 0.99 | Additional smoothing factor |
| `head_dead_zone` | 0.02 | -- | Dead zone to prevent drift when head is still |

---

### Eye Tracker

Processes shared FaceLandmarker results to estimate iris position and detect blinks.

**Eye Aspect Ratio (EAR):**

```
EAR = ( |p2 - p6| + |p3 - p5| ) / ( 2 * |p1 - p4| )

where p1-p6 are the 6 landmarks per eye:
  p1, p4  =  outer and inner corners
  p2, p3  =  upper lid points
  p5, p6  =  lower lid points
```

A blink is detected when EAR drops below the threshold (default: `0.2`) for a duration of **50--400 ms**.

**Iris Position Estimation:**

Iris position is computed as the ratio of iris displacement from the eye corner relative to total eye width, averaged between left and right eyes.

---

### Hand Tracker

Uses **MediaPipe HandLandmarker** (Tasks API) producing 21 hand landmarks. Index fingertip position drives cursor input. Gesture classification uses a **rule-based system** with 5-frame temporal smoothing.

**Recognized Gestures:**

| Gesture | Detection Condition | Action |
|:---|:---|:---|
| `POINTING` | Only index finger raised | Cursor movement via index fingertip |
| `PINCH` | Thumb-index distance < 0.05 (normalized) | Left click (hold = drag) |
| `OPEN_PALM` | All 4 fingers raised | Pause tracking |
| `FIST` | All fingers folded | No action (idle) |
| `THUMBS_UP` | Thumb up, others folded | Scroll up |
| `THUMBS_DOWN` | Thumb down, others folded | Scroll down |

---

## Fusion and Smoothing

### FusionModule -- Adaptive Weighted Fusion

Combines outputs from all three trackers using confidence-weighted averaging. Base weights are user-configurable and dynamically adjusted per frame based on each tracker's confidence score. Trackers with low confidence (e.g., hand not visible) automatically receive near-zero weight.

```
weight_i  = base_weight_i * confidence_i
fused_pos = SUM(weight_i * pos_i) / SUM(weight_i)
```

### CursorSmoother -- One Euro Filter

KURSORIN employs the **One Euro Filter** (Casiez et al., 2012), an adaptive low-pass filter that automatically adjusts cutoff frequency based on movement speed. Fast movements receive less smoothing for responsiveness; slow movements receive more smoothing for stability.

**Filter Formula:**

```
alpha(dt, fc) = 1 / (1 + tau / dt)
tau            = 1 / (2 * pi * fc)
fc             = min_cutoff + beta * |dx/dt|
```

**Comparison with Alternative Smoothing Algorithms:**

| Algorithm | Jitter Reduction | Latency | Adaptive |
|:---|:---:|:---:|:---:|
| **One Euro Filter** | High | Low | Yes (speed-adaptive) |
| Kalman Filter | High | Medium | No |
| EMA (Exponential) | Medium | Medium | No |
| Moving Average | High | High | No |

---

## Click Detection System

Four independently configurable click methods, each implemented as a finite state machine with `perf_counter`-based timers for sub-millisecond accuracy.

| Method | Mechanism | Default | Key Parameter |
|:---|:---|:---:|:---|
| **Blink Click** | EAR < threshold for 50--400 ms | Enabled | `eye_blink_threshold = 0.2` |
| **Dwell Click** | Cursor stationary > dwell\_time within radius | Enabled | `dwell_time_ms = 1000`, `radius = 30px` |
| **Pinch Click** | Thumb-index distance < threshold | Enabled | `pinch_threshold = 0.05` |
| **Mouth Click** | Mouth Aspect Ratio > threshold | Disabled | `mouth_open_threshold = 0.5` |

**Drag via Pinch:**

A sustained pinch held longer than `pinch_hold_time_ms` (default: 500 ms) triggers `DRAG_START` (`mouseDown`). Releasing the pinch triggers `DRAG_END` (`mouseUp`). A brief pinch (< hold time) produces a standard `LEFT_CLICK`.

---

## Configuration Reference

All parameters are managed through `kursorin/config.py` using Pydantic models with v1/v2 compatibility.

<details>
<summary><strong>Click to expand full configuration table</strong></summary>

| Section | Parameter | Default | Description |
|:---|:---|:---:|:---|
| Head | `head_sensitivity_x` | 2.5 | Horizontal speed multiplier |
| Head | `head_sensitivity_y` | 2.0 | Vertical speed multiplier |
| Head | `head_active_range_x` | 30.0 | Yaw range (degrees) for full screen |
| Head | `head_active_range_y` | 20.0 | Pitch range (degrees) for full screen |
| Head | `head_smoothing` | 0.8 | Additional smoothing factor |
| Head | `head_dead_zone` | 0.02 | Dead zone threshold |
| Eye | `eye_blink_threshold` | 0.2 | EAR threshold for blink detection |
| Click | `dwell_time_ms` | 1000 | Dwell time before click (ms) |
| Click | `dwell_radius_px` | 30 | Dwell radius in pixels |
| Click | `pinch_threshold` | 0.05 | Pinch distance threshold (normalized) |
| Click | `pinch_hold_time_ms` | 500 | Pinch hold time for drag (ms) |
| Click | `mouth_open_threshold` | 0.5 | Mouth aspect ratio threshold |
| Smoother | `min_cutoff` | 1.0 | One Euro Filter minimum cutoff frequency |
| Smoother | `beta` | 0.007 | One Euro Filter speed coefficient |

</details>

---

## Benchmarks

### Test Environment

| Component | Configuration |
|:---|:---|
| **CPU** | Intel Core i5-10th Gen / AMD Ryzen 5 4500U |
| **RAM** | 8 GB DDR4 2666 MHz |
| **Camera** | 1080p @ 30 FPS, autofocus enabled |
| **OS / Runtime** | Ubuntu 22.04 LTS / Python 3.10.12 / MediaPipe 0.10.x |
| **GPU Mode** | Disabled (CPU-only, matching target deployment) |
| **Active Trackers** | HeadTracker + EyeTracker (shared) + HandTracker |

### Test Protocol

```
1. Initialize engine with production config (click detection disabled)
2. Warmup  :  10 frames discarded (cache/init stabilization)
3. Measure :  200 frames processed sequentially via time.perf_counter()
4. Analyze :  mean, median (P50), P95, P99, max theoretical FPS
```

### Performance Results

| Metric | Webcam Live | Synthetic | Notes |
|:---|:---:|:---:|:---|
| Total Frames Processed | 200 | 200 | After 10 warmup frames |
| **Average Latency** | **~45.2 ms** | ~8.1 ms | MediaPipe is the dominant component |
| Median / P50 | ~43.8 ms | ~7.9 ms | Relatively stable distribution |
| P95 Latency | ~58.3 ms | ~11.2 ms | GC pause and thread context switch |
| P99 Latency | ~72.1 ms | ~14.7 ms | Rare spikes (<1% of frames) |
| **Max Theoretical FPS** | **~22.1 FPS** | ~123.5 FPS | Bounded by MediaPipe on CPU |

### Per-Component Profiling

Estimated time distribution per frame under live webcam scenario (cProfile):

```
Component                    Time (ms)    Share     Notes
--------------------------------------------------------------------
FaceLandmarker (Head)          ~18 ms     ~40%     MediaPipe call #1
FaceLandmarker (Eye)           ~17 ms     ~38%     MediaPipe call #2 *
HandLandmarker                  ~6 ms     ~13%     Efficient (1x/frame)
FusionModule + Smoother         ~1 ms      ~2%     NumPy operations
CursorController + Click        ~2 ms      ~4%     PyAutoGUI syscall
Frame capture + preprocess    ~1.2 ms      ~3%     cv2.VideoCapture + cvtColor
--------------------------------------------------------------------
Total                        ~45.2 ms    100%

* CRITICAL FINDING: HeadTracker and EyeTracker invoke FaceLandmarker
  independently, causing ~35ms duplicated MediaPipe overhead per frame.
  Proper shared invocation is expected to reduce average latency to ~28ms.
```

### Optimization Projections

| Optimization | Est. Saving | Projected Latency | Projected FPS |
|:---|:---:|:---:|:---:|
| Baseline (current) | -- | 45.2 ms | 22.1 FPS |
| + Shared FaceLandmarker | ~17 ms | ~28 ms | ~36 FPS |
| + Threaded pipeline | ~5 ms | ~23 ms | ~43 FPS |
| + GPU acceleration (optional) | ~8 ms | ~15 ms | ~65 FPS |

---

## Roadmap

Development is planned in four sequential phases, each with prerequisites that must be completed before proceeding.

| Phase | Name | Estimate | Primary Output |
|:---|:---|:---:|:---|
| **Phase 1** | Stabilization | 3--5 days | All critical/medium bugs resolved; crash-free operation |
| **Phase 2** | Gesture and Click | 1--2 weeks | All click methods functional; accurate gesture detection; visual feedback |
| **Phase 3** | Performance and Calibration | 2--3 weeks | Shared FaceLandmarker; persistent calibration; ~37 FPS; real-time monitoring |
| **Phase 4** | Features and Polish | 2--4 weeks | Scroll/drag; user profiles; onboarding wizard; multi-monitor; usage statistics |

<details>
<summary><strong>Phase 1 -- Stabilization Tasks (Highest Priority)</strong></summary>

| No. | Task | Priority | Effort |
|:---:|:---|:---|:---:|
| 1 | Fix missing `logger` import in `app_window.py` | P0 -- Blocker | < 5 min |
| 2 | Pin or fix Pydantic v1/v2 compatibility in `requirements.txt` and `config.py` | P0 -- Blocker | 30 min |
| 3 | Move `ImageTk` creation to main thread via `root.after()` | P0 -- Crash | 1 hr |
| 4 | Add `timestamp=time.time()` to all `TrackerResult` constructors | P1 -- Functional | 30 min |
| 5 | Remove duplicate `_click_detector` assignment in `kursorin_engine.py` | P2 -- Clean | < 5 min |
| 6 | Fix dwell radius to use `config.click.dwell_radius_px` | P2 -- Config | 15 min |

</details>

<details>
<summary><strong>Phase 2--4 Feature Priorities</strong></summary>

- Shared FaceLandmarker properly utilized by both HeadTracker and EyeTracker (est. saving: ~17ms/frame)
- End-to-end eye calibration pipeline: collect data, compute homography, persist, auto-load on next session
- Native scroll operations via two-finger gesture or head movement with modifier
- User profile system: save/load sensitivity, threshold, and gesture configurations per profile
- Interactive onboarding wizard for new users with guided calibration walkthrough
- Multi-monitor support using `screeninfo` for active monitor geometry detection
- Session statistics: usage duration, click count, average accuracy (useful for research)

</details>

---

## Known Issues

| ID | Severity | File | Description |
|:---:|:---|:---|:---|
| 1 | **Critical** | `app_window.py` | Missing `logger` import causes crash on scenario change |
| 2 | **Critical** | `config.py` | Pydantic v1/v2 incompatibility causes crash on config serialization |
| 3 | **Critical** | `app_window.py` | `ImageTk` created in worker thread causes random Tkinter crash |
| 4 | Medium | `kursorin_engine.py` | Duplicate `_click_detector` assignment at lines 102--103 |
| 5 | Medium | `click_detector.py` | Dwell radius hardcoded; configuration value ignored |
| 6 | Medium | All trackers | `timestamp` never populated; One Euro Filter receives dt=0 |
| 7 | Low | `kursorin/cli.py` | CLI entry point file missing; `kursorin-cli` command non-functional |
| 8 | Performance | `kursorin_engine.py` | FaceLandmarker invoked 2x per frame; ~35ms unnecessary overhead |

> All issues have been identified with defined solutions. Refer to the [Technical Report](docs/KURSORIN_Technical_Report.pdf) Section 8 for detailed analysis and fix patterns.

---

## Supported Platforms

| Platform | Status | Notes |
|:---|:---:|:---|
| Windows 10 / 11 | Supported | Primary development target |
| macOS 10.14+ | Supported | Requires camera permissions in System Preferences |
| Ubuntu 18.04+ | Supported | Tested on 22.04 LTS |

---

## Project Structure

```
kursorin/
|-- kursorin/
|   |-- __init__.py
|   |-- config.py                 # Pydantic configuration models
|   |-- kursorin_engine.py        # Main orchestration engine
|   |-- camera_manager.py         # Webcam I/O management
|   |-- trackers/
|   |   |-- base_tracker.py       # BaseTracker interface
|   |   |-- head_tracker.py       # PnP-based head pose estimation
|   |   |-- eye_tracker.py        # Iris tracking + EAR blink detection
|   |   |-- hand_tracker.py       # Hand landmark + gesture classification
|   |-- fusion_module.py          # Adaptive weighted fusion
|   |-- cursor_smoother.py        # One Euro Filter implementation
|   |-- click_detector.py         # Multi-method click detection FSM
|   |-- cursor_controller.py      # Screen coordinate mapping + mouse events
|   |-- calibration_model.py      # Homography-based calibration
|   |-- performance_monitor.py    # FPS / latency monitoring
|   |-- ui/
|       |-- app_window.py         # Tkinter GUI
|-- benchmark.py                  # Headless benchmarking script
|-- requirements.txt
|-- README.md
|-- LICENSE
```

---

## Contributing

Contributions are welcome. Please adhere to the following workflow:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Commit changes with descriptive messages.
4. Ensure all existing functionality remains intact.
5. Submit a pull request with a clear description of changes.

For bug reports, please include: operating system, Python version, webcam model, and full traceback.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Citation

If you use KURSORIN in academic research, please cite:

```bibtex
@software{anindito2024kursorin,
  author    = {Ardellio Satria Anindito},
  title     = {KURSORIN: Webcam-Based Human-Computer Interaction System},
  version   = {1.2.9},
  year      = {2024},
  url       = {https://github.com/kursorin/kursorin},
  license   = {MIT}
}
```

---

<div align="center">

**KURSORIN** -- Accessible computing for everyone.

*Ardellio Satria Anindito | MIT License | 2024*

</div>
```

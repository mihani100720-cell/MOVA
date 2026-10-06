# 🌌 MOVA — Multimodal Spatial Gaming & Movement Intelligence Platform

> **MOVE. PLAY. IMPROVE.**
> 
> *MOVA doesn't just watch your body. It understands how eyes, face, hands, arms, body, and voice interact together in space.*

---

## 🌟 What is MOVA?

**MOVA** is a multimodal spatial gaming platform that uses standard webcam computer vision, pose estimation, hand tracking, gaze/face mesh analysis, and spatial audio to deliver 10 interactive spatial gaming experiences.

MOVA evaluates physical-digital coordination strictly on a **YOU vs. YOUR PREVIOUS PERFORMANCE** basis. It never compares you against other users or normative averages, and strictly adheres to non-medical spatial wellness and movement intelligence principles.

---

## 🎮 Game Library (10 Multimodal Games)

| Game | Category | Modalities | Movement Focus |
| :--- | :--- | :--- | :--- |
| **Gravity Flip** | Spatial Navigation | Torso Lean, Posture | Dynamic Lateral Balance & Core Steering |
| **Dragon Dash** | Dodging & Agility | Torso Dodge, Hand Reach | Reactive Spatial Evasion & Energy Harvesting |
| **Galaxy Rescue** | Gaze-Hand Coordination | Gaze Fixation, Pinch/Grasp | Spatial Tractor Beam & Orbital Locking |
| **Spellcaster** | Trajectory Art | Hand Path, Voice Command | Geometric Glyph Casting & Velocity Shaping |
| **Bee Swarm** | Precision Interception | Hand Tracking, Spatial Reach | Multi-Target Swarm Swatting & Interception |
| **Treasure Storm** | Multimodal Agility | Torso Dodge, Pinch Gesture | Storm Evasion & Spatial Vault Cracking |
| **Robot Factory** | Multimodal Sequence | Gaze, Point, Grab, Voice | 5-Stage Spatial Object Assembly |
| **Ocean Guardian** | Torso & Hand Navigation | Torso Steering, Reach | Submarine Pitch/Roll Navigation & Pearl Recovery |
| **Mirror Mage** | Movement Memory | Pose Mimicry, Bilateral Reach | Memory Mirroring & Spatial Symmetry |
| **Neon Pulse** | Spatial Rhythm | Dual-Hand Spatial Timing | Beat Synchronization & 4-Quadrant Reach |

---

## 🚀 Key Features

* **Advanced Vision Pipeline**: Built with MediaPipe Tasks API (`PoseLandmarker`, `HandLandmarker`, `FaceLandmarker` with 468 mesh points & blendshapes) running real-time on standard webcams.
* **Multimodal Fusion Engine**: Integrates gaze fixation, hand position, head yaw/pitch, and voice commands into unified spatial intent vectors with measured response latencies.
* **Movement Intelligence Metrics**: Evaluates bilateral symmetry, path efficiency, jerk/smoothness, repetition state machines, and postural stability.
* **Adaptive Difficulty Engine**: Dynamically shifts target velocity, spawn density, scale, and reaction windows based on personal precision.
* **AI Movement Coach**: Provides non-medical movement guidance, habit synthesis, and session summaries using Gemini, OpenAI, or the local deterministic fallback.
* **Automated PDF Reports**: High-resolution exportable PDF reports with radar charts, metric breakdown tables, and baseline comparisons.
* **Movement Lab**: Real-time diagnostic sandbox showing joint angles, gaze vectors, gesture classification, and frame-by-frame kinematics.
* **Interactive Sensor Calibration**: 6-step guided wizard for lighting, standing distance, hand extension, torso lean, head rotation, and eye fixation.
* **Demo Mode Simulation**: Full synthetic spatial rig simulation enabling smooth testing, presentations, and headless environments without a webcam.

---

## 🛠️ Architecture & Tech Stack

```
MOVA/
├── app.py                      # Main Streamlit application entry point & routing
├── config/                     # Settings, environment loading, model endpoints
├── utils/                      # Privacy filters, logging, high-precision timers
├── database/                   # SQLite engine, models, personal baseline repository
├── vision/                     # MediaPipe Tasks vision pipeline & camera manager
├── movement/                   # Kinematics, angle, velocity, trajectory, stability engines
├── multimodal/                 # Spatial intent, gaze-hand fusion, multimodal coordination
├── ml/                         # Adaptive difficulty, pattern classification, recommendations
├── voice/                      # Voice command grammar, STT, ElevenLabs TTS integration
├── games/                      # BaseGame engine & all 10 spatial game implementations
├── ai/                         # Local deterministic, Gemini, and OpenAI AI coaches
├── reports/                    # Session report generation & ReportLab PDF export
├── ui/                         # Streamlit UI modules (Dashboard, Library, Lab, Coach, etc.)
├── tests/                      # Automated unit test suite
└── assets/models/              # MediaPipe task models (Pose, Hand, Face)
```

---

## ⚡ Quick Start

### 1. Requirements
* Python 3.10+ (tested on Python 3.14)
* Webcam (optional — full Demo Mode simulation included)

### 2. Installation
```bash
git clone https://github.com/mova-platform/mova.git
cd MOVA
pip install -r requirements.txt
```

### 3. Run the Platform
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Tests
```bash
python -m unittest tests/test_engines.py
```

---

## 🔒 Privacy & Safety Notice
MOVA strictly processes camera video locally on your device. Video frames are never stored or transmitted to external servers. Any cloud-assisted AI coaching uses structured numeric scalars only. MOVA is designed solely for recreational spatial gaming, fitness awareness, and movement intelligence. It does not provide medical advice, diagnosis, or clinical treatment.

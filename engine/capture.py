"""
MOVA Engine: Unified Camera + MediaPipe Pipeline
Pure OpenCV + MediaPipe Tasks API (no Streamlit).
Provides a single read_frame() call that returns all tracking data.
"""

import cv2
import time
import os
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "assets" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

POSE_MODEL = str(MODEL_DIR / "pose_landmarker_lite.task")
HAND_MODEL = str(MODEL_DIR / "hand_landmarker.task")
FACE_MODEL = str(MODEL_DIR / "face_landmarker.task")

# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class HandData:
    detected: bool = False
    label: str = ""            # "Left" or "Right"
    landmarks: np.ndarray = field(default_factory=lambda: np.zeros((21, 2)))
    landmarks_3d: np.ndarray = field(default_factory=lambda: np.zeros((21, 3)))
    palm_center: Tuple[float, float] = (0.5, 0.5)
    gesture: str = "NONE"
    pinch_distance: float = 1.0
    confidence: float = 0.0

@dataclass
class PoseData:
    detected: bool = False
    landmarks: np.ndarray = field(default_factory=lambda: np.zeros((33, 2)))
    body_center: Tuple[float, float] = (0.5, 0.5)
    torso_lean: float = 0.0       # -1.0 (left) to +1.0 (right)
    confidence: float = 0.0

@dataclass
class FaceData:
    detected: bool = False
    landmarks: np.ndarray = field(default_factory=lambda: np.zeros((478, 2)))
    face_center: Tuple[float, float] = (0.5, 0.5)
    head_yaw: float = 0.0     # degrees, left-right (-left, +right)
    head_pitch: float = 0.0   # degrees, up-down (-down, +up)
    head_roll: float = 0.0    # degrees, tilt (-left, +right)
    is_smiling: bool = False
    mouth_open: bool = False
    smile_score: float = 0.0
    mouth_score: float = 0.0
    gesture: str = "NEUTRAL"  # "SMILE", "MOUTH_OPEN", "HEAD_TILT_LEFT", "HEAD_TILT_RIGHT", "HEAD_NOD", "NEUTRAL"
    confidence: float = 0.0

@dataclass
class FrameData:
    frame: Optional[np.ndarray] = None    # BGR frame
    timestamp: float = 0.0
    dt: float = 0.033
    fps: float = 30.0
    # Tracking
    right_hand: HandData = field(default_factory=HandData)
    left_hand: HandData   = field(default_factory=HandData)
    pose: PoseData         = field(default_factory=PoseData)
    face: FaceData         = field(default_factory=FaceData)
    # Quality
    lighting_ok: bool = True
    lighting_score: float = 1.0


# ─── Camera + MediaPipe Pipeline ─────────────────────────────────────────────
class MOVAPipeline:
    """
    Unified OpenCV + MediaPipe pipeline.
    Usage:
        pipe = MOVAPipeline()
        while True:
            fd = pipe.read()          # FrameData with all tracking
            cv2.imshow("MOVA", fd.frame)
    """
    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720):
        self.camera_index = camera_index
        self.width        = width
        self.height       = height
        self.cap: Optional[cv2.VideoCapture] = None
        self._last_ts = time.perf_counter()
        self._fps_ts: List[float] = []

        # MediaPipe detectors
        self._pose: Optional[vision.PoseLandmarker]    = None
        self._hand: Optional[vision.HandLandmarker]    = None
        self._face: Optional[vision.FaceLandmarker]    = None

        self._init_models()
        self.open()

    # ── Initialisation ─────────────────────────────────────────────────────
    def _init_models(self):
        try:
            if os.path.exists(POSE_MODEL):
                self._pose = vision.PoseLandmarker.create_from_options(
                    vision.PoseLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=POSE_MODEL),
                        running_mode=vision.RunningMode.IMAGE,
                        num_poses=1,
                        min_pose_detection_confidence=0.5,
                        min_pose_presence_confidence=0.5,
                        min_tracking_confidence=0.5,
                    ))
        except Exception as e:
            print(f"[MOVA] PoseLandmarker init failed: {e}")

        try:
            if os.path.exists(HAND_MODEL):
                self._hand = vision.HandLandmarker.create_from_options(
                    vision.HandLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=HAND_MODEL),
                        running_mode=vision.RunningMode.IMAGE,
                        num_hands=2,
                        min_hand_detection_confidence=0.5,
                        min_hand_presence_confidence=0.5,
                        min_tracking_confidence=0.5,
                    ))
        except Exception as e:
            print(f"[MOVA] HandLandmarker init failed: {e}")

        try:
            if os.path.exists(FACE_MODEL):
                self._face = vision.FaceLandmarker.create_from_options(
                    vision.FaceLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=FACE_MODEL),
                        running_mode=vision.RunningMode.IMAGE,
                        output_face_blendshapes=True,
                        min_face_detection_confidence=0.5,
                        min_face_presence_confidence=0.5,
                        min_tracking_confidence=0.5,
                    ))
        except Exception as e:
            print(f"[MOVA] FaceLandmarker init failed: {e}")

        models_ok = sum([self._pose is not None, self._hand is not None, self._face is not None])
        print(f"[MOVA] MediaPipe: {models_ok}/3 models loaded.")

    def open(self) -> bool:
        """Open the physical camera."""
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[MOVA] Camera opened: index={self.camera_index}  {actual_w}×{actual_h}")
            return True
        print(f"[MOVA] ERROR: Cannot open camera index {self.camera_index}")
        return False

    def close(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    # ── FPS ────────────────────────────────────────────────────────────────
    def _update_fps(self) -> float:
        now = time.perf_counter()
        self._fps_ts.append(now)
        if len(self._fps_ts) > 30:
            self._fps_ts.pop(0)
        if len(self._fps_ts) > 1:
            elapsed = self._fps_ts[-1] - self._fps_ts[0]
            if elapsed > 0:
                return (len(self._fps_ts) - 1) / elapsed
        return 30.0

    # ── Lighting ───────────────────────────────────────────────────────────
    @staticmethod
    def _lighting(frame: np.ndarray) -> Tuple[bool, float]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean = float(np.mean(gray))
        score = np.clip(mean / 100.0, 0.0, 1.0)
        ok = 30 < mean < 220
        return ok, round(score, 2)

    # ── Hand processing ───────────────────────────────────────────────────
    def _process_hands(self, mp_img: mp.Image, frame_shape: Tuple) -> Tuple[HandData, HandData]:
        right, left = HandData(), HandData()
        if self._hand is None:
            return right, left
        try:
            res = self._hand.detect(mp_img)
        except Exception:
            return right, left

        h, w = frame_shape[:2]
        for i, (hcat, hlm) in enumerate(zip(res.handedness, res.hand_landmarks)):
            label = hcat[0].display_name  # "Left" or "Right"
            pts_norm = np.array([[lm.x, lm.y] for lm in hlm])      # (21, 2) normalised
            pts_3d   = np.array([[lm.x, lm.y, lm.z] for lm in hlm]) # (21, 3)

            d = HandData(
                detected    = True,
                label       = label,
                landmarks   = pts_norm,
                landmarks_3d= pts_3d,
                palm_center = (float(pts_norm[0, 0]), float(pts_norm[0, 1])),
                confidence  = hcat[0].score,
            )
            if label == "Right":
                right = d
            else:
                left = d
        return right, left

    # ── Pose processing ───────────────────────────────────────────────────
    def _process_pose(self, mp_img: mp.Image) -> PoseData:
        pd = PoseData()
        if self._pose is None:
            return pd
        try:
            res = self._pose.detect(mp_img)
        except Exception:
            return pd
        if not res.pose_landmarks:
            return pd

        lms = res.pose_landmarks[0]
        pts = np.array([[lm.x, lm.y] for lm in lms])  # (33, 2)

        # Body center = midpoint of hips (23=left hip, 24=right hip)
        cx = (pts[23, 0] + pts[24, 0]) / 2.0
        cy = (pts[23, 1] + pts[24, 1]) / 2.0

        # Torso lean: shoulder midpoint x vs hip midpoint x
        shoulder_cx = (pts[11, 0] + pts[12, 0]) / 2.0
        lean = float(np.clip((shoulder_cx - cx) * 4.0, -1.0, 1.0))

        pd.detected    = True
        pd.landmarks   = pts
        pd.body_center = (float(cx), float(cy))
        pd.torso_lean  = lean
        pd.confidence  = float(lms[0].visibility) if hasattr(lms[0], "visibility") else 0.9
        return pd

    # ── Face processing ───────────────────────────────────────────────────
    def _process_face(self, mp_img: mp.Image) -> FaceData:
        fd = FaceData()
        if self._face is None:
            return fd
        try:
            res = self._face.detect(mp_img)
        except Exception:
            return fd
        if not res.face_landmarks:
            return fd

        lms  = res.face_landmarks[0]
        pts  = np.array([[lm.x, lm.y] for lm in lms])  # (478, 2)
        nose = pts[1]   # tip of nose
        chin = pts[152] # chin
        forehead = pts[10] # top of head
        left_eye  = pts[33]
        right_eye = pts[263]
        lip_top = pts[13]
        lip_bot = pts[14]
        mouth_l = pts[61]
        mouth_r = pts[291]

        # Approximate yaw, pitch, roll
        face_cx = float(np.mean(pts[:, 0]))
        face_cy = float(np.mean(pts[:, 1]))
        yaw   = float((nose[0] - face_cx) * 180.0)
        pitch = float((nose[1] - face_cy) * -180.0)

        # Head roll (tilt) via eye slope
        eye_dx = float(right_eye[0] - left_eye[0])
        eye_dy = float(right_eye[1] - left_eye[1])
        roll = float(np.degrees(np.arctan2(eye_dy, eye_dx)))

        # Facial gesture metrics
        face_h = float(np.linalg.norm(forehead - chin)) + 1e-6
        eye_w  = float(np.linalg.norm(left_eye - right_eye)) + 1e-6
        mouth_h = float(np.linalg.norm(lip_top - lip_bot))
        mouth_w = float(np.linalg.norm(mouth_l - mouth_r))

        mouth_ratio = mouth_h / face_h
        smile_ratio = mouth_w / eye_w

        smile_score = float(np.clip((smile_ratio - 0.42) / 0.15, 0.0, 1.0))
        mouth_score = float(np.clip((mouth_ratio - 0.05) / 0.10, 0.0, 1.0))

        # Check blendshapes if available from MediaPipe
        if hasattr(res, "face_blendshapes") and res.face_blendshapes and len(res.face_blendshapes) > 0:
            bs_dict = {b.category_name: b.score for b in res.face_blendshapes[0]}
            bs_smile = max(bs_dict.get("mouthSmileLeft", 0.0), bs_dict.get("mouthSmileRight", 0.0))
            bs_jaw   = bs_dict.get("jawOpen", 0.0)
            smile_score = max(smile_score, bs_smile)
            mouth_score = max(mouth_score, bs_jaw)

        is_smiling = smile_score > 0.45
        mouth_open = mouth_score > 0.38

        # Classify primary face gesture
        if is_smiling:
            gesture = "SMILE"
        elif mouth_open:
            gesture = "MOUTH_OPEN"
        elif roll < -12.0:
            gesture = "HEAD_TILT_LEFT"
        elif roll > 12.0:
            gesture = "HEAD_TILT_RIGHT"
        elif pitch > 18.0:
            gesture = "HEAD_NOD"
        else:
            gesture = "NEUTRAL"

        fd.detected    = True
        fd.landmarks   = pts
        fd.face_center = (face_cx, face_cy)
        fd.head_yaw    = round(yaw, 1)
        fd.head_pitch  = round(pitch, 1)
        fd.head_roll   = round(roll, 1)
        fd.is_smiling  = is_smiling
        fd.mouth_open  = mouth_open
        fd.smile_score = round(smile_score, 2)
        fd.mouth_score = round(mouth_score, 2)
        fd.gesture     = gesture
        fd.confidence  = 0.95
        return fd

    # ── Main read() ───────────────────────────────────────────────────────
    def read(self) -> FrameData:
        """Read one frame and run all MediaPipe detectors. Returns FrameData."""
        now = time.perf_counter()
        dt  = max(0.001, now - self._last_ts)
        self._last_ts = now
        fps = self._update_fps()

        fd = FrameData(timestamp=now, dt=dt, fps=fps)

        if self.cap is None or not self.cap.isOpened():
            fd.frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            return fd

        ret, frame = self.cap.read()
        if not ret:
            fd.frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            return fd

        frame = cv2.flip(frame, 1)  # Mirror for natural interaction
        fd.frame = frame
        lit_ok, lit_score = self._lighting(frame)
        fd.lighting_ok    = lit_ok
        fd.lighting_score = lit_score

        # Build MediaPipe image (RGB)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Run all detectors
        fd.right_hand, fd.left_hand = self._process_hands(mp_img, frame.shape)
        fd.pose  = self._process_pose(mp_img)
        fd.face  = self._process_face(mp_img)

        return fd

    # ── Context manager ───────────────────────────────────────────────────
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

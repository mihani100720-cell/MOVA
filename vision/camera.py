"""
MOVA Vision Pipeline & Camera Manager — Threaded Architecture v2
 - CaptureThread: only calls cv2.read() at hardware speed
 - InferenceThread: runs all 3 MediaPipe models; publishes UnifiedFrameData
 - read_frame(): non-blocking, returns the latest processed result instantly
"""

import cv2
import time
import os
import threading
import queue
import urllib.request
import numpy as np
from pathlib import Path
from typing import Optional

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from config.settings import settings
from utils.logger import logger
from vision.confidence import QualityEvaluator
from vision.pose_tracker import PoseTracker, PoseData
from vision.hand_tracker import HandTracker, HandTrackingResult
from vision.face_tracker import FaceTracker, FaceData
from vision.eye_tracker import EyeTracker, EyeTrackingData


# ─────────────────────────────────────────────────────────────────────────────
class UnifiedFrameData:
    """Aggregated perception state for a single video frame."""
    def __init__(self, timestamp: float = 0.0):
        self.timestamp: float = timestamp
        self.dt: float = 0.033
        self.frame: Optional[np.ndarray] = None
        self.lighting_score: float = 1.0
        self.lighting_status: str = "Optimal"
        self.is_demo_mode: bool = False
        self.camera_active: bool = False

        # Modalities
        self.pose: PoseData = PoseData()
        self.hands: HandTrackingResult = HandTrackingResult()
        self.face: FaceData = FaceData()
        self.eyes: EyeTrackingData = EyeTrackingData()

        self.overall_confidence: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
class CameraManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CameraManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, camera_index: int = 0):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_demo_mode: bool = settings.DEMO_MODE_DEFAULT
        self.simulated_t: float = 0.0

        # Trackers (used in inference thread)
        self.pose_tracker = PoseTracker()
        self.hand_tracker = HandTracker()
        self.face_tracker = FaceTracker()
        self.eye_tracker = EyeTracker()

        # MediaPipe detectors
        self.pose_detector = None
        self.hand_detector = None
        self.face_detector = None
        self.models_ready: bool = False

        # ── Threading ────────────────────────────────────────────────────────
        # Bounded queue: capture thread → inference thread (max 2 frames deep)
        self._raw_queue: queue.Queue = queue.Queue(maxsize=2)
        # Latest fully processed frame, guarded by lock
        self._latest_frame: Optional[UnifiedFrameData] = None
        self._frame_lock = threading.Lock()
        # dt tracking for the UI caller
        self._last_ui_ts: float = time.perf_counter()

        self._capture_thread: Optional[threading.Thread] = None
        self._inference_thread: Optional[threading.Thread] = None
        self._threads_running: bool = False

        self._init_models()
        self._initialized = True

    # ── Model management ──────────────────────────────────────────────────────
    def _ensure_model_exists(self, filename: str, url: str) -> str:
        dest = settings.MODELS_DIR / filename
        if not dest.exists():
            logger.info(f"Downloading model {filename}…")
            try:
                urllib.request.urlretrieve(url, str(dest))
                logger.info(f"Model {filename} downloaded.")
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
        return str(dest)

    def _init_models(self):
        try:
            pose_path = self._ensure_model_exists(
                "pose_landmarker_lite.task",
                "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
            )
            hand_path = self._ensure_model_exists(
                "hand_landmarker.task",
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )
            face_path = self._ensure_model_exists(
                "face_landmarker.task",
                "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
            )

            if os.path.exists(pose_path):
                self.pose_detector = vision.PoseLandmarker.create_from_options(
                    vision.PoseLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=pose_path),
                        running_mode=vision.RunningMode.IMAGE
                    )
                )
            if os.path.exists(hand_path):
                self.hand_detector = vision.HandLandmarker.create_from_options(
                    vision.HandLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=hand_path),
                        num_hands=2,
                        running_mode=vision.RunningMode.IMAGE
                    )
                )
            if os.path.exists(face_path):
                self.face_detector = vision.FaceLandmarker.create_from_options(
                    vision.FaceLandmarkerOptions(
                        base_options=python.BaseOptions(model_asset_path=face_path),
                        output_face_blendshapes=True,
                        running_mode=vision.RunningMode.IMAGE
                    )
                )

            self.models_ready = True
            logger.info("MediaPipe tasks pipeline ready.")
        except Exception as e:
            logger.error(f"MediaPipe init error: {e}. Fallbacks active.")
            self.models_ready = False

    # ── Background threads ────────────────────────────────────────────────────
    def _capture_loop(self):
        """Thread A: reads raw BGR frames from hardware as fast as possible."""
        while self._threads_running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.05)
                continue
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            # Drop stale frame so inference always works on the newest one
            if self._raw_queue.full():
                try:
                    self._raw_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                self._raw_queue.put_nowait((time.perf_counter(), frame))
            except queue.Full:
                pass

    def _inference_loop(self):
        """Thread B: runs MediaPipe on raw frames; publishes UnifiedFrameData."""
        _last_ts = time.perf_counter()
        while self._threads_running:
            try:
                ts, raw_frame = self._raw_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            dt = max(0.001, ts - _last_ts)
            _last_ts = ts

            fd = UnifiedFrameData(timestamp=ts)
            fd.dt = dt
            fd.camera_active = True

            frame = cv2.flip(raw_frame, 1)
            fd.frame = frame

            score, status = QualityEvaluator.evaluate_frame_lighting(frame)
            fd.lighting_score = score
            fd.lighting_status = status

            if self.models_ready:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    rgb_small = cv2.resize(rgb, (320, 240))
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_small)

                    if self.pose_detector:
                        p_res = self.pose_detector.detect(mp_img)
                        fd.pose = self.pose_tracker.extract_from_mediapipe(p_res)

                    if self.hand_detector:
                        h_res = self.hand_detector.detect(mp_img)
                        fd.hands = self.hand_tracker.process_mediapipe_result(h_res, dt)

                    if self.face_detector:
                        f_res = self.face_detector.detect(mp_img)
                        fd.face = self.face_tracker.process_mediapipe_result(f_res)
                        if f_res and f_res.face_landmarks:
                            fd.eyes = self.eye_tracker.process_face_data(
                                f_res.face_landmarks[0], fd.face.blendshapes, dt
                            )
                except Exception as e:
                    logger.error(f"Inference error: {e}")

            c_vals = []
            if fd.pose.detected: c_vals.append(fd.pose.confidence)
            if fd.hands.hands_count > 0: c_vals.append(0.9)
            if fd.face.detected: c_vals.append(fd.face.confidence)
            fd.overall_confidence = float(np.mean(c_vals)) if c_vals else 0.0

            with self._frame_lock:
                self._latest_frame = fd

    def _start_threads(self):
        if self._threads_running:
            return
        self._threads_running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="MOVA-Capture"
        )
        self._inference_thread = threading.Thread(
            target=self._inference_loop, daemon=True, name="MOVA-Inference"
        )
        self._capture_thread.start()
        self._inference_thread.start()
        logger.info("Capture + Inference threads started.")

    def _stop_threads(self):
        self._threads_running = False
        while not self._raw_queue.empty():
            try: self._raw_queue.get_nowait()
            except: pass
        with self._frame_lock:
            self._latest_frame = None

    # ── Public API ────────────────────────────────────────────────────────────
    def start_camera(self) -> bool:
        self.is_demo_mode = False
        if self.cap is None or not self.cap.isOpened():
            self.stop_camera()
            self.cap = cv2.VideoCapture(
                self.camera_index,
                cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            )
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self._start_threads()
                return True
            else:
                logger.warning(f"Could not open camera {self.camera_index}. Demo Mode.")
                self.is_demo_mode = True
                return False
        else:
            self._start_threads()
            return True

    def stop_camera(self):
        self._stop_threads()
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def set_demo_mode(self, enabled: bool):
        self.is_demo_mode = enabled
        if enabled:
            self.stop_camera()
        else:
            self.start_camera()

    def read_frame(self) -> UnifiedFrameData:
        """
        Non-blocking read. Returns latest inference result immediately.
        Falls back to simulated frames in demo / no-camera mode.
        """
        now = time.perf_counter()
        dt = max(0.001, now - self._last_ui_ts)
        self._last_ui_ts = now

        # ── Demo / no camera path ─────────────────────────────────────────────
        if self.is_demo_mode or self.cap is None or not self.cap.isOpened():
            self.simulated_t += dt
            fd = UnifiedFrameData(timestamp=now)
            fd.dt = dt
            fd.is_demo_mode = True
            fd.camera_active = False
            fd.lighting_status = "Demo Mode Simulation"

            sim_img = np.zeros((480, 640, 3), dtype=np.uint8)
            for y in range(480):
                sim_img[y, :, :] = (int(16 + y * 0.02), int(14 + y * 0.01), int(28 + y * 0.04))
            fd.frame = sim_img
            fd.pose = self.pose_tracker.create_simulated(self.simulated_t)
            fd.hands = self.hand_tracker.create_simulated(self.simulated_t)
            fd.face = self.face_tracker.create_simulated(self.simulated_t)
            fd.eyes = self.eye_tracker.create_simulated(self.simulated_t)
            fd.overall_confidence = 0.99
            return fd

        # ── Live path: snapshot latest processed frame ────────────────────────
        with self._frame_lock:
            fd = self._latest_frame

        if fd is None:
            # Threads warming up — return blank placeholder
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            fd = UnifiedFrameData(timestamp=now)
            fd.dt = dt
            fd.frame = blank
            fd.camera_active = True
            fd.lighting_status = "Camera warming up…"
        else:
            fd.dt = dt

        return fd


camera_manager = CameraManager()

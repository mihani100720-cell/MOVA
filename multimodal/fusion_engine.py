"""
MOVA Multimodal Fusion Engine
Implements Section 9, 21, 22, 53:
Unifies Eyes + Face + Hands + Arms + Body + Voice into coherent Spatial Intent and Multimodal Coordination Score.
Fully composable: games declare required and optional modalities.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from multimodal.intent_engine import SpatialIntentEngine
from multimodal.gaze_hand_fusion import GazeHandFusion
from multimodal.gesture_body_fusion import GestureBodyFusion, VoiceGestureFusion

class MultimodalFusionEngine:
    def __init__(self):
        self.intent_engine = SpatialIntentEngine()
        self.gaze_hand = GazeHandFusion()
        self.gesture_body = GestureBodyFusion()
        self.voice_gesture = VoiceGestureFusion()

        # Session tracking
        self.multimodal_sync_scores: List[float] = []
        self.eye_hand_latencies: List[float] = []

    def fuse_frame(self, frame_data, movement_metrics: Dict[str, Any],
                   required_modalities: Optional[List[str]] = None,
                   active_target_pos: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Fuses modalities for current game step.
        """
        req = required_modalities or ["hands", "body"]
        now = frame_data.timestamp

        # Extract primary signals
        gaze_coords = frame_data.eyes.gaze_target_coords
        gaze_dir = frame_data.eyes.gaze_direction
        face_center = frame_data.face.face_center
        head_yaw = frame_data.face.head_yaw

        # Hands
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        primary_hand = rh if rh.detected else (lh if lh.detected else None)

        hand_pos = primary_hand.palm_center if primary_hand else (0.5, 0.7)
        hand_gesture = primary_hand.gesture if primary_hand else "neutral"
        hand_speed = primary_hand.speed if primary_hand else 0.0

        # Body
        body_center = frame_data.pose.body_center if frame_data.pose.detected else (0.5, 0.5)
        torso_tilt = frame_data.pose.torso_tilt if frame_data.pose.detected else 0.0
        stability_score = movement_metrics.get("stability", {}).get("stability_score", 90.0)

        # 1. Resolve Spatial Intent
        intent = self.intent_engine.estimate_intent_target(
            gaze_target=gaze_coords,
            hand_pos=hand_pos,
            hand_gesture=hand_gesture,
            head_yaw=head_yaw,
            face_center=face_center
        )

        # 2. Eye-Hand Coordination Step
        eye_hand_res = {}
        if "eyes" in req and "hands" in req and active_target_pos:
            eye_hand_res = self.gaze_hand.evaluate_step(
                gaze_pos=gaze_coords,
                hand_pos=hand_pos,
                hand_speed=hand_speed,
                timestamp=now
            )
            if eye_hand_res.get("completed"):
                self.eye_hand_latencies.append(eye_hand_res["gaze_to_hand_latency"])

        # 3. Hand-Body Reach Integration
        hand_body_res = self.gesture_body.evaluate_reach_posture(
            hand_reach_x=hand_pos[0],
            body_tilt_deg=torso_tilt,
            stability_score=stability_score
        )

        # 4. Multimodal Synchronization Score [0..100]
        # Evaluates alignment across requested modalities
        sync_components = []
        if "hands" in req:
            sync_components.append(1.0 if primary_hand and primary_hand.detected else 0.0)
        if "eyes" in req:
            sync_components.append(1.0 if frame_data.eyes.detected else 0.5)
        if "body" in req:
            sync_components.append(min(1.0, stability_score / 100.0))
        if "face" in req:
            sync_components.append(1.0 if frame_data.face.detected else 0.5)

        # Intent confidence component
        sync_components.append(intent["intent_confidence"])

        sync_score = round(float(np.mean(sync_components)) * 100.0, 1) if sync_components else 90.0
        self.multimodal_sync_scores.append(sync_score)

        return {
            "intent": intent,
            "eye_hand": eye_hand_res,
            "hand_body": hand_body_res,
            "multimodal_sync_score": sync_score,
            "modalities_status": {
                "eyes": frame_data.eyes.detected,
                "hands": (rh.detected or lh.detected),
                "body": frame_data.pose.detected,
                "face": frame_data.face.detected
            }
        }

    def notify_target_spawn(self, target_pos: Tuple[float, float], timestamp: float):
        self.gaze_hand.on_target_spawned(target_pos, timestamp)

    def get_session_summary(self) -> Dict[str, Any]:
        return self.get_session_fusion_summary()

    def get_session_fusion_summary(self) -> Dict[str, Any]:
        avg_sync = float(np.mean(self.multimodal_sync_scores)) if self.multimodal_sync_scores else 85.0
        avg_gaze_hand = float(np.mean(self.eye_hand_latencies)) if self.eye_hand_latencies else 0.25
        return {
            "avg_multimodal_coordination": round(avg_sync, 1),
            "avg_gaze_to_hand_latency": round(avg_gaze_hand, 3)
        }

    def reset_session(self):
        self.multimodal_sync_scores.clear()
        self.eye_hand_latencies.clear()

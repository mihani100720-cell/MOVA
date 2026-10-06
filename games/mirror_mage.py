"""
GAME 09 — MIRROR MAGE 🪞
Concept: Ultimate multimodal coordination showcase.
A progressive sequence of sensory-motor actions appears on screen (e.g. LOOK LEFT -> RIGHT HAND UP -> HEAD TURN RIGHT -> BOTH HANDS OPEN).
User reproduces the sequence in order. Tests multimodal synchronization and sequence working memory.
Inputs: Eyes, Face, Hands, Arms, Body
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class MirrorMageGame(BaseGame):
    ACTIONS_POOL = [
        {"id": "LOOK_LEFT", "desc": "LOOK LEFT 👀", "modality": "eyes"},
        {"id": "LOOK_RIGHT", "desc": "LOOK RIGHT 👀", "modality": "eyes"},
        {"id": "RIGHT_HAND_UP", "desc": "RIGHT HAND UP 🖐️", "modality": "hands"},
        {"id": "LEFT_HAND_UP", "desc": "LEFT HAND UP 🖐️", "modality": "hands"},
        {"id": "HEAD_TURN_RIGHT", "desc": "TURN HEAD RIGHT 😊", "modality": "face"},
        {"id": "HEAD_TURN_LEFT", "desc": "TURN HEAD LEFT 😊", "modality": "face"},
        {"id": "BOTH_HANDS_OPEN", "desc": "BOTH HANDS OPEN 👐", "modality": "hands"},
        {"id": "PINCH_RIGHT", "desc": "PINCH RIGHT HAND 🤏", "modality": "hands"},
        {"id": "LEAN_LEFT", "desc": "LEAN TORSO LEFT 🧍", "modality": "body"},
        {"id": "LEAN_RIGHT", "desc": "LEAN TORSO RIGHT 🧍", "modality": "body"}
    ]

    def __init__(self):
        super().__init__(game_id="mirror_mage", game_name="Mirror Mage 🪞", duration_sec=50.0)
        self.required_modalities = ["eyes", "face", "hands", "arms", "body"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Full Multimodal Synchronization & Sequence Memory"

        self.sequence: List[Dict[str, str]] = []
        self.current_step: int = 0
        self.sequences_completed: int = 0
        self.hold_timer: float = 0.0
        self.action_start_time: float = 0.0

    def on_start(self):
        self.sequences_completed = 0
        self.hold_timer = 0.0
        self.action_start_time = self.elapsed_time
        self._generate_sequence(length=3)

    def on_stop(self):
        pass

    def _generate_sequence(self, length: int = 3):
        import random
        self.sequence = [random.choice(self.ACTIONS_POOL) for _ in range(length)]
        self.current_step = 0
        self.hold_timer = 0.0
        self.action_start_time = self.elapsed_time
        self._update_objective()

    def _update_objective(self):
        if self.current_step < len(self.sequence):
            act = self.sequence[self.current_step]
            self.objective_text = f"Mirror Step {self.current_step + 1}/{len(self.sequence)}: {act['desc']}"

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        if self.current_step >= len(self.sequence):
            return

        target_act = self.sequence[self.current_step]["id"]
        matched = False

        # Evaluation against active perception
        gaze_dir = frame_data.eyes.gaze_direction
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        head_yaw = frame_data.face.head_yaw
        tilt = frame_data.pose.torso_tilt

        if target_act == "LOOK_LEFT" and (gaze_dir == "LEFT" or frame_data.eyes.gaze_target_coords[0] < 0.35):
            matched = True
        elif target_act == "LOOK_RIGHT" and (gaze_dir == "RIGHT" or frame_data.eyes.gaze_target_coords[0] > 0.65):
            matched = True
        elif target_act == "RIGHT_HAND_UP" and rh.detected and rh.palm_center[1] < 0.40:
            matched = True
        elif target_act == "LEFT_HAND_UP" and lh.detected and lh.palm_center[1] < 0.40:
            matched = True
        elif target_act == "HEAD_TURN_RIGHT" and head_yaw > 12.0:
            matched = True
        elif target_act == "HEAD_TURN_LEFT" and head_yaw < -12.0:
            matched = True
        elif target_act == "BOTH_HANDS_OPEN" and rh.detected and lh.detected and rh.is_open_palm and lh.is_open_palm:
            matched = True
        elif target_act == "PINCH_RIGHT" and rh.detected and (rh.is_pinching or rh.gesture == "pinch"):
            matched = True
        elif target_act == "LEAN_LEFT" and tilt < -10.0:
            matched = True
        elif target_act == "LEAN_RIGHT" and tilt > 10.0:
            matched = True

        if matched:
            self.hold_timer += dt
            if self.hold_timer >= 0.45:  # Must hold posture for 0.45s to confirm deliberate match
                self.current_step += 1
                self.hold_timer = 0.0
                react = max(0.4, self.elapsed_time - self.action_start_time)
                self.record_hit(reaction_time=react, accuracy=1.0, points=180)
                self.action_start_time = self.elapsed_time

                # Check if full sequence completed
                if self.current_step >= len(self.sequence):
                    self.sequences_completed += 1
                    # Progressively increase sequence length
                    new_len = min(5, 3 + (self.sequences_completed // 2))
                    self._generate_sequence(length=new_len)
                else:
                    self._update_objective()
        else:
            self.hold_timer = max(0.0, self.hold_timer - dt * 2.0)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Mirror Frame border
        cv2.rectangle(frame, (25, 65), (width - 25, height - 35), (200, 160, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "MIRROR REALM", (width // 2 - 80, 92),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (220, 200, 255), 1, cv2.LINE_AA)

        # Draw Full Sequence Bubbles
        total = len(self.sequence)
        start_x = width // 2 - (total * 65) // 2
        for i, act in enumerate(self.sequence):
            bx = start_x + i * 65 + 30
            by = 135
            is_curr = (i == self.current_step)
            is_done = (i < self.current_step)

            color = (0, 255, 120) if is_done else ((0, 220, 255) if is_curr else (100, 100, 140))
            cv2.circle(frame, (bx, by), 24, color, 2 if not is_curr else -1, cv2.LINE_AA)
            if is_curr:
                # Hold circle animation
                hold_angle = int(360 * min(1.0, self.hold_timer / 0.45))
                cv2.ellipse(frame, (bx, by), (30, 30), 0, 0, hold_angle, (255, 255, 255), 3, cv2.LINE_AA)

            cv2.putText(frame, str(i + 1), (bx - 5, by + 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"sequences_completed": self.sequences_completed}

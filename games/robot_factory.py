"""
GAME 07 — ROBOT FACTORY 🤖
Concept: Precision multimodal sequential assembly line.
User executes the mandatory sequence: LOOK -> POINT -> GRAB -> MOVE -> RELEASE
to assemble cybernetic robot components into the chassis.
Inputs: Hands, Arms, Eyes, Voice
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class RobotFactoryGame(BaseGame):
    STEPS = ["LOOK", "POINT", "GRAB", "MOVE", "RELEASE"]

    def __init__(self):
        super().__init__(game_id="robot_factory", game_name="Robot Factory 🤖", duration_sec=45.0)
        self.required_modalities = ["hands", "arms", "eyes"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Sequential Multimodal Flow (Gaze -> Gesture -> Placement)"

        self.current_step_idx: int = 0
        self.part_pos = [0.25, 0.45]
        self.chassis_pos = [0.75, 0.45]
        self.robots_built: int = 0
        self.sequence_step_time: float = 0.0

    def on_start(self):
        self.current_step_idx = 0
        self.robots_built = 0
        self.part_pos = [0.25, 0.45]
        self.sequence_step_time = self.elapsed_time
        self._update_objective()

    def on_stop(self):
        pass

    def _update_objective(self):
        step_name = self.STEPS[self.current_step_idx]
        if step_name == "LOOK":
            self.objective_text = "1. LOOK: Fixate your gaze onto the robot power core on the left!"
        elif step_name == "POINT":
            self.objective_text = "2. POINT: Extend index finger to target the power core!"
        elif step_name == "GRAB":
            self.objective_text = "3. GRAB: Form a fist or pinch to secure the component!"
        elif step_name == "MOVE":
            self.objective_text = "4. MOVE: Carry the component across to the chassis on the right!"
        elif step_name == "RELEASE":
            self.objective_text = "5. RELEASE: Open your palm to install the component!"

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        hand = rh if rh.detected else (lh if lh.detected else None)
        gaze = frame_data.eyes.gaze_target_coords

        step_name = self.STEPS[self.current_step_idx]

        if step_name == "LOOK":
            dist_gaze = np.hypot(gaze[0] - self.part_pos[0], gaze[1] - self.part_pos[1])
            if dist_gaze < 0.20:
                self._advance_step()

        elif step_name == "POINT" and hand:
            dist_hand = np.hypot(hand.palm_center[0] - self.part_pos[0], hand.palm_center[1] - self.part_pos[1])
            if dist_hand < 0.15 and hand.gesture in ("point", "neutral", "open_palm"):
                self._advance_step()

        elif step_name == "GRAB" and hand:
            dist_hand = np.hypot(hand.palm_center[0] - self.part_pos[0], hand.palm_center[1] - self.part_pos[1])
            if dist_hand < 0.12 and (hand.is_pinching or hand.gesture in ("fist", "pinch")):
                self._advance_step()

        elif step_name == "MOVE" and hand:
            # Component follows hand
            self.part_pos[0] = hand.palm_center[0]
            self.part_pos[1] = hand.palm_center[1]
            dist_chassis = np.hypot(hand.palm_center[0] - self.chassis_pos[0], hand.palm_center[1] - self.chassis_pos[1])
            if dist_chassis < 0.14:
                self._advance_step()

        elif step_name == "RELEASE" and hand:
            if hand.is_open_palm or hand.gesture in ("open_palm", "neutral"):
                self.robots_built += 1
                reaction = max(0.4, self.elapsed_time - self.sequence_step_time)
                self.record_hit(reaction_time=reaction, accuracy=0.95, points=300)
                # Reset for next robot part
                self.part_pos = [0.25, 0.45]
                self.current_step_idx = 0
                self._update_objective()

    def _advance_step(self):
        self.current_step_idx += 1
        self.sequence_step_time = self.elapsed_time
        self._update_objective()

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Step Sequence Banner
        seq_text = " -> ".join([f"[{s}]" if i == self.current_step_idx else s for i, s in enumerate(self.STEPS)])
        cv2.putText(frame, seq_text, (width // 2 - 200, 95),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 240, 255), 1, cv2.LINE_AA)

        # Draw Robot Chassis on Right
        cx, cy = int(self.chassis_pos[0] * width), int(self.chassis_pos[1] * height)
        cv2.rectangle(frame, (cx - 50, cy - 60), (cx + 50, cy + 60), (80, 80, 100), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (cx - 50, cy - 60), (cx + 50, cy + 60), (0, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(frame, "CHASSIS", (cx - 32, cy - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        # Draw Component Part
        px, py = int(self.part_pos[0] * width), int(self.part_pos[1] * height)
        cv2.circle(frame, (px, py), 26, (255, 160, 40), -1, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 30, (255, 220, 100), 2, cv2.LINE_AA)
        cv2.putText(frame, "CORE", (px - 18, py + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    def handle_input(self, command: str):
        if command in ("grab_part", "activate_portal") and self.STEPS[self.current_step_idx] == "GRAB":
            self._advance_step()

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"robots_built": self.robots_built}

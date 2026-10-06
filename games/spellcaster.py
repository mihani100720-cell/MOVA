"""
GAME 04 — SPELLCASTER 🪄
Concept: Magical glyph tracing game. User draws arcane patterns (CIRCLE, ZIGZAG, TRIANGLE, HORIZONTAL)
in space using hand/arm trajectory, then casts the spell with a release gesture or voice command.
Inputs: Hands, Arms, Optional Voice
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame
from movement.trajectory_engine import TrajectoryEngine

class SpellcasterGame(BaseGame):
    SPELL_PATTERNS = ["CIRCLE", "HORIZONTAL", "ZIGZAG", "TRIANGLE"]

    def __init__(self):
        super().__init__(game_id="spellcaster", game_name="Spellcaster 🪄", duration_sec=45.0)
        self.required_modalities = ["hands", "arms"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Glyph Trajectory & Gesture Precision"

        self.current_spell_idx: int = 0
        self.current_pattern: str = "CIRCLE"
        self.trajectory_tracer = TrajectoryEngine(max_points=80)
        self.spells_cast: int = 0
        self.match_score: float = 0.0
        self.drawing_active: bool = False

    def on_start(self):
        self.spells_cast = 0
        self.current_spell_idx = 0
        self.current_pattern = self.SPELL_PATTERNS[0]
        self.trajectory_tracer.clear()
        self.match_score = 0.0
        self.drawing_active = False
        self.objective_text = f"Draw the [{self.current_pattern}] glyph in the air with your hand!"

    def on_stop(self):
        pass

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        active_hand = rh if rh.detected else (lh if lh.detected else None)

        if not active_hand:
            return

        hx, hy = active_hand.palm_center
        # Draw while pointing or moving
        is_drawing = active_hand.gesture in ("point", "fist", "open_palm") or active_hand.speed > 0.15

        if is_drawing:
            self.trajectory_tracer.add_point((hx, hy))
            self.drawing_active = True

            pts = self.trajectory_tracer.get_trail()
            if len(pts) >= 15:
                # Continuously evaluate match similarity
                sim = TrajectoryEngine.match_glyph(pts, self.current_pattern)
                self.match_score = sim

                # Threshold to complete spell
                if sim >= 0.78:
                    self._cast_successful_spell()
        else:
            if len(self.trajectory_tracer.get_trail()) > 5:
                # Reset if stopped without completion
                self.trajectory_tracer.clear()
                self.drawing_active = False

    def _cast_successful_spell(self):
        self.spells_cast += 1
        acc = round(min(1.0, self.match_score), 2)
        self.record_hit(reaction_time=1.2, accuracy=acc, points=220)
        self.trajectory_tracer.clear()

        # Advance spell pattern
        self.current_spell_idx = (self.current_spell_idx + 1) % len(self.SPELL_PATTERNS)
        self.current_pattern = self.SPELL_PATTERNS[self.current_spell_idx]
        self.objective_text = f"Awesome cast! Next Glyph: [{self.current_pattern}]"

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Target Glyph Guide in Center
        cx, cy = width // 2, height // 2
        cv2.putText(frame, f"SPELL: {self.current_pattern}", (cx - 100, 95),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 180, 50), 2, cv2.LINE_AA)

        # Draw glyph reference outline
        self._render_glyph_guide(frame, cx, cy, self.current_pattern)

        # Draw user's luminous drawn trail
        trail = self.trajectory_tracer.get_trail()
        if len(trail) >= 2:
            for i in range(1, len(trail)):
                p1 = (int(trail[i-1][0] * width), int(trail[i-1][1] * height))
                p2 = (int(trail[i][0] * width), int(trail[i][1] * height))
                alpha = i / len(trail)
                thickness = int(3 + alpha * 5)
                color = (int(255 * alpha), int(200 * alpha), 255)
                cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)

        # Draw match progress meter
        bar_w = 200
        bar_h = 14
        bx = cx - bar_w // 2
        by = height - 45
        cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (40, 40, 60), -1)
        fill_w = int(bar_w * self.match_score)
        fill_color = (0, 255, 120) if self.match_score >= 0.75 else (0, 180, 255)
        cv2.rectangle(frame, (bx, by), (bx + fill_w, by + bar_h), fill_color, -1)
        cv2.putText(frame, f"Arcane Resonance: {int(self.match_score * 100)}%", (bx + 15, by - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 255), 1)

    def _render_glyph_guide(self, frame: np.ndarray, cx: int, cy: int, pattern: str):
        color = (120, 100, 160)
        if pattern == "CIRCLE":
            cv2.circle(frame, (cx, cy), 70, color, 2, cv2.LINE_AA)
        elif pattern == "HORIZONTAL":
            cv2.line(frame, (cx - 80, cy), (cx + 80, cy), color, 3, cv2.LINE_AA)
        elif pattern == "TRIANGLE":
            pts = np.array([[cx, cy - 70], [cx + 70, cy + 60], [cx - 70, cy + 60]], np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_AA)
        elif pattern == "ZIGZAG":
            pts = np.array([[cx - 70, cy - 50], [cx, cy - 20], [cx - 60, cy + 20], [cx + 60, cy + 50]], np.int32)
            cv2.polylines(frame, [pts], isClosed=False, color=color, thickness=2, lineType=cv2.LINE_AA)

    def handle_input(self, command: str):
        if command == "cast_spell" and self.match_score >= 0.60:
            self._cast_successful_spell()

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"glyph_accuracy": self.match_score, "spells_cast": self.spells_cast}

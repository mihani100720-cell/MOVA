"""
MOVA Base Game Framework
Implements Section 12, 16, 17:
Lifecycle methods, mode handling (EXPLORE, CHALLENGE, EXTREME, ASSESSMENT),
practice mode mechanics, and standard result emission.
"""

from abc import ABC, abstractmethod
from enum import Enum
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2

from database.models import StandardGameResult
from ml.difficulty_engine import AdaptiveDifficultyEngine

class GameMode(Enum):
    EXPLORE = "EXPLORE"
    CHALLENGE = "CHALLENGE"
    EXTREME = "EXTREME"
    ASSESSMENT = "ASSESSMENT"
    PRACTICE = "PRACTICE"

class GameState(Enum):
    READY = "READY"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class BaseGame(ABC):
    def __init__(self, game_id: str, game_name: str, duration_sec: float = 45.0):
        self.game_id: str = game_id
        self.game_name: str = game_name
        self.target_duration: float = duration_sec

        # Modalities
        self.required_modalities: List[str] = ["hands", "body"]
        self.optional_modalities: List[str] = ["eyes", "voice"]
        self.movement_focus: str = "Multimodal Spatial Coordination"

        # State & Mode
        self.state: GameState = GameState.READY
        self.mode: GameMode = GameMode.CHALLENGE
        self.elapsed_time: float = 0.0
        self.start_timestamp: float = 0.0

        # Scoring & HUD
        self.score: int = 0
        self.combo: int = 0
        self.max_combo: int = 0
        self.objective_text: str = "Engage Targets"

        # Adaptive Difficulty (Section 25)
        self.difficulty_engine = AdaptiveDifficultyEngine(base_level=1.0)
        self.difficulty_start: float = 1.0

        # Target Tracking & Metrics
        self.targets_attempted: int = 0
        self.targets_successful: int = 0
        self.reaction_times: List[float] = []
        self.accuracies: List[float] = []

    def set_mode(self, mode: GameMode):
        self.mode = mode
        if mode == GameMode.EXPLORE:
            self.difficulty_engine.current_level = 0.7
        elif mode == GameMode.CHALLENGE:
            self.difficulty_engine.current_level = 1.0
        elif mode == GameMode.EXTREME:
            self.difficulty_engine.current_level = 2.0
        elif mode == GameMode.PRACTICE:
            self.difficulty_engine.current_level = 0.5

    def start(self):
        self.state = GameState.PLAYING
        self.start_timestamp = time.perf_counter()
        self.elapsed_time = 0.0
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.targets_attempted = 0
        self.targets_successful = 0
        self.reaction_times.clear()
        self.accuracies.clear()
        self.difficulty_start = self.difficulty_engine.current_level
        self.on_start()

    def pause(self):
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED

    def resume(self):
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def stop(self):
        self.state = GameState.COMPLETED
        self.on_stop()

    def update_lifecycle(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        if self.state != GameState.PLAYING:
            return

        self.elapsed_time += dt
        if self.mode != GameMode.PRACTICE and self.elapsed_time >= self.target_duration:
            self.stop()
            return

        # Let game subclass update internal objects and logic
        self.update(dt, frame_data, movement_metrics, fusion_result)

    def record_hit(self, reaction_time: float, accuracy: float, points: int = 100):
        self.targets_attempted += 1
        self.targets_successful += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        combo_bonus = min(3.0, 1.0 + (self.combo * 0.1))
        earned = int(points * combo_bonus * self.difficulty_engine.current_level)
        self.score += earned

        if reaction_time > 0:
            self.reaction_times.append(reaction_time)
        self.accuracies.append(accuracy)

        if self.mode == GameMode.CHALLENGE:
            self.difficulty_engine.record_hit(reaction_time, accuracy)

    def record_miss(self):
        self.targets_attempted += 1
        self.combo = 0
        self.accuracies.append(0.0)
        if self.mode == GameMode.CHALLENGE:
            self.difficulty_engine.record_miss()

    def calculate_score(self) -> int:
        return self.score

    def get_results(self, session_id: str, movement_summary: Dict[str, Any], fusion_summary: Dict[str, Any]) -> StandardGameResult:
        mean_reaction = float(np.mean(self.reaction_times)) if self.reaction_times else movement_summary.get("avg_reaction_time", 0.7)
        mean_acc = float(np.mean(self.accuracies)) if self.accuracies else (
            (self.targets_successful / max(1, self.targets_attempted)) if self.targets_attempted > 0 else 0.8
        )
        mean_acc = round(float(np.clip(mean_acc, 0.0, 1.0)), 2)

        return StandardGameResult(
            game_id=self.game_id,
            game_name=self.game_name,
            duration=round(self.elapsed_time, 1),
            score=self.score,
            accuracy=mean_acc,
            reaction_time=round(mean_reaction, 3),
            movement_score=round(movement_summary.get("avg_speed", 0.0) * 100.0, 1),
            repetitions=movement_summary.get("total_repetitions", 0),
            left_right_balance=movement_summary.get("avg_symmetry", 0.85),
            stability_score=movement_summary.get("avg_stability", 90.0),
            gaze_accuracy=round(float(fusion_summary.get("avg_multimodal_coordination", 85.0) / 100.0), 2),
            gesture_accuracy=mean_acc,
            coordination_score=fusion_summary.get("avg_multimodal_coordination", 85.0),
            multimodal_coordination=fusion_summary.get("avg_multimodal_coordination", 85.0),
            difficulty_start=self.difficulty_start,
            difficulty_end=self.difficulty_engine.current_level,
            targets_attempted=self.targets_attempted,
            targets_successful=self.targets_successful,
            session_id=session_id,
            modalities_used=self.required_modalities + self.optional_modalities,
            extra_metrics=self.get_extra_metrics()
        )

    def draw_universal_hud(self, frame: np.ndarray, width: int, height: int):
        """
        Universal clean HUD (Section 18):
        SCORE | COMBO | TIME | OBJECTIVE.
        """
        # Top banner with gradient background
        banner_h = 55
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, banner_h), (12, 10, 24), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Bottom subtle border line
        cv2.line(frame, (0, banner_h), (width, banner_h), (80, 70, 140), 1)

        # 1. SCORE
        cv2.putText(frame, f"SCORE {self.score:,}", (20, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 235, 100), 2, cv2.LINE_AA)

        # 2. COMBO
        combo_color = (100, 255, 150) if self.combo > 2 else (200, 200, 220)
        cv2.putText(frame, f"COMBO x{self.combo}", (220, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, combo_color, 2, cv2.LINE_AA)

        # 3. TIME
        remaining = max(0, int(self.target_duration - self.elapsed_time)) if self.mode != GameMode.PRACTICE else "INF"
        time_text = f"TIME {remaining}s" if remaining != "INF" else "PRACTICE"
        cv2.putText(frame, time_text, (380, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, (100, 220, 255), 2, cv2.LINE_AA)

        # 4. OBJECTIVE
        cv2.putText(frame, self.objective_text, (20, height - 20),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (240, 240, 250), 1, cv2.LINE_AA)

        # Mode Indicator
        mode_badge = f"[{self.mode.value}]"
        cv2.putText(frame, mode_badge, (width - 150, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (180, 160, 255), 1, cv2.LINE_AA)

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_stop(self):
        pass

    @abstractmethod
    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        pass

    @abstractmethod
    def render(self, frame: np.ndarray, width: int, height: int):
        pass

    @abstractmethod
    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {}

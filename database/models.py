"""
MOVA Data Models matching the Section 32 Standard Game Result schema and Baselines
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import datetime

@dataclass
class StandardGameResult:
    game_id: str
    game_name: str
    duration: float = 0.0
    score: int = 0
    accuracy: float = 0.0
    reaction_time: float = 0.0
    movement_score: float = 0.0
    repetitions: int = 0
    left_right_balance: float = 0.0
    stability_score: float = 0.0
    gaze_accuracy: float = 0.0
    gesture_accuracy: float = 0.0
    coordination_score: float = 0.0
    multimodal_coordination: float = 0.0
    difficulty_start: float = 1.0
    difficulty_end: float = 1.0
    targets_attempted: int = 0
    targets_successful: int = 0
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    session_id: str = ""
    modalities_used: List[str] = field(default_factory=list)
    extra_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PersonalBaseline:
    user_id: str
    game_id: str
    sessions_count: int = 0
    best_score: int = 0
    avg_score: float = 0.0
    avg_accuracy: float = 0.0
    avg_reaction_time: float = 0.0
    avg_stability: float = 0.0
    avg_coordination: float = 0.0
    last_updated: str = ""

@dataclass
class CalibrationProfile:
    user_id: str = "default_user"
    head_center_x: float = 0.5
    head_center_y: float = 0.3
    reach_x_min: float = 0.15
    reach_x_max: float = 0.85
    reach_y_min: float = 0.15
    reach_y_max: float = 0.85
    lighting_score: float = 1.0
    calibrated_at: str = ""

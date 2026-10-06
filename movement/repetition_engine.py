"""
MOVA Repetition Engine: State Machine Movement Counter
Implements Section 23:
IDLE -> START -> MOVING -> TARGET_REACHED -> RETURN -> COMPLETED
Strictly avoids double-counting repetitions.
"""

from enum import Enum
from typing import Dict, Any, Optional

class RepetitionState(Enum):
    IDLE = "IDLE"
    START = "START"
    MOVING = "MOVING"
    TARGET_REACHED = "TARGET_REACHED"
    RETURN = "RETURN"
    COMPLETED = "COMPLETED"

class RepetitionStateMachine:
    def __init__(self, start_threshold: float = 0.15, reach_threshold: float = 0.45, return_threshold: float = 0.15):
        self.state = RepetitionState.IDLE
        self.start_threshold = start_threshold
        self.reach_threshold = reach_threshold
        self.return_threshold = return_threshold
        self.repetition_count = 0
        self.peak_displacement = 0.0

    def update(self, current_displacement: float) -> Tuple_State_Update:
        rep_completed = False
        self.peak_displacement = max(self.peak_displacement, current_displacement)

        if self.state == RepetitionState.IDLE:
            if current_displacement > self.start_threshold:
                self.state = RepetitionState.START

        elif self.state == RepetitionState.START:
            if current_displacement > self.start_threshold * 1.5:
                self.state = RepetitionState.MOVING
            elif current_displacement < self.start_threshold * 0.5:
                self.state = RepetitionState.IDLE

        elif self.state == RepetitionState.MOVING:
            if current_displacement >= self.reach_threshold:
                self.state = RepetitionState.TARGET_REACHED
            elif current_displacement < self.start_threshold:
                self.state = RepetitionState.IDLE

        elif self.state == RepetitionState.TARGET_REACHED:
            if current_displacement < self.reach_threshold * 0.8:
                self.state = RepetitionState.RETURN

        elif self.state == RepetitionState.RETURN:
            if current_displacement <= self.return_threshold:
                self.state = RepetitionState.COMPLETED
                self.repetition_count += 1
                rep_completed = True
                self.peak_displacement = 0.0
                self.state = RepetitionState.IDLE

        return {
            "state": self.state.value,
            "rep_count": self.repetition_count,
            "just_completed": rep_completed,
            "peak_displacement": round(self.peak_displacement, 3)
        }

    def reset(self):
        self.state = RepetitionState.IDLE
        self.repetition_count = 0
        self.peak_displacement = 0.0

Tuple_State_Update = Dict[str, Any]

"""
MOVA Movement Metrics Engine: Central Movement Intelligence Aggregator
Integrates Spatial, Angles, Velocity, Trajectory, Repetitions, Symmetry, Stability, and Coordination.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from movement.spatial_engine import SpatialEngine
from movement.angle_engine import AngleEngine
from movement.velocity_engine import VelocityEngine
from movement.trajectory_engine import TrajectoryEngine
from movement.repetition_engine import RepetitionStateMachine
from movement.symmetry_engine import SymmetryEngine
from movement.stability_engine import StabilityEngine
from movement.coordination_engine import CoordinationEngine

class MovementMetricsEngine:
    def __init__(self):
        self.spatial = SpatialEngine()
        self.angles = AngleEngine()
        self.velocity = VelocityEngine()
        self.trajectory_right = TrajectoryEngine()
        self.trajectory_left = TrajectoryEngine()
        self.repetition_sm = RepetitionStateMachine()
        self.symmetry = SymmetryEngine()
        self.stability = StabilityEngine()
        self.coordination = CoordinationEngine()

        # Session accumulators
        self.session_speeds: List[float] = []
        self.session_stabilities: List[float] = []
        self.session_symmetries: List[float] = []
        self.session_accuracies: List[float] = []
        self.session_reactions: List[float] = []

    def process_frame(self, frame_data, dt: float) -> Dict[str, Any]:
        """
        Extracts movement features for the current frame.
        """
        metrics = {
            "dt": dt,
            "body_center": frame_data.pose.body_center if frame_data.pose.detected else (0.5, 0.5),
            "torso_tilt": frame_data.pose.torso_tilt if frame_data.pose.detected else 0.0,
            "left_elbow_angle": frame_data.pose.left_elbow_angle if frame_data.pose.detected else 0.0,
            "right_elbow_angle": frame_data.pose.right_elbow_angle if frame_data.pose.detected else 0.0,
            "angles": {},
            "angular_velocities": {},
            "kinematics": {},
            "stability": {},
            "symmetry": {},
            "coordination": {},
            "repetition": {},
            "right_trajectory_smoothness": 1.0,
            "left_trajectory_smoothness": 1.0,
        }

        # Angles
        if frame_data.pose.detected:
            arm_angles = self.angles.compute_arm_angles(frame_data.pose.landmarks)
            metrics["angles"] = arm_angles
            metrics["angular_velocities"] = self.angles.compute_angular_velocities(arm_angles, dt)

        # Positions for kinematics
        pos_dict = {}
        if frame_data.hands.right_hand.detected:
            pos_dict["right_hand"] = frame_data.hands.right_hand.palm_center
            self.trajectory_right.add_point(frame_data.hands.right_hand.palm_center)
        if frame_data.hands.left_hand.detected:
            pos_dict["left_hand"] = frame_data.hands.left_hand.palm_center
            self.trajectory_left.add_point(frame_data.hands.left_hand.palm_center)
        if frame_data.pose.detected:
            pos_dict["body_center"] = frame_data.pose.body_center
            pos_dict["head"] = frame_data.face.face_center if frame_data.face.detected else (0.5, 0.3)

        kinematics = self.velocity.update(pos_dict, frame_data.timestamp)
        metrics["kinematics"] = kinematics

        # Stability
        if frame_data.pose.detected:
            stab = self.stability.update(frame_data.pose.body_center)
            metrics["stability"] = stab
            self.session_stabilities.append(stab["stability_score"])

        # Trajectory Smoothness
        metrics["right_trajectory_smoothness"] = self.trajectory_right.calculate_smoothness()
        metrics["left_trajectory_smoothness"] = self.trajectory_left.calculate_smoothness()

        # Symmetry & Coordination
        r_speed = kinematics.get("right_hand", {}).get("speed", 0.0)
        l_speed = kinematics.get("left_hand", {}).get("speed", 0.0)
        self.session_speeds.append(max(r_speed, l_speed))

        # Reach distance from center
        r_reach = 0.0
        l_reach = 0.0
        bc = metrics["body_center"]
        if frame_data.hands.right_hand.detected:
            r_reach = float(np.hypot(frame_data.hands.right_hand.palm_center[0] - bc[0],
                                     frame_data.hands.right_hand.palm_center[1] - bc[1]))
        if frame_data.hands.left_hand.detected:
            l_reach = float(np.hypot(frame_data.hands.left_hand.palm_center[0] - bc[0],
                                     frame_data.hands.left_hand.palm_center[1] - bc[1]))

        sym = self.symmetry.evaluate_arms_symmetry(l_reach, r_reach, l_speed, r_speed)
        metrics["symmetry"] = sym
        self.session_symmetries.append(sym["overall_symmetry"])

        coord = self.coordination.update_bilateral(l_speed, r_speed)
        metrics["coordination"] = coord

        # Repetition State Machine
        active_disp = max(r_reach, l_reach)
        rep = self.repetition_sm.update(active_disp)
        metrics["repetition"] = rep

        return metrics

    def record_target_interaction(self, reaction_time: float, accuracy: float):
        if reaction_time > 0:
            self.session_reactions.append(reaction_time)
        self.session_accuracies.append(accuracy)

    def get_session_summary(self) -> Dict[str, Any]:
        avg_speed = float(np.mean(self.session_speeds)) if self.session_speeds else 0.0
        avg_stab = float(np.mean(self.session_stabilities)) if self.session_stabilities else 90.0
        avg_sym = float(np.mean(self.session_symmetries)) if self.session_symmetries else 0.85
        avg_acc = float(np.mean(self.session_accuracies)) if self.session_accuracies else 0.85
        avg_react = float(np.mean(self.session_reactions)) if self.session_reactions else 0.75
        reps = self.repetition_sm.repetition_count

        # Movement consistency: inverse of speed variance
        speed_var = float(np.std(self.session_speeds)) if len(self.session_speeds) > 5 else 0.1
        movement_consistency = round(float(np.clip(1.0 - (speed_var * 0.5), 0.4, 0.98)), 2)

        return {
            "avg_speed": round(avg_speed, 3),
            "avg_stability": round(avg_stab, 1),
            "avg_symmetry": round(avg_sym, 2),
            "avg_accuracy": round(avg_acc, 2),
            "avg_reaction_time": round(avg_react, 3),
            "movement_consistency": movement_consistency,
            "total_repetitions": reps
        }

    def reset_session(self):
        self.session_speeds.clear()
        self.session_stabilities.clear()
        self.session_symmetries.clear()
        self.session_accuracies.clear()
        self.session_reactions.clear()
        self.trajectory_right.clear()
        self.trajectory_left.clear()
        self.repetition_sm.reset()
        self.stability.reset()

"""
MOVA Repository: Database CRUD and Personal Baseline Analytics
Strictly enforces YOU vs. YOUR PREVIOUS PERFORMANCE.
"""

import json
from typing import List, Optional, Dict, Any
from database.sqlite import get_connection
from database.models import StandardGameResult, PersonalBaseline, CalibrationProfile
from utils.privacy import sanitize_metrics_for_cloud

class Repository:
    def __init__(self):
        pass

    def save_session(self, session_id: str, user_id: str = "default_user", duration: float = 0.0,
                     total_score: int = 0, games_completed: int = 0, avg_reaction: float = 0.0,
                     avg_accuracy: float = 0.0, multimodal_coord: float = 0.0, ai_summary: str = ""):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        INSERT OR REPLACE INTO sessions 
        (session_id, user_id, duration, games_completed, total_score, avg_reaction_time, avg_accuracy, multimodal_coordination, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, duration, games_completed, total_score, avg_reaction, avg_accuracy, multimodal_coord, ai_summary))
        conn.commit()
        conn.close()

    def save_game_result(self, res: StandardGameResult, user_id: str = "default_user"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        INSERT INTO game_results (
            session_id, game_id, game_name, duration, score, accuracy, reaction_time,
            movement_score, repetitions, left_right_balance, stability_score,
            gaze_accuracy, gesture_accuracy, coordination_score, multimodal_coordination,
            difficulty_start, difficulty_end, targets_attempted, targets_successful,
            timestamp, modalities_used, extra_metrics
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            res.session_id, res.game_id, res.game_name, res.duration, res.score, res.accuracy, res.reaction_time,
            res.movement_score, res.repetitions, res.left_right_balance, res.stability_score,
            res.gaze_accuracy, res.gesture_accuracy, res.coordination_score, res.multimodal_coordination,
            res.difficulty_start, res.difficulty_end, res.targets_attempted, res.targets_successful,
            res.timestamp, json.dumps(res.modalities_used), json.dumps(res.extra_metrics)
        ))

        # Update Personal Baseline
        c.execute("SELECT * FROM personal_baselines WHERE user_id = ? AND game_id = ?", (user_id, res.game_id))
        row = c.fetchone()
        if row:
            count = row["sessions_count"] + 1
            best_score = max(row["best_score"], res.score)
            new_avg_score = (row["avg_score"] * row["sessions_count"] + res.score) / count
            new_avg_acc = (row["avg_accuracy"] * row["sessions_count"] + res.accuracy) / count
            new_avg_reaction = (row["avg_reaction_time"] * row["sessions_count"] + res.reaction_time) / count
            new_avg_stability = (row["avg_stability"] * row["sessions_count"] + res.stability_score) / count
            new_avg_coord = (row["avg_coordination"] * row["sessions_count"] + res.multimodal_coordination) / count

            c.execute("""
            UPDATE personal_baselines SET
                sessions_count = ?, best_score = ?, avg_score = ?, avg_accuracy = ?,
                avg_reaction_time = ?, avg_stability = ?, avg_coordination = ?, last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND game_id = ?
            """, (count, best_score, new_avg_score, new_avg_acc, new_avg_reaction, new_avg_stability, new_avg_coord, user_id, res.game_id))
        else:
            c.execute("""
            INSERT INTO personal_baselines (
                user_id, game_id, sessions_count, best_score, avg_score, avg_accuracy,
                avg_reaction_time, avg_stability, avg_coordination
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
            """, (user_id, res.game_id, res.score, res.score, res.accuracy, res.reaction_time, res.stability_score, res.multimodal_coordination))

        conn.commit()
        conn.close()

    def get_personal_baseline(self, user_id: str, game_id: str) -> Optional[PersonalBaseline]:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM personal_baselines WHERE user_id = ? AND game_id = ?", (user_id, game_id))
        row = c.fetchone()
        conn.close()
        if row:
            return PersonalBaseline(
                user_id=row["user_id"],
                game_id=row["game_id"],
                sessions_count=row["sessions_count"],
                best_score=row["best_score"],
                avg_score=row["avg_score"],
                avg_accuracy=row["avg_accuracy"],
                avg_reaction_time=row["avg_reaction_time"],
                avg_stability=row["avg_stability"],
                avg_coordination=row["avg_coordination"],
                last_updated=row["last_updated"]
            )
        return None

    def get_recent_results(self, limit: int = 20, game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        if game_id:
            c.execute("SELECT * FROM game_results WHERE game_id = ? ORDER BY id DESC LIMIT ?", (game_id, limit))
        else:
            c.execute("SELECT * FROM game_results ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_comparison_trend(self, user_id: str, game_id: str, current_result: StandardGameResult) -> Dict[str, Any]:
        """
        Calculates personal progress: YOU vs. YOUR PREVIOUS PERFORMANCE.
        Never compares to other users or normative averages.
        """
        baseline = self.get_personal_baseline(user_id, game_id)
        if not baseline or baseline.sessions_count <= 1:
            return {
                "has_previous": False,
                "sessions_completed": 1,
                "score_delta": 0,
                "reaction_delta": 0.0,
                "accuracy_delta": 0.0,
                "trend_status": "Personal baseline established",
                "summary": "Great start! This establishes your personal movement baseline."
            }

        score_diff = current_result.score - int(baseline.avg_score)
        reaction_diff = round(baseline.avg_reaction_time - current_result.reaction_time, 3) # positive means faster!
        acc_diff = round(current_result.accuracy - baseline.avg_accuracy, 3)

        trend_status = "Consistent"
        if reaction_diff > 0.05 and acc_diff >= 0:
            trend_status = "Improved Response & Precision"
        elif reaction_diff > 0.05:
            trend_status = "Faster Reaction Time"
        elif acc_diff > 0.05:
            trend_status = "Higher Interaction Precision"
        elif reaction_diff < -0.08:
            trend_status = "Deliberate / Slower Pacing"

        return {
            "has_previous": True,
            "sessions_completed": baseline.sessions_count,
            "score_delta": score_diff,
            "reaction_delta": reaction_diff,
            "accuracy_delta": acc_diff,
            "baseline_avg_score": baseline.avg_score,
            "baseline_avg_reaction": baseline.avg_reaction_time,
            "baseline_avg_accuracy": baseline.avg_accuracy,
            "trend_status": trend_status,
            "summary": f"{trend_status} compared to your personal baseline across {baseline.sessions_count} previous rounds."
        }

    def save_calibration_profile(self, profile: CalibrationProfile):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        INSERT OR REPLACE INTO calibration_profiles 
        (user_id, head_center_x, head_center_y, reach_x_min, reach_x_max, reach_y_min, reach_y_max, lighting_score, calibrated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (profile.user_id, profile.head_center_x, profile.head_center_y,
              profile.reach_x_min, profile.reach_x_max, profile.reach_y_min, profile.reach_y_max, profile.lighting_score))
        conn.commit()
        conn.close()

    def get_calibration_profile(self, user_id: str = "default_user") -> CalibrationProfile:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM calibration_profiles WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return CalibrationProfile(
                user_id=row["user_id"],
                head_center_x=row["head_center_x"],
                head_center_y=row["head_center_y"],
                reach_x_min=row["reach_x_min"],
                reach_x_max=row["reach_x_max"],
                reach_y_min=row["reach_y_min"],
                reach_y_max=row["reach_y_max"],
                lighting_score=row["lighting_score"],
                calibrated_at=row["calibrated_at"]
            )
        return CalibrationProfile()

repo = Repository()

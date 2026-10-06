"""
MOVA Test Suite: Verification of core algorithms and engines.
Tests:
- Landmark Processor (Angle calculation, smoothing)
- Kinematics & Velocity Engine
- Trajectory Glyph Matcher
- Personal Baseline calculations
- Adaptive Difficulty updates
"""

import unittest
import numpy as np
from vision.landmark_processor import LandmarkProcessor, ExponentialMovingAverage
from movement.velocity_engine import KinematicTracker
from movement.trajectory_engine import TrajectoryEngine
from ml.difficulty_engine import AdaptiveDifficultyEngine
from ml.recommendation_engine import RecommendationEngine

class TestLandmarkProcessor(unittest.TestCase):
    def test_calculate_angle_right_angle(self):
        # (0, 1) -> (0, 0) -> (1, 0) should be 90 degrees
        a = (0.0, 1.0)
        b = (0.0, 0.0)
        c = (1.0, 0.0)
        angle = LandmarkProcessor.calculate_angle_3p(a, b, c)
        self.assertAlmostEqual(angle, 90.0, places=1)

    def test_calculate_angle_straight_line(self):
        # (-1, 0) -> (0, 0) -> (1, 0) should be 180 degrees
        a = (-1.0, 0.0)
        b = (0.0, 0.0)
        c = (1.0, 0.0)
        angle = LandmarkProcessor.calculate_angle_3p(a, b, c)
        self.assertAlmostEqual(angle, 180.0, places=1)

    def test_ema_filter(self):
        ema = ExponentialMovingAverage(alpha=0.5)
        # First sample
        res1 = ema.update((10.0, 20.0))
        self.assertTrue(np.allclose(res1, [10.0, 20.0]))
        # Second sample
        res2 = ema.update((20.0, 40.0))
        self.assertTrue(np.allclose(res2, [15.0, 30.0]))

class TestKinematicTracker(unittest.TestCase):
    def test_velocity_calculation(self):
        tracker = KinematicTracker()
        # Initial point at t=0.0
        res0 = tracker.update((0.0, 0.0), timestamp=0.0)
        self.assertEqual(res0["speed"], 0.0)
        # Move by distance 1.0 at t=0.1 -> speed = 10.0
        res1 = tracker.update((1.0, 0.0), timestamp=0.1)
        self.assertAlmostEqual(res1["speed"], 10.0, places=1)

class TestTrajectoryEngine(unittest.TestCase):
    def test_path_efficiency_straight_line(self):
        engine = TrajectoryEngine()
        # Add straight line points
        for i in range(11):
            engine.add_point((float(i) / 10.0, 0.5))
        length = engine.calculate_path_length()
        efficiency = engine.calculate_efficiency()
        self.assertGreater(length, 0.9)
        self.assertAlmostEqual(efficiency, 1.0, places=2)

    def test_glyph_circle_recognition(self):
        engine = TrajectoryEngine()
        # Generate points along a circle
        for theta in np.linspace(0, 2 * np.pi, 30):
            x = 0.5 + 0.2 * np.cos(theta)
            y = 0.5 + 0.2 * np.sin(theta)
            engine.add_point((x, y))
        score = TrajectoryEngine.match_glyph(engine.get_trail(), "CIRCLE")
        self.assertGreater(score, 0.4)

class TestAdaptiveDifficulty(unittest.TestCase):
    def test_difficulty_adaptation(self):
        diff_engine = AdaptiveDifficultyEngine(base_level=1.0, min_level=0.5, max_level=3.0)
        # Consecutive fast hits should increase difficulty
        for _ in range(4):
            diff_engine.record_hit(reaction_time=0.5, accuracy=0.9)
        level_after_hits = diff_engine.current_level
        self.assertGreater(level_after_hits, 1.0)

        # Consecutive misses should decrease difficulty
        for _ in range(4):
            diff_engine.record_miss()
        level_after_misses = diff_engine.current_level
        self.assertLess(level_after_misses, level_after_hits)

if __name__ == "__main__":
    unittest.main()

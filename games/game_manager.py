"""
MOVA Game Manager & Game Registry
Orchestrates the 10 crazy games, lifecycle states, modalities requirements,
practice mode, and results persistence.
"""

from typing import Dict, Any, List, Optional, Type
import cv2
import numpy as np

from games.base_game import BaseGame, GameMode, GameState
from games.gravity_flip import GravityFlipGame
from games.dragon_dash import DragonDashGame
from games.galaxy_rescue import GalaxyRescueGame
from games.spellcaster import SpellcasterGame
from games.bee_swarm import BeeSwarmGame
from games.treasure_storm import TreasureStormGame
from games.robot_factory import RobotFactoryGame
from games.ocean_guardian import OceanGuardianGame
from games.mirror_mage import MirrorMageGame
from games.neon_pulse import NeonPulseGame
from database.models import StandardGameResult

class GameRegistry:
    CATALOG = {
        "gravity_flip": {
            "cls": GravityFlipGame,
            "title": "Gravity Flip 🪐",
            "category": "STABILITY",
            "description": "Shift cosmic gravity across multiple directions and steer your celestial orb through hazards into the portal.",
            "modalities": ["🧍 Body", "💪 Arms", "😊 Head", "👀 Gaze"],
            "movement_focus": "Directional Posture Shift & Stability",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🪐",
            "color": "#7928CA"
        },
        "dragon_dash": {
            "cls": DragonDashGame,
            "title": "Dragon Dash 🐉",
            "category": "REACTION",
            "description": "Dodge incoming dragon fire hazards with whole-body displacement while reaching with hands to capture energy orbs.",
            "modalities": ["👀 Eyes", "🖐️ Hands", "💪 Arms", "🧍 Body"],
            "movement_focus": "Whole-Body Dodge & Hand Collection",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🐉",
            "color": "#FF0080"
        },
        "galaxy_rescue": {
            "cls": GalaxyRescueGame,
            "title": "Galaxy Rescue 🌌",
            "category": "COORDINATION",
            "description": "Locate exoplanets with gaze fixation, reach outward with your hand, and channel tractor beams to rescue cosmic beings.",
            "modalities": ["👀 Gaze", "🖐️ Hand", "💪 Arm", "🧍 Body"],
            "movement_focus": "Gaze-To-Reach Coupling & Spatial Reach",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🌌",
            "color": "#0070F3"
        },
        "spellcaster": {
            "cls": SpellcasterGame,
            "title": "Spellcaster 🪄",
            "category": "GESTURE",
            "description": "Trace glowing arcane geometric trajectories in space with your hand and release bursts of magical energy.",
            "modalities": ["🖐️ Hands", "💪 Arms", "🗣️ Voice"],
            "movement_focus": "Glyph Trajectory & Smooth Arcane Precision",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🪄",
            "color": "#F5A623"
        },
        "bee_swarm": {
            "cls": BeeSwarmGame,
            "title": "Bee Swarm 🐝",
            "category": "REACTION",
            "description": "Visually pick out the fast fluttering Golden Queen Bee among swarming hornets and intercept her in flight.",
            "modalities": ["🖐️ Hands", "👀 Eyes", "💪 Arms"],
            "movement_focus": "Visual Selectivity & Interception Speed",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🐝",
            "color": "#F8E71C"
        },
        "treasure_storm": {
            "cls": TreasureStormGame,
            "title": "Treasure Storm 🏴‍☠️",
            "category": "GESTURE",
            "description": "Maneuver your body around rotating lightning hazard sectors, reach sunken treasure chests, and unlock with pinch gestures.",
            "modalities": ["🧍 Body", "💪 Arms", "🖐️ Hands", "👀 Gaze"],
            "movement_focus": "Hazard Avoidance & Fine Pinch Precision",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🏴‍☠️",
            "color": "#50E3C2"
        },
        "robot_factory": {
            "cls": RobotFactoryGame,
            "title": "Robot Factory 🤖",
            "category": "MULTIMODAL",
            "description": "Master a 5-step industrial cybernetic assembly flow: Look -> Point -> Grab -> Move -> Release components into the chassis.",
            "modalities": ["🖐️ Hands", "💪 Arms", "👀 Eyes", "🗣️ Voice"],
            "movement_focus": "Sequential Multimodal Sensorimotor Flow",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🤖",
            "color": "#BD10E0"
        },
        "ocean_guardian": {
            "cls": OceanGuardianGame,
            "title": "Ocean Guardian 🌊",
            "category": "STABILITY",
            "description": "Pilot an underwater submersible by leaning your torso and tilting arms, retrieving ocean pearls while dodging naval mines.",
            "modalities": ["🧍 Body", "💪 Arms", "🖐️ Hands", "👀 Gaze"],
            "movement_focus": "Submarine Lateral Steering & Hand Reaching",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🌊",
            "color": "#4A90E2"
        },
        "mirror_mage": {
            "cls": MirrorMageGame,
            "title": "Mirror Mage 🪞",
            "category": "MULTIMODAL",
            "description": "The ultimate multimodal coordination test. Reproduce escalating mirror choreography sequences across eyes, face, hands, and body.",
            "modalities": ["👀 Eyes", "😊 Face", "🖐️ Hands", "💪 Arms", "🧍 Body"],
            "movement_focus": "Complete Multimodal Synchronization & Working Memory",
            "duration": "50s",
            "difficulty": "Dynamic Adaptive",
            "icon": "🪞",
            "color": "#B8E986"
        },
        "neon_pulse": {
            "cls": NeonPulseGame,
            "title": "Neon Pulse ⚡",
            "category": "RHYTHM",
            "description": "Strike rhythm target pads on beat as collapsing neon rings align with the tempo. Tests millisecond timing and bilateral hand coordination.",
            "modalities": ["👀 Eyes", "🖐️ Hands", "💪 Arms", "🧍 Body"],
            "movement_focus": "Spatial Rhythm & Bilateral Timing Accuracy",
            "duration": "45s",
            "difficulty": "Dynamic Adaptive",
            "icon": "⚡",
            "color": "#D0021B"
        }
    }

class GameManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.active_game: Optional[BaseGame] = None
        self.active_game_id: Optional[str] = None
        self.games_cache: Dict[str, BaseGame] = {}
        self._initialized = True

    def select_game(self, game_id: str, mode: GameMode = GameMode.CHALLENGE) -> BaseGame:
        if game_id not in GameRegistry.CATALOG:
            game_id = "gravity_flip"

        game_cls = GameRegistry.CATALOG[game_id]["cls"]
        game_instance = game_cls()
        game_instance.set_mode(mode)
        self.active_game = game_instance
        self.active_game_id = game_id
        return game_instance

    def start_active_game(self):
        if self.active_game:
            self.active_game.start()

    def pause_active_game(self):
        if self.active_game:
            self.active_game.pause()

    def resume_active_game(self):
        if self.active_game:
            self.active_game.resume()

    def stop_active_game(self):
        if self.active_game:
            self.active_game.stop()

    def update_frame(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        if self.active_game:
            self.active_game.update_lifecycle(dt, frame_data, movement_metrics, fusion_result)

    def render_game_view(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)

        render_frame = frame.copy()
        h, w = render_frame.shape[:2]

        if self.active_game and self.active_game.state == GameState.PLAYING:
            self.active_game.render(render_frame, w, h)
        elif self.active_game and self.active_game.state == GameState.PAUSED:
            self.active_game.render(render_frame, w, h)
            # Semi-transparent pause scrim
            overlay = render_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 20), -1)
            cv2.addWeighted(overlay, 0.65, render_frame, 0.35, 0, render_frame)
            cv2.putText(render_frame, "PAUSED", (w // 2 - 80, h // 2),
                        cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(render_frame, "Say 'Resume' or click Resume to continue", (w // 2 - 160, h // 2 + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 220), 1, cv2.LINE_AA)

        return render_frame

    def handle_voice_input(self, command: str):
        if not command:
            return
        if command == "pause":
            self.pause_active_game()
        elif command == "resume":
            self.resume_active_game()
        elif command == "stop":
            self.stop_active_game()
        elif self.active_game and self.active_game.state == GameState.PLAYING:
            self.active_game.handle_input(command)

game_manager = GameManager()

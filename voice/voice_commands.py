"""
MOVA Voice Command Grammar & Intent Parser
Implements Section 8:
Start, Pause, Resume, Stop, Repeat, Next Game, Select, and Game Action cued words.
"""

from typing import Dict, Any, Optional, List

class VoiceCommandParser:
    COMMANDS = {
        "start": ["start", "begin", "play", "go"],
        "pause": ["pause", "hold", "wait"],
        "resume": ["resume", "continue", "unpause"],
        "stop": ["stop", "quit", "exit", "end"],
        "practice": ["practice", "training", "tutorial"],
        "next": ["next", "next game", "forward"],
        "repeat": ["repeat", "again", "repeat instructions"],
        # In-game voice prompts
        "activate_portal": ["activate portal", "portal", "open portal", "engage"],
        "cast_spell": ["cast", "ignite", "lumos", "frost", "fire"],
        "grab_part": ["grab", "attach", "assemble", "build"]
    }

    @classmethod
    def parse_utterance(cls, text: str) -> Optional[str]:
        if not text:
            return None
        clean = text.strip().lower()
        for cmd_key, triggers in cls.COMMANDS.items():
            for trigger in triggers:
                if trigger in clean:
                    return cmd_key
        return None

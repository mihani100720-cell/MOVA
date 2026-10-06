"""
MOVA Database SQLite Schema and Connection Manager
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from config.settings import settings

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or settings.DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT DEFAULT 'default_user',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        duration REAL DEFAULT 0,
        games_completed INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,
        avg_reaction_time REAL DEFAULT 0,
        avg_accuracy REAL DEFAULT 0,
        multimodal_coordination REAL DEFAULT 0,
        ai_summary TEXT DEFAULT ''
    )
    """)

    # Game Results table (Matches Section 32 Standard Game Result Schema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        game_id TEXT NOT NULL,
        game_name TEXT NOT NULL,
        duration REAL DEFAULT 0,
        score INTEGER DEFAULT 0,
        accuracy REAL DEFAULT 0,
        reaction_time REAL DEFAULT 0,
        movement_score REAL DEFAULT 0,
        repetitions INTEGER DEFAULT 0,
        left_right_balance REAL DEFAULT 0,
        stability_score REAL DEFAULT 0,
        gaze_accuracy REAL DEFAULT 0,
        gesture_accuracy REAL DEFAULT 0,
        coordination_score REAL DEFAULT 0,
        multimodal_coordination REAL DEFAULT 0,
        difficulty_start REAL DEFAULT 1.0,
        difficulty_end REAL DEFAULT 1.0,
        targets_attempted INTEGER DEFAULT 0,
        targets_successful INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        modalities_used TEXT DEFAULT '[]',
        extra_metrics TEXT DEFAULT '{}',
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)

    # Personal Baselines table (Section 26 - YOU vs YOUR PREVIOUS PERFORMANCE)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal_baselines (
        user_id TEXT NOT NULL,
        game_id TEXT NOT NULL,
        sessions_count INTEGER DEFAULT 0,
        best_score INTEGER DEFAULT 0,
        avg_score REAL DEFAULT 0,
        avg_accuracy REAL DEFAULT 0,
        avg_reaction_time REAL DEFAULT 0,
        avg_stability REAL DEFAULT 0,
        avg_coordination REAL DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, game_id)
    )
    """)

    # Calibration baseline table (Section 11)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calibration_profiles (
        user_id TEXT PRIMARY KEY,
        head_center_x REAL DEFAULT 0.5,
        head_center_y REAL DEFAULT 0.3,
        reach_x_min REAL DEFAULT 0.2,
        reach_x_max REAL DEFAULT 0.8,
        reach_y_min REAL DEFAULT 0.2,
        reach_y_max REAL DEFAULT 0.8,
        lighting_score REAL DEFAULT 1.0,
        calibrated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# Auto-initialize
init_db()

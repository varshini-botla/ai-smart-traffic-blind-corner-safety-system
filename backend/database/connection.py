"""
SQLite Database Connection and Schema Management
"""

import os
import sqlite3
from typing import Generator
from pathlib import Path

# Database file location in data/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "traffic_events.db"


def get_db_path() -> Path:
    """Return database file path and ensure directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    """
    Create and return a new SQLite database connection with row factory enabled.
    """
    db_file = get_db_path()
    conn = sqlite3.connect(str(db_file), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize SQLite schema for traffic_events and indexes if not already present.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'User Provided Traffic Data',
                distance_a REAL NOT NULL,
                distance_b REAL NOT NULL,
                speed_a REAL NOT NULL,
                speed_b REAL NOT NULL,
                vehicle_count_a INTEGER NOT NULL,
                vehicle_count_b INTEGER NOT NULL,
                ttc_a REAL,
                ttc_b REAL,
                traffic_density TEXT NOT NULL,
                ai_risk TEXT NOT NULL,
                final_risk TEXT NOT NULL,
                warning TEXT NOT NULL,
                side_a_action TEXT NOT NULL,
                side_b_action TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                explanation TEXT NOT NULL,
                raw_features TEXT
            );
        """)

        # Performance indexes for history query filtering & analytics
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traffic_events_timestamp 
            ON traffic_events(timestamp DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traffic_events_final_risk 
            ON traffic_events(final_risk);
        """)
        conn.commit()
    finally:
        conn.close()

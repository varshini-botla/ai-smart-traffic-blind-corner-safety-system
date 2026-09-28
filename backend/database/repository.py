"""
Data Access Repository for SQLite Traffic Events
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.database.connection import get_connection


def insert_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a processed traffic analysis event into the SQLite database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        timestamp = event_data.get("timestamp") or datetime.now(timezone.utc).isoformat()
        raw_features_json = json.dumps(event_data.get("raw_features", {}))

        cursor.execute("""
            INSERT INTO traffic_events (
                timestamp,
                source,
                distance_a,
                distance_b,
                speed_a,
                speed_b,
                vehicle_count_a,
                vehicle_count_b,
                ttc_a,
                ttc_b,
                traffic_density,
                ai_risk,
                final_risk,
                warning,
                side_a_action,
                side_b_action,
                recommendation,
                explanation,
                raw_features
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            event_data.get("source", "User Provided Traffic Data"),
            float(event_data["distance_a"]),
            float(event_data["distance_b"]),
            float(event_data["speed_a"]),
            float(event_data["speed_b"]),
            int(event_data["vehicle_count_a"]),
            int(event_data["vehicle_count_b"]),
            event_data.get("ttc_a"),
            event_data.get("ttc_b"),
            str(event_data["traffic_density"]),
            str(event_data["ai_risk"]),
            str(event_data["final_risk"]),
            str(event_data["warning"]),
            str(event_data["side_a_action"]),
            str(event_data["side_b_action"]),
            str(event_data["recommendation"]),
            str(event_data.get("explanation", "")),
            raw_features_json
        ))
        conn.commit()
        inserted_id = cursor.lastrowid
        return get_event_by_id(inserted_id)
    finally:
        conn.close()


def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve an event by primary key ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM traffic_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def get_latest_event() -> Optional[Dict[str, Any]]:
    """Retrieve the most recent traffic analysis event."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM traffic_events ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def get_events(
    limit: int = 50,
    offset: int = 0,
    risk_filter: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve stored traffic events with optional risk and text filtering.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM traffic_events WHERE 1=1"
        params: List[Any] = []

        if risk_filter and risk_filter.upper() != "ALL":
            query += " AND final_risk = ?"
            params.append(risk_filter.upper())

        if search:
            query += " AND (recommendation LIKE ? OR warning LIKE ? OR explanation LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_events_count(risk_filter: Optional[str] = None) -> int:
    """Get total count of events matching criteria."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT COUNT(*) FROM traffic_events WHERE 1=1"
        params: List[Any] = []
        if risk_filter and risk_filter.upper() != "ALL":
            query += " AND final_risk = ?"
            params.append(risk_filter.upper())

        cursor.execute(query, params)
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_analytics_summary() -> Dict[str, Any]:
    """
    Compute genuine analytics calculated directly from stored SQLite records.
    Returns empty/zero structures if no records exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM traffic_events")
        total_events = cursor.fetchone()[0]

        if total_events == 0:
            return {
                "total_events": 0,
                "has_data": False,
                "risk_distribution": {},
                "density_distribution": {},
                "average_speed_a": 0.0,
                "average_speed_b": 0.0,
                "average_distance_a": 0.0,
                "average_distance_b": 0.0,
                "high_risk_count": 0,
                "collision_risk_count": 0,
                "safe_count": 0,
                "caution_count": 0,
            }

        # Risk distribution
        cursor.execute("""
            SELECT final_risk, COUNT(*) as count 
            FROM traffic_events 
            GROUP BY final_risk
        """)
        risk_dist = {row["final_risk"]: row["count"] for row in cursor.fetchall()}

        # Density distribution
        cursor.execute("""
            SELECT traffic_density, COUNT(*) as count 
            FROM traffic_events 
            GROUP BY traffic_density
        """)
        density_dist = {row["traffic_density"]: row["count"] for row in cursor.fetchall()}

        # Averages
        cursor.execute("""
            SELECT 
                AVG(speed_a) as avg_speed_a,
                AVG(speed_b) as avg_speed_b,
                AVG(distance_a) as avg_dist_a,
                AVG(distance_b) as avg_dist_b
            FROM traffic_events
        """)
        avgs = cursor.fetchone()

        return {
            "total_events": total_events,
            "has_data": True,
            "risk_distribution": risk_dist,
            "density_distribution": density_dist,
            "average_speed_a": round(avgs["avg_speed_a"] or 0.0, 2),
            "average_speed_b": round(avgs["avg_speed_b"] or 0.0, 2),
            "average_distance_a": round(avgs["avg_dist_a"] or 0.0, 2),
            "average_distance_b": round(avgs["avg_dist_b"] or 0.0, 2),
            "safe_count": risk_dist.get("SAFE", 0),
            "caution_count": risk_dist.get("CAUTION", 0),
            "high_risk_count": risk_dist.get("HIGH_RISK", 0),
            "collision_risk_count": risk_dist.get("COLLISION_RISK", 0),
        }
    finally:
        conn.close()


def clear_all_events() -> int:
    """Clear all records from traffic_events table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM traffic_events")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Helper to convert sqlite3.Row to standard Python dictionary."""
    d = dict(row)
    if "raw_features" in d and d["raw_features"]:
        try:
            d["raw_features"] = json.loads(d["raw_features"])
        except Exception:
            pass
    return d

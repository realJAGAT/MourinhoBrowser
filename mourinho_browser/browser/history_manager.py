from datetime import datetime
from typing import Dict, List, Optional

from database.database import Database


class HistoryManager:
    def record_visit(self, url: str, title: str, duration_seconds: int = 0) -> None:
        conn = Database.connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "SELECT id, visit_count FROM history WHERE url = ?", (url,)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE history SET title = ?, duration_seconds = duration_seconds + ?, visit_count = visit_count + 1, last_visit = ? "
                "WHERE id = ?",
                (title, duration_seconds, now, existing["id"]),
            )
        else:
            cursor.execute(
                "INSERT INTO history(url, title, duration_seconds, visit_time, last_visit) VALUES(?, ?, ?, ?, ?)",
                (url, title, duration_seconds, now, now),
            )
        conn.commit()

    def search_history(self, query: str, limit: int = 100) -> List[Dict]:
        cursor = Database.connection().cursor()
        pattern = f"%{query}%"
        cursor.execute(
            "SELECT * FROM history WHERE url LIKE ? OR title LIKE ? ORDER BY last_visit DESC LIMIT ?",
            (pattern, pattern, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_history(self, limit: int = 100) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM history ORDER BY last_visit DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_analytics(self) -> Dict[str, int]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT COUNT(*) AS total_visits, SUM(visit_count) AS total_visits_all FROM history")
        result = cursor.fetchone()
        return {
            "unique_sites": result["total_visits"] or 0,
            "total_visits": result["total_visits_all"] or 0,
        }

    def clear_history(self) -> None:
        conn = Database.connection()
        conn.execute("DELETE FROM history")
        conn.commit()

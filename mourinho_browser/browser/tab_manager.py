import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class TabManager:
    def __init__(self):
        self.active_tab_id: Optional[int] = None

    def create_tab(self, title: str, url: str, group_name: Optional[str] = None, pinned: bool = False) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tabs(title, url, pinned, group_name, last_active, health_score, cpu_score, ram_score, responsive, benched) "
            "VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP, 100, 0, 0, 1, 0)",
            (title, url, 1 if pinned else 0, group_name),
        )
        conn.commit()
        tab_id = cursor.lastrowid
        self.set_active_tab(tab_id)
        return tab_id

    def close_tab(self, tab_id: int) -> None:
        conn = Database.connection()
        conn.execute("DELETE FROM tabs WHERE id = ?", (tab_id,))
        conn.commit()
        if self.active_tab_id == tab_id:
            self.active_tab_id = None

    def move_tab(self, tab_id: int, group_name: str) -> None:
        conn = Database.connection()
        conn.execute("UPDATE tabs SET group_name = ? WHERE id = ?", (group_name, tab_id))
        conn.commit()

    def duplicate_tab(self, tab_id: int) -> Optional[int]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM tabs WHERE id = ?", (tab_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self.create_tab(row["title"], row["url"], row["group_name"], bool(row["pinned"]))

    def list_tabs(self, include_benched: bool = True) -> List[Dict]:
        cursor = Database.connection().cursor()
        if include_benched:
            cursor.execute("SELECT * FROM tabs ORDER BY last_active DESC")
        else:
            cursor.execute("SELECT * FROM tabs WHERE benched = 0 ORDER BY last_active DESC")
        return [dict(row) for row in cursor.fetchall()]

    def update_tab_scores(self, tab_id: int, cpu_score: int, ram_score: int, responsiveness: int, health_score: int) -> None:
        conn = Database.connection()
        conn.execute(
            "UPDATE tabs SET cpu_score = ?, ram_score = ?, responsive = ?, health_score = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?",
            (cpu_score, ram_score, responsiveness, health_score, tab_id),
        )
        conn.commit()

    def set_active_tab(self, tab_id: int) -> None:
        self.active_tab_id = tab_id
        conn = Database.connection()
        conn.execute("UPDATE tabs SET last_active = CURRENT_TIMESTAMP WHERE id = ?", (tab_id,))
        conn.commit()

    def get_tab(self, tab_id: int) -> Optional[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM tabs WHERE id = ?", (tab_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_tab_count(self) -> int:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM tabs")
        return int(cursor.fetchone()["count"])

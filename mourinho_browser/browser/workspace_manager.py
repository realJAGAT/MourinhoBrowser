import json
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class WorkspaceManager:
    def __init__(self, workspaces_path: Path):
        self.workspaces_path = workspaces_path
        self.workspaces_path.mkdir(parents=True, exist_ok=True)

    def save_workspace(self, name: str, description: str, payload: Dict) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO workspaces(name, description, payload, created_at, updated_at) "
            "VALUES(?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (name, description, json.dumps(payload)),
        )
        conn.commit()
        return cursor.lastrowid

    def restore_workspace(self, workspace_id: int) -> Optional[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT payload FROM workspaces WHERE id = ?", (workspace_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row["payload"])

    def list_workspaces(self) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT id, name, description, created_at, updated_at FROM workspaces ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def delete_workspace(self, workspace_id: int) -> None:
        conn = Database.connection()
        conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        conn.commit()

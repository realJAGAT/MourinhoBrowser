import json
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class BookmarkManager:
    def add_bookmark(self, title: str, url: str, folder_id: Optional[int] = None, tags: Optional[List[str]] = None) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookmarks(title, url, folder_id, tags, created_at, updated_at) VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (title, url, folder_id, json.dumps(tags or [])),
        )
        conn.commit()
        return cursor.lastrowid

    def list_bookmarks(self, folder_id: Optional[int] = None) -> List[Dict]:
        cursor = Database.connection().cursor()
        if folder_id is None:
            cursor.execute("SELECT * FROM bookmarks ORDER BY updated_at DESC")
        else:
            cursor.execute("SELECT * FROM bookmarks WHERE folder_id = ? ORDER BY updated_at DESC", (folder_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_bookmarks(self, query: str, limit: int = 100) -> List[Dict]:
        cursor = Database.connection().cursor()
        pattern = f"%{query}%"
        cursor.execute(
            "SELECT * FROM bookmarks WHERE title LIKE ? OR url LIKE ? OR tags LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (pattern, pattern, pattern, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_folder(self, name: str, parent_id: Optional[int] = None) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookmark_folders(name, parent_id, created_at, updated_at) VALUES(?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (name, parent_id),
        )
        conn.commit()
        return cursor.lastrowid

    def list_folders(self, parent_id: Optional[int] = None) -> List[Dict]:
        cursor = Database.connection().cursor()
        if parent_id is None:
            cursor.execute("SELECT * FROM bookmark_folders ORDER BY name ASC")
        else:
            cursor.execute("SELECT * FROM bookmark_folders WHERE parent_id = ? ORDER BY name ASC", (parent_id,))
        return [dict(row) for row in cursor.fetchall()]

    def export_bookmarks(self, destination: Path) -> None:
        export_data = {
            "bookmarks": self.list_bookmarks(),
            "folders": self.list_folders(),
        }
        destination.write_text(json.dumps(export_data, indent=2), encoding="utf-8")

    def import_bookmarks(self, source: Path) -> None:
        content = json.loads(source.read_text(encoding="utf-8"))
        conn = Database.connection()
        cursor = conn.cursor()
        for folder in content.get("folders", []):
            cursor.execute(
                "INSERT OR IGNORE INTO bookmark_folders(id, name, parent_id, created_at, updated_at) VALUES(?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (folder.get("id"), folder.get("name"), folder.get("parent_id")),
            )
        for bookmark in content.get("bookmarks", []):
            cursor.execute(
                "INSERT OR IGNORE INTO bookmarks(id, title, url, folder_id, tags, created_at, updated_at) VALUES(?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (bookmark.get("id"), bookmark.get("title"), bookmark.get("url"), bookmark.get("folder_id"), bookmark.get("tags")),
            )
        conn.commit()

import enum
import os
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class DownloadStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class DownloadManager:
    def __init__(self, downloads_path: Path):
        self.downloads_path = downloads_path
        self.downloads_path.mkdir(parents=True, exist_ok=True)

    def create_download(self, url: str, filename: str) -> int:
        destination = self.downloads_path / filename
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO downloads(url, filename, destination, status, progress, started_at, updated_at) "
            "VALUES(?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (url, filename, str(destination), DownloadStatus.PENDING.value),
        )
        conn.commit()
        return cursor.lastrowid

    def update_progress(self, download_id: int, progress: int, status: DownloadStatus) -> None:
        conn = Database.connection()
        conn.execute(
            "UPDATE downloads SET progress = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (progress, status.value, download_id),
        )
        conn.commit()

    def list_downloads(self) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM downloads ORDER BY started_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def pause(self, download_id: int) -> None:
        self.update_progress(download_id, self._progress_for(download_id), DownloadStatus.PAUSED)

    def resume(self, download_id: int) -> None:
        self.update_progress(download_id, self._progress_for(download_id), DownloadStatus.IN_PROGRESS)

    def cancel(self, download_id: int) -> None:
        self.update_progress(download_id, self._progress_for(download_id), DownloadStatus.CANCELED)

    def retry(self, download_id: int) -> None:
        self.update_progress(download_id, self._progress_for(download_id), DownloadStatus.PENDING)

    def _progress_for(self, download_id: int) -> int:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT progress FROM downloads WHERE id = ?", (download_id,))
        row = cursor.fetchone()
        return int(row["progress"]) if row else 0

    def virus_scan_hook(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
        return True

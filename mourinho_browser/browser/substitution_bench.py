import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from database.database import Database


class SubstitutionBench:
    BENCH_THRESHOLD_SECONDS = 120

    def __init__(self, bench_storage: Path):
        self.bench_storage = bench_storage
        self.bench_storage.mkdir(parents=True, exist_ok=True)

    def bench_tab(self, tab_id: int, metadata: Dict) -> None:
        conn = Database.connection()
        conn.execute(
            "UPDATE tabs SET benched = 1, last_active = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), tab_id),
        )
        conn.commit()
        self._save_bench_state(tab_id, metadata)

    def restore_tab(self, tab_id: int) -> Dict:
        conn = Database.connection()
        conn.execute("UPDATE tabs SET benched = 0 WHERE id = ?", (tab_id,))
        conn.commit()
        return self._load_bench_state(tab_id)

    def _save_bench_state(self, tab_id: int, metadata: Dict) -> None:
        path = self.bench_storage / f"benched_{tab_id}.json"
        path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def _load_bench_state(self, tab_id: int) -> Dict:
        path = self.bench_storage / f"benched_{tab_id}.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def list_benched_tabs(self) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM tabs WHERE benched = 1")
        return [dict(row) for row in cursor.fetchall()]

    def auto_bench_inactive_tabs(self) -> None:
        cursor = Database.connection().cursor()
        cursor.execute(
            "SELECT id, title, url, last_active FROM tabs WHERE benched = 0 ORDER BY last_active ASC"
        )
        rows = cursor.fetchall()
        for row in rows:
            if row["last_active"] is None:
                continue
            active_seconds = (datetime.utcnow() - datetime.fromisoformat(row["last_active"])).total_seconds()
            if active_seconds >= self.BENCH_THRESHOLD_SECONDS:
                metadata = {
                    "title": row["title"],
                    "url": row["url"],
                    "benched_at": datetime.utcnow().isoformat(),
                }
                self.bench_tab(row["id"], metadata)

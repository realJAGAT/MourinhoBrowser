import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from browser.substitution_bench import SubstitutionBench
from database.database import Database


class AutoSubstitution:
    def __init__(self, bench_storage: Path):
        self.bench = SubstitutionBench(bench_storage)

    def substitute_tab(self, tab_id: int, current_state: Dict) -> Optional[Dict]:
        try:
            url = current_state.get("url")
            if not url:
                return None

            saved_session = {
                "url": url,
                "title": current_state.get("title", "New Tab"),
                "last_state": current_state,
                "substituted_at": datetime.utcnow().isoformat(),
            }
            metadata = saved_session.copy()
            self.bench._save_bench_state(tab_id, metadata)
            conn = Database.connection()
            conn.execute("DELETE FROM tabs WHERE id = ?", (tab_id,))
            conn.commit()
            new_id = self._create_replacement_tab(saved_session)
            return self.bench._load_bench_state(new_id)
        except Exception:
            traceback.print_exc()
            return None

    def _create_replacement_tab(self, session_state: Dict) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tabs(title, url, pinned, group_name, last_active, health_score, cpu_score, ram_score, responsive, benched) "
            "VALUES(?, ?, 0, ?, ?, 100, 0, 0, 1, 0)",
            (
                session_state.get("title", "Restored Tab"),
                session_state.get("url", "about:blank"),
                session_state.get("last_state", {}).get("group_name"),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid

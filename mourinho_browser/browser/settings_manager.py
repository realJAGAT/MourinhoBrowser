import json
from pathlib import Path
from typing import Any

from database.database import Database


class SettingsManager:
    def __init__(self, settings_path: Path, database_path: Path):
        self.settings_path = settings_path
        self.database_path = database_path
        self.settings = self._load_settings()
        self._ensure_defaults()

    def _load_settings(self) -> dict:
        if self.settings_path.exists():
            try:
                return json.loads(self.settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _ensure_defaults(self) -> None:
        defaults = {
            "theme": "mourinho_dark",
            "privacy_mode": "Normal",
            "counter_attack_enabled": True,
            "startup_url": "https://www.google.com",
            "default_search_engine": "https://www.google.com/search?q={query}",
            "analytics_enabled": False,
            "do_not_track": True,
        }
        for key, value in defaults.items():
            self.settings.setdefault(key, value)
        self.save_settings()

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save_settings()

    def save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def get_database_path(self) -> Path:
        return self.database_path

    def persist_setting(self, key: str, value: str) -> None:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings(key, value, updated_at) VALUES(?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, str(value)),
        )
        conn.commit()

    def load_persisted_setting(self, key: str, default: Any = None) -> Any:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

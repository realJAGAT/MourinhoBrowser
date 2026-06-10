import json
from pathlib import Path

from database.database import Database
from browser.settings_manager import SettingsManager


def test_settings_manager_defaults(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    db_path = tmp_path / "browser.db"
    schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    Database.initialize(db_path, schema_path)
    settings = SettingsManager(settings_path, db_path)

    assert settings.get("theme") == "mourinho_dark"
    settings.set("theme", "classic_white")
    assert settings.get("theme") == "classic_white"
    assert settings_path.exists()
    loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    assert loaded["theme"] == "classic_white"

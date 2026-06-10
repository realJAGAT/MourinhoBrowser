from browser.omnibox import Omnibox
from browser.settings_manager import SettingsManager
from pathlib import Path
from database.database import Database


def test_omnibox_resolve_url(tmp_path: Path):
    settings_path = tmp_path / "settings.json"
    db_path = tmp_path / "browser.db"
    schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    Database.initialize(db_path, schema_path)
    settings = SettingsManager(settings_path, db_path)
    omnibox = Omnibox(settings)

    assert omnibox.resolve_query("https://example.com") == "https://example.com"
    assert omnibox.resolve_query("example.com") == "https://example.com"
    assert "google.com" in omnibox.resolve_query("test search")

from pathlib import Path
from database.database import Database
from browser.history_manager import HistoryManager


def test_history_records_and_searches(tmp_path: Path):
    db_path = tmp_path / "browser.db"
    schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    Database.initialize(db_path, schema_path)

    manager = HistoryManager()
    manager.record_visit("https://example.com", "Example", duration_seconds=12)
    results = manager.search_history("example")
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"
    manager.clear_history()
    assert manager.list_history() == []

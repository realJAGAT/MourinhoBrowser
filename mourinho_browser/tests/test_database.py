import sqlite3
from pathlib import Path

def test_database_initializes(tmp_path: Path):
    schema_src = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    database_file = tmp_path / "browser.db"
    from database.database import Database

    Database.initialize(database_file, schema_src)
    conn = Database.connection()
    assert isinstance(conn, sqlite3.Connection)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
    assert cursor.fetchone() is not None

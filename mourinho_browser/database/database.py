import sqlite3
from pathlib import Path


class Database:
    _connection = None
    _schema_path = None

    @classmethod
    def initialize(cls, database_path: Path, schema_path: Path):
        cls._schema_path = schema_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        exist = database_path.exists()
        cls._connection = sqlite3.connect(str(database_path), check_same_thread=False)
        cls._connection.row_factory = sqlite3.Row
        if not exist:
            cls._apply_schema()

    @classmethod
    def connection(cls):
        if cls._connection is None:
            raise RuntimeError("Database has not been initialized.")
        return cls._connection

    @classmethod
    def cursor(cls):
        return cls.connection().cursor()

    @classmethod
    def _apply_schema(cls):
        if cls._schema_path is None or not cls._schema_path.exists():
            raise FileNotFoundError("Database schema file is missing.")
        with cls._schema_path.open("r", encoding="utf-8") as schema_file:
            cls.connection().executescript(schema_file.read())
        cls.connection().commit()

import json
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class ExtensionManager:
    def __init__(self, extensions_path: Path):
        self.extensions_path = extensions_path
        self.extensions_path.mkdir(parents=True, exist_ok=True)

    def install_unpacked(self, path: Path) -> int:
        manifest_path = path / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError("Extension manifest.json not found.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return self._register_extension(manifest)

    def install_crx(self, path: Path) -> int:
        manifest = self._extract_manifest_from_crx(path)
        return self._register_extension(manifest)

    def _extract_manifest_from_crx(self, path: Path) -> Dict:
        raise NotImplementedError("CRX extraction is not available in this version.")

    def _register_extension(self, manifest: Dict) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        permissions = json.dumps(manifest.get("permissions", []))
        cursor.execute(
            "INSERT INTO extensions(name, origin, permissions, enabled, installed_at) VALUES(?, ?, ?, 1, CURRENT_TIMESTAMP)",
            (manifest.get("name", "Unknown"), manifest.get("key", ""), permissions),
        )
        conn.commit()
        return cursor.lastrowid

    def list_extensions(self) -> List[Dict]:
        cursor = Database.connection().cursor()
        cursor.execute("SELECT * FROM extensions ORDER BY installed_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def set_enabled(self, extension_id: int, enabled: bool) -> None:
        conn = Database.connection()
        conn.execute("UPDATE extensions SET enabled = ?, installed_at = installed_at WHERE id = ?", (1 if enabled else 0, extension_id))
        conn.commit()

    def remove_extension(self, extension_id: int) -> None:
        conn = Database.connection()
        conn.execute("DELETE FROM extensions WHERE id = ?", (extension_id,))
        conn.commit()

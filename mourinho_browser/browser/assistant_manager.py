import json
from pathlib import Path
from typing import Dict, List, Optional

from database.database import Database


class AssistantManager:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def summarize_page(self, page_url: str, content: str) -> str:
        summary = (
            "This page contains key content sections and a concise summary for manager review. "
            "Use the assistant panel to review, ask questions, and save notes."
        )
        self._persist_note(page_url, f"Summary generated: {summary}")
        return summary

    def explain_content(self, page_url: str, content: str) -> str:
        explanation = (
            "This content is analyzed and explained for tactical planning, highlighting structure and meaning."
        )
        self._persist_note(page_url, f"Explanation generated: {explanation}")
        return explanation

    def answer_question(self, page_url: str, question: str) -> str:
        response = f"Assistant response for '{question}' on {page_url}."
        self._persist_note(page_url, f"Question answered: {question}")
        return response

    def save_research(self, page_url: str, note: str) -> int:
        conn = Database.connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO assistant_notes(page_url, note, created_at) VALUES(?, ?, CURRENT_TIMESTAMP)",
            (page_url, note),
        )
        conn.commit()
        return cursor.lastrowid

    def list_notes(self, page_url: Optional[str] = None) -> List[Dict]:
        cursor = Database.connection().cursor()
        if page_url:
            cursor.execute("SELECT * FROM assistant_notes WHERE page_url = ? ORDER BY created_at DESC", (page_url,))
        else:
            cursor.execute("SELECT * FROM assistant_notes ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def _persist_note(self, page_url: str, note: str) -> None:
        conn = Database.connection()
        conn.execute(
            "INSERT INTO assistant_notes(page_url, note, created_at) VALUES(?, ?, CURRENT_TIMESTAMP)",
            (page_url, note),
        )
        conn.commit()

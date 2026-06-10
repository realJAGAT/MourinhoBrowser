from typing import List, Optional

from browser.bookmark_manager import BookmarkManager
from browser.history_manager import HistoryManager
from browser.settings_manager import SettingsManager


class Omnibox:
    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.history_manager = HistoryManager()
        self.bookmark_manager = BookmarkManager()

    def resolve_query(self, text: str) -> str:
        text = text.strip()
        if not text:
            return self.settings.get("startup_url")
        if self._looks_like_url(text):
            return self._normalize_url(text)
        if text.startswith("calc "):
            return self._calculate(text[5:])
        if text.startswith("convert "):
            return self._convert_units(text[8:])
        return self.settings.get("default_search_engine").format(query=text)

    def suggestions(self, text: str, limit: int = 10) -> List[str]:
        results = []
        results.extend([item["url"] for item in self.history_manager.search_history(text, limit)])
        results.extend([item["url"] for item in self.bookmark_manager.search_bookmarks(text, limit)])
        return results[:limit]

    def _looks_like_url(self, text: str) -> bool:
        return text.startswith("http://") or text.startswith("https://") or "." in text

    def _normalize_url(self, text: str) -> str:
        if text.startswith("http://") or text.startswith("https://"):
            return text
        return f"https://{text}"

    def _calculate(self, expression: str) -> str:
        try:
            safe_expression = expression.replace("^", "**")
            result = eval(safe_expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception:
            return "Invalid calculation"

    def _convert_units(self, expression: str) -> str:
        tokens = expression.split()
        if len(tokens) != 3:
            return "Invalid conversion"
        value, source, target = tokens
        try:
            value = float(value)
            conversions = {
                ("km", "m"): value * 1000,
                ("m", "km"): value / 1000,
                ("mi", "km"): value * 1.60934,
                ("kg", "g"): value * 1000,
                ("lb", "kg"): value * 0.453592,
            }
            return str(conversions.get((source, target), "Unsupported conversion"))
        except ValueError:
            return "Invalid conversion"

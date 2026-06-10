import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from browser.settings_manager import SettingsManager


def normalize_domain(url: str) -> str:
    return re.sub(r"^https?://", "", url).split("/")[0].lower()


class PrivacyEngine:
    BLOCK_LIST = [
        "doubleclick.net",
        "googlesyndication.com",
        "adservice.google.com",
        "facebook.net",
        "tracking.mozilla.org",
        "ads.yahoo.com",
    ]
    TRACKER_LIST = [
        "analytics.google.com",
        "pixel.wp.com",
        "connect.facebook.net",
        "static.doubleclick.net",
    ]

    DOH_SERVERS = {
        "cloudflare": "https://cloudflare-dns.com/dns-query",
        "google": "https://dns.google/dns-query",
    }

    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.mode = settings.get("privacy_mode", "Normal")
        self.custom_rules = self._load_custom_rules()

    def _load_custom_rules(self) -> Dict[str, List[str]]:
        path = Path(__file__).resolve().parent.parent / "database" / "privacy_rules.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.settings.set("privacy_mode", mode)

    def is_defensive(self) -> bool:
        return self.mode in ("Defensive", "Parking The Bus")

    def is_parking_the_bus(self) -> bool:
        return self.mode == "Parking The Bus"

    def should_block_url(self, url: str, resource_type: Optional[str] = None) -> bool:
        domain = normalize_domain(url)
        if any(blocked in domain for blocked in self.BLOCK_LIST):
            return True
        if self.is_defensive() and any(tracker in domain for tracker in self.TRACKER_LIST):
            return True
        if self.is_parking_the_bus():
            if resource_type and resource_type.lower() in ["image", "font", "script", "stylesheet"]:
                return True
        if any(pattern in domain for pattern in self.custom_rules.get("blocked_domains", [])):
            return True
        return False

    def should_block_third_party_cookie(self, url: str, first_party_url: str) -> bool:
        if not self.is_defensive():
            return False
        return normalize_domain(url) != normalize_domain(first_party_url)

    def should_restrict_script(self, url: str) -> bool:
        return self.is_parking_the_bus() and normalize_domain(url) not in ["mozilla.org", "python.org"]

    def get_doh_endpoint(self) -> str:
        return self.DOH_SERVERS.get("cloudflare")

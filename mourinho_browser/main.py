import os
import sys
from pathlib import Path

from PyQt6 import QtWidgets

from browser.browser_window import BrowserWindow
from browser.fitness_monitor import FitnessMonitor
from browser.privacy_engine import PrivacyEngine
from browser.settings_manager import SettingsManager
from database.database import Database

try:
    from cefpython3 import cefpython as cef
except ImportError as exc:
    raise ImportError(
        "cefpython3 is required to run Mourinho Browser. Install it via pip and ensure your platform is supported."
    ) from exc


def initialize_environment():
    root_path = Path(__file__).resolve().parent
    db_path = root_path / "database" / "browser.db"
    settings_path = root_path / "database" / "settings.json"
    Database.initialize(db_path, root_path / "database" / "schema.sql")
    return {
        "root_path": root_path,
        "db_path": db_path,
        "settings_path": settings_path,
    }


def main():
    env = initialize_environment()
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Mourinho Browser")

    settings = SettingsManager(env["settings_path"], env["db_path"])
    privacy_engine = PrivacyEngine(settings)
    fitness_monitor = FitnessMonitor()

    cef_settings = {
        "multi_threaded_message_loop": False,
        "log_severity": cef.LOGSEVERITY_INFO,
        "ignore_certificate_errors": False,
        "context_menu": {
            "enabled": False,
        },
    }

    cef.Initialize(cef_settings)

    browser_window = BrowserWindow(
        env["root_path"],
        settings,
        privacy_engine,
        fitness_monitor,
    )

    browser_window.showMaximized()
    exit_code = app.exec()

    cef.Shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

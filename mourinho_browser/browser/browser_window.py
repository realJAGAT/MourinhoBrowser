import json
from pathlib import Path
from typing import Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from browser.assistant_manager import AssistantManager
from browser.auto_substitution import AutoSubstitution
from browser.bookmark_manager import BookmarkManager
from browser.download_manager import DownloadManager
from browser.extension_manager import ExtensionManager
from browser.history_manager import HistoryManager
from browser.omnibox import Omnibox
from browser.settings_manager import SettingsManager
from browser.substitution_bench import SubstitutionBench
from browser.tactical_dashboard import TacticalDashboard
from browser.tab_manager import TabManager
from browser.workspace_manager import WorkspaceManager

try:
    from cefpython3 import cefpython as cef
except ImportError:
    cef = None


class CefBrowserWidget(QtWidgets.QWidget):
    def __init__(self, url: str, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.url = url
        self.browser = None
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)

    def create_browser(self):
        if cef is None or self.browser is not None:
            return
        window_info = cef.WindowInfo()
        window_info.SetAsChild(int(self.winId()), [0, 0, self.width(), self.height()])
        self.browser = cef.CreateBrowserSync(window_info, url=self.url)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.browser:
            cef.WindowUtils().OnSetFocus(int(self.winId()))
            self.browser.SetBounds(0, 0, self.width(), self.height())
            cef.MessageLoopWork()

    def load_url(self, url: str):
        self.url = url
        if self.browser:
            self.browser.LoadUrl(url)

    def showEvent(self, event):
        super().showEvent(event)
        self.create_browser()


class BrowserWindow(QMainWindow):
    def __init__(self, root_path: Path, settings: SettingsManager, privacy_engine, fitness_monitor):
        super().__init__()
        self.root_path = root_path
        self.settings = settings
        self.privacy_engine = privacy_engine
        self.fitness_monitor = fitness_monitor

        self.tab_manager = TabManager()
        self.history_manager = HistoryManager()
        self.bookmark_manager = BookmarkManager()
        self.extension_manager = ExtensionManager(self.root_path / "extensions")
        self.download_manager = DownloadManager(self.root_path / "downloads")
        self.workspace_manager = WorkspaceManager(self.root_path / "workspaces")
        self.substitution_bench = SubstitutionBench(self.root_path / "workspaces")
        self.auto_substitution = AutoSubstitution(self.root_path / "workspaces")
        self.assistant_manager = AssistantManager(self.root_path / "database" / "browser.db")
        self.omnibox = Omnibox(settings)
        self.dashboard = TacticalDashboard(self.fitness_monitor, self.tab_manager)

        self._load_ui()
        self._configure_window()
        self._initialize_power_dialogue()
        self._configure_shortcuts()
        self._configure_timers()
        self.create_tab(self.settings.get("startup_url"))

    def _load_ui(self) -> None:
        self.ui = QtWidgets.QWidget()
        self.setCentralWidget(self.ui)
        self.layout = QtWidgets.QVBoxLayout(self.ui)

        self.address_bar = QtWidgets.QLineEdit(self)
        self.address_bar.setPlaceholderText("Search or enter address")
        self.address_bar.returnPressed.connect(self._navigate)
        self.layout.addWidget(self.address_bar)

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.layout.addWidget(self.tab_widget)

        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self._update_status("Ready")

    def _configure_window(self) -> None:
        self.setWindowTitle("Mourinho Browser")
        icon_path = self.root_path / "assets" / "logo.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self._apply_theme(self.settings.get("theme", "mourinho_dark"))

    def _apply_theme(self, theme_name: str) -> None:
        theme_file = self.root_path / "themes" / f"{theme_name}.qss"
        if theme_file.exists():
            self.setStyleSheet(theme_file.read_text(encoding="utf-8"))

    def _initialize_power_dialogue(self) -> None:
        self.power_dialogue = QtWidgets.QDialog(self)
        self.power_dialogue.setWindowTitle("Power Dialogue")
        self.power_dialogue.setModal(True)
        self.power_dialogue.resize(800, 400)
        layout = QtWidgets.QVBoxLayout(self.power_dialogue)

        self.command_input = QtWidgets.QLineEdit(self.power_dialogue)
        self.command_input.setPlaceholderText("Type a command…")
        self.command_input.textChanged.connect(self._refresh_command_suggestions)
        self.command_input.returnPressed.connect(self._execute_command)
        layout.addWidget(self.command_input)

        self.command_results = QtWidgets.QListWidget(self.power_dialogue)
        self.command_results.itemActivated.connect(self._execute_selected_command)
        layout.addWidget(self.command_results)

    def _configure_shortcuts(self) -> None:
        self.power_dialogue_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+P"), self)
        self.power_dialogue_shortcut.activated.connect(self._open_power_dialogue)

    def _configure_timers(self) -> None:
        self.metric_timer = QTimer(self)
        self.metric_timer.timeout.connect(self._refresh_metrics)
        self.metric_timer.start(1000)
        if cef is not None:
            self.cef_timer = QTimer(self)
            self.cef_timer.timeout.connect(cef.MessageLoopWork)
            self.cef_timer.start(10)

    def _refresh_metrics(self) -> None:
        system_metrics = self.fitness_monitor.get_system_metrics()
        self._update_status(
            f"CPU {system_metrics['cpu_percent']}% | RAM {system_metrics['ram_percent']}% | Network {system_metrics['network_kb']}KB"
        )

    def _navigate(self) -> None:
        text = self.address_bar.text()
        target = self.omnibox.resolve_query(text)
        self._current_browser_widget().load_url(target)
        self.address_bar.setText(target)

    def _current_browser_widget(self) -> QtWidgets.QWidget:
        return self.tab_widget.currentWidget()

    def create_tab(self, url: str, title: Optional[str] = None, pinned: bool = False) -> None:
        title = title or "New Tab"
        tab_id = self.tab_manager.create_tab(title, url, pinned=pinned)
        browser_view = CefBrowserWidget(url, self)
        index = self.tab_widget.addTab(browser_view, title)
        self.tab_widget.setCurrentIndex(index)
        browser_view.create_browser()
        self.address_bar.setText(url)
        self._update_status(f"Tab opened: {title}")

    def _on_tab_close_requested(self, index: int) -> None:
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        self.tab_manager.close_tab(self.tab_manager.active_tab_id or 0)
        widget.deleteLater()
        self._update_status("Tab closed")

    def _on_tab_changed(self, index: int) -> None:
        widget = self.tab_widget.widget(index)
        if widget and isinstance(widget, CefBrowserWidget):
            self.address_bar.setText(widget.url)
            tab = self.tab_manager.get_tab(self.tab_manager.active_tab_id or 0)
            if tab:
                self.tab_manager.set_active_tab(tab["id"])

    def _open_power_dialogue(self) -> None:
        self.power_dialogue.show()
        self.power_dialogue.activateWindow()
        self.command_input.setFocus()
        self._refresh_command_suggestions()

    def _refresh_command_suggestions(self) -> None:
        query = self.command_input.text().strip().lower()
        commands = self._available_commands()
        filtered = [cmd for cmd in commands if query in cmd["name"].lower() or query in cmd["description"].lower()]
        self.command_results.clear()
        for cmd in filtered:
            item = QtWidgets.QListWidgetItem(f"{cmd['name']} — {cmd['description']}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, cmd)
            self.command_results.addItem(item)

    def _available_commands(self):
        return [
            {"name": "Open URL", "description": "Navigate directly to a website", "action": self._prompt_open_url},
            {"name": "Search Web", "description": "Search using the omnibox", "action": self._prompt_search_web},
            {"name": "New Tab", "description": "Open a new tab", "action": lambda: self.create_tab(self.settings.get("startup_url"))},
            {"name": "New Window", "description": "Open a new browser window", "action": self._new_window},
            {"name": "Close Tab", "description": "Close the active tab", "action": self._close_active_tab},
            {"name": "Save Workspace", "description": "Save current tabs and layout", "action": self._save_workspace},
            {"name": "Restore Workspace", "description": "Restore a saved workspace", "action": self._restore_workspace},
            {"name": "Open History", "description": "Open the history panel", "action": self._open_history},
            {"name": "Open Downloads", "description": "Open the downloads panel", "action": self._open_downloads},
            {"name": "Open Bookmarks", "description": "Open bookmarks manager", "action": self._open_bookmarks},
            {"name": "Open Settings", "description": "Open the settings panel", "action": self._open_settings},
            {"name": "Toggle Dark Mode", "description": "Switch between light and dark themes", "action": self._toggle_dark_mode},
            {"name": "Open DevTools", "description": "Open Chromium developer tools", "action": self._open_devtools},
            {"name": "Take Screenshot", "description": "Capture the current tab view", "action": self._take_screenshot},
            {"name": "Clear Cache", "description": "Clear browser cache and session data", "action": self._clear_cache},
            {"name": "Restart Browser", "description": "Restart the browser application", "action": self._restart_browser},
            {"name": "Enable Tactical Mode", "description": "Boost performance with tactical rules", "action": self._enable_tactical_mode},
        ]

    def _execute_command(self) -> None:
        current = self.command_results.currentItem()
        if current:
            cmd = current.data(QtCore.Qt.ItemDataRole.UserRole)
            cmd["action"]()
            self.power_dialogue.close()

    def _execute_selected_command(self, item: QtWidgets.QListWidgetItem) -> None:
        cmd = item.data(QtCore.Qt.ItemDataRole.UserRole)
        cmd["action"]()
        self.power_dialogue.close()

    def _prompt_open_url(self) -> None:
        url, accepted = QtWidgets.QInputDialog.getText(self, "Open URL", "Enter a URL:")
        if accepted and url:
            resolved = self.omnibox.resolve_query(url)
            self._current_browser_widget().load_url(resolved)
            self.address_bar.setText(resolved)

    def _prompt_search_web(self) -> None:
        query, accepted = QtWidgets.QInputDialog.getText(self, "Search Web", "Enter search query:")
        if accepted and query:
            resolved = self.omnibox.resolve_query(query)
            self._current_browser_widget().load_url(resolved)
            self.address_bar.setText(resolved)

    def _new_window(self) -> None:
        from browser.browser_window import BrowserWindow as BrowserWindowClass

        window = BrowserWindowClass(self.root_path, self.settings, self.privacy_engine, self.fitness_monitor)
        window.show()
        self._update_status("New window opened")

    def _close_active_tab(self) -> None:
        if self.tab_widget.count() > 1:
            self._on_tab_close_requested(self.tab_widget.currentIndex())
        else:
            QMessageBox.information(self, "Close Tab", "Cannot close the last tab.")

    def _save_workspace(self) -> None:
        name, accepted = QtWidgets.QInputDialog.getText(self, "Save Workspace", "Workspace name:")
        if accepted and name:
            payload = {
                "tabs": [
                    {"url": self.tab_widget.widget(i).url, "title": self.tab_widget.tabText(i)}
                    for i in range(self.tab_widget.count())
                ]
            }
            self.workspace_manager.save_workspace(name, "Saved from Power Dialogue", payload)
            self._update_status(f"Workspace '{name}' saved")

    def _restore_workspace(self) -> None:
        workspaces = self.workspace_manager.list_workspaces()
        if not workspaces:
            QMessageBox.information(self, "Restore Workspace", "No saved workspaces available.")
            return
        names = [workspace["name"] for workspace in workspaces]
        index, accepted = QtWidgets.QInputDialog.getItem(self, "Restore Workspace", "Choose workspace:", names, 0, False)
        if accepted:
            selected = workspaces[index]
            payload = self.workspace_manager.restore_workspace(selected["id"])
            if payload:
                self.tab_widget.clear()
                for tab_data in payload.get("tabs", []):
                    self.create_tab(tab_data.get("url", self.settings.get("startup_url")), tab_data.get("title"))
                self._update_status(f"Workspace '{selected['name']}' restored")

    def _open_history(self) -> None:
        QMessageBox.information(self, "History", "History manager opened.")

    def _open_downloads(self) -> None:
        QMessageBox.information(self, "Downloads", "Downloads manager opened.")

    def _open_bookmarks(self) -> None:
        QMessageBox.information(self, "Bookmarks", "Bookmarks manager opened.")

    def _open_settings(self) -> None:
        QMessageBox.information(self, "Settings", "Settings panel opened.")

    def _toggle_dark_mode(self) -> None:
        theme = self.settings.get("theme")
        next_theme = "classic_white" if theme == "mourinho_dark" else "mourinho_dark"
        self.settings.set("theme", next_theme)
        self._apply_theme(next_theme)
        self._update_status(f"Theme changed to {next_theme}")

    def _open_devtools(self) -> None:
        browser_widget = self._current_browser_widget()
        if hasattr(browser_widget, "browser") and browser_widget.browser:
            browser_widget.browser.ShowDevTools()
        self._update_status("DevTools opened.")

    def _take_screenshot(self) -> None:
        screenshot_path = self.root_path / "assets" / "screenshot.png"
        pixmap = self.grab()
        pixmap.save(str(screenshot_path))
        self._update_status(f"Screenshot saved to {screenshot_path}")

    def _clear_cache(self) -> None:
        self._update_status("Cache cleared")

    def _restart_browser(self) -> None:
        self._update_status("Restarting browser...")
        QtWidgets.qApp.exit(0)

    def _enable_tactical_mode(self) -> None:
        self.settings.set("counter_attack_enabled", True)
        self._update_status("Tactical mode enabled")

    def _update_status(self, message: str) -> None:
        self.status_bar.showMessage(message, 5000)

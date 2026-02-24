"""Main window — tab-based shell."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from ui.match_screen import MatchScreen
from ui.leaderboard_screen import LeaderboardScreen
from ui.combo_screen import ComboScreen
from ui.add_names_screen import AddNamesScreen
from ui.settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nominis")
        self.resize(900, 680)
        self.setMinimumSize(700, 520)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.match_screen = MatchScreen()
        self.leaderboard_screen = LeaderboardScreen()
        self.combo_screen = ComboScreen()
        self.add_names_screen = AddNamesScreen()
        self.settings_screen = SettingsScreen()

        self.tabs.addTab(self.match_screen, "⚔  Match")
        self.tabs.addTab(self.leaderboard_screen, "🏆  Leaderboard")
        self.tabs.addTab(self.combo_screen, "✨  Name Combos")
        self.tabs.addTab(self.add_names_screen, "➕  Add Names")
        self.tabs.addTab(self.settings_screen, "⚙  Settings")

        # Refresh relevant screens on tab switch
        self.tabs.currentChanged.connect(self._on_tab_changed)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

    def _on_tab_changed(self, idx: int):
        widget = self.tabs.widget(idx)
        if hasattr(widget, "refresh"):
            widget.refresh()

"""Leaderboard screen — top 10 per profile + combined."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QButtonGroup,
    QAbstractItemView,
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from sqlalchemy import func
from database.db import get_session
from database.models import ProfileName, Name, Gender
from styles.theme import COLORS

GENDER_LABELS = {
    "All": None,
    "♂ Masc": Gender.M,
    "♀ Fem": Gender.F,
    "⚥ Neutral": Gender.N,
}
TOP_N = 10


class LeaderboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._gender_filter: Gender | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Leaderboard")
        title.setObjectName("h1")
        hdr.addWidget(title)
        hdr.addStretch()

        # Gender filter chips
        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        for i, (lbl, g) in enumerate(GENDER_LABELS.items()):
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setFixedHeight(28)
            btn.setStyleSheet(self._chip_style(i == 0))
            btn.clicked.connect(lambda _, gl=g, b=btn: self._set_gender(gl, b))
            self._filter_group.addButton(btn, i)
            hdr.addWidget(btn)

        root.addLayout(hdr)

        # Three-column table layout
        cols = QHBoxLayout()
        cols.setSpacing(16)

        self._tbl_husband = self._make_table("Husband", COLORS["blue"])
        self._tbl_wife = self._make_table("Wife", COLORS["pink"])
        self._tbl_combined = self._make_table("Combined", COLORS["laven"])

        for tbl_widget in (self._tbl_husband, self._tbl_wife, self._tbl_combined):
            cols.addWidget(tbl_widget)

        root.addLayout(cols, stretch=1)

    def _make_table(self, heading: str, color: str) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)

        lbl = QLabel(heading)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 15px;")
        vbox.addWidget(lbl)

        tbl = QTableWidget(0, 3)
        tbl.setHorizontalHeaderLabels(["#", "Name", "Elo"])
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.setFocusPolicy(Qt.NoFocus)
        tbl.setObjectName("leaderboard_table")
        vbox.addWidget(tbl)

        # store reference by heading
        setattr(self, f"_tbl_{heading.lower()}", tbl)
        return container

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        g = self._gender_filter
        self._populate(self._tbl_husband, self._get_top(1, g), COLORS["blue"])
        self._populate(self._tbl_wife, self._get_top(2, g), COLORS["pink"])
        self._populate(self._tbl_combined, self._get_combined(g), COLORS["laven"])

    def _get_top(
        self, profile_id: int, gender: Gender | None
    ) -> list[tuple[str, float]]:
        with get_session() as s:
            q = (
                s.query(Name.text, ProfileName.elo_score)
                .join(ProfileName, ProfileName.name_id == Name.id)
                .filter(ProfileName.profile_id == profile_id)
            )
            if gender:
                q = q.filter(Name.gender == gender)
            rows = q.order_by(ProfileName.elo_score.desc()).limit(TOP_N).all()
        return [(r[0], r[1]) for r in rows]

    def _get_combined(self, gender: Gender | None) -> list[tuple[str, float]]:
        """Average Elo across both profiles."""
        with get_session() as s:
            q = (
                s.query(Name.text, func.avg(ProfileName.elo_score).label("avg_elo"))
                .join(ProfileName, ProfileName.name_id == Name.id)
                .filter(ProfileName.profile_id.in_([1, 2]))
            )
            if gender:
                q = q.filter(Name.gender == gender)
            rows = (
                q.group_by(Name.id)
                .order_by(func.avg(ProfileName.elo_score).desc())
                .limit(TOP_N)
                .all()
            )
        return [(r[0], r[1]) for r in rows]

    def _populate(self, tbl: QTableWidget, rows: list[tuple[str, float]], color: str):
        tbl.setRowCount(0)
        for rank, (name_text, elo) in enumerate(rows, 1):
            tbl.insertRow(rank - 1)
            rank_item = QTableWidgetItem(str(rank))
            rank_item.setTextAlignment(Qt.AlignCenter)
            name_item = QTableWidgetItem(name_text)
            elo_item = QTableWidgetItem(f"{elo:.0f}")
            elo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if rank == 1:
                for item in (rank_item, name_item, elo_item):
                    item.setForeground(QColor(color))
            tbl.setItem(rank - 1, 0, rank_item)
            tbl.setItem(rank - 1, 1, name_item)
            tbl.setItem(rank - 1, 2, elo_item)

    # ── Filters ───────────────────────────────────────────────────────────────

    def _set_gender(self, gender: Gender | None, btn: QPushButton):
        self._gender_filter = gender
        # Update chip styles
        for b in self._filter_group.buttons():
            b.setStyleSheet(self._chip_style(b is btn))
        self.refresh()

    def _chip_style(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton {{ background: {COLORS['blue']}; color: {COLORS['bg0']}; "
                f"border-radius: 14px; padding: 2px 12px; font-size: 12px; font-weight: bold; }}"
            )
        return (
            f"QPushButton {{ background: {COLORS['bg2']}; color: {COLORS['muted']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 14px; "
            f"padding: 2px 12px; font-size: 12px; }}"
            f"QPushButton:hover {{ color: {COLORS['text']}; }}"
        )

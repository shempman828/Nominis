"""Leaderboard screen — top combos per profile + combined."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func

from database.db import get_session, get_setting
from database.models import Gender, Name, NameCombo
from styles.theme import COLORS

GENDER_LABELS = {
    "All": None,
    "♂ Masc": "M",
    "♀ Fem": "F",
}
TOP_N = 15


class LeaderboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._gender_filter: str | None = None  # "M", "F", or None
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

        subtitle = QLabel("Rankings show first · middle name combinations.")
        subtitle.setObjectName("muted")
        root.addWidget(subtitle)

        # Three-column table layout
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # NOTE: store table widgets directly — avoid name collision with containers
        self._tbl_husband = self._make_table_section("Husband", COLORS["blue"])
        self._tbl_wife = self._make_table_section("Wife", COLORS["pink"])
        self._tbl_combined = self._make_table_section("Combined", COLORS["laven"])

        for container in (
            self._container_husband,
            self._container_wife,
            self._container_combined,
        ):
            cols.addWidget(container)

        root.addLayout(cols, stretch=1)

    def _make_table_section(self, heading: str, color: str) -> QTableWidget:
        """Create a labeled table section. Returns the QTableWidget; stores container."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)

        lbl = QLabel(heading)
        lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 15px;")
        vbox.addWidget(lbl)

        tbl = QTableWidget(0, 4)
        tbl.setHorizontalHeaderLabels(["#", "First", "Middle", "Elo"])
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.setFocusPolicy(Qt.NoFocus)
        vbox.addWidget(tbl)

        # Store container separately from the table widget
        setattr(self, f"_container_{heading.lower()}", container)
        return tbl

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        g = self._gender_filter
        self._populate(self._tbl_husband, self._get_top(1, g), COLORS["blue"])
        self._populate(self._tbl_wife, self._get_top(2, g), COLORS["pink"])
        self._populate(self._tbl_combined, self._get_combined(g), COLORS["laven"])

    def _eligible_gender_values(self, mode: str | None):
        """Return Gender enum values eligible for a mode filter."""
        if mode == "M":
            return [Gender.M, Gender.N]
        elif mode == "F":
            return [Gender.F, Gender.N]
        return None  # no filter

    def _get_top(
        self, profile_id: int, mode: str | None
    ) -> list[tuple[str, str, float]]:
        eligible = self._eligible_gender_values(mode)
        with get_session() as s:
            Name.__table__.alias("first_name")
            Name.__table__.alias("middle_name")

            q = s.query(
                NameCombo.first_id,
                NameCombo.middle_id,
                NameCombo.elo_score,
            ).filter(NameCombo.profile_id == profile_id)

            if eligible:
                first_ids = {
                    n.id for n in s.query(Name).filter(Name.gender.in_(eligible)).all()
                }
                q = q.filter(
                    NameCombo.first_id.in_(first_ids),
                    NameCombo.middle_id.in_(first_ids),
                )

            rows = q.order_by(NameCombo.elo_score.desc()).limit(TOP_N).all()

            result = []
            for first_id, middle_id, elo in rows:
                fn = s.get(Name, first_id)
                mn = s.get(Name, middle_id)
                result.append((fn.text, mn.text, elo))
        return result

    def _get_combined(self, mode: str | None) -> list[tuple[str, str, float]]:
        """Average Elo across both profiles."""
        eligible = self._eligible_gender_values(mode)
        with get_session() as s:
            q = s.query(
                NameCombo.first_id,
                NameCombo.middle_id,
                func.avg(NameCombo.elo_score).label("avg_elo"),
            ).filter(NameCombo.profile_id.in_([1, 2]))

            if eligible:
                eligible_ids = {
                    n.id for n in s.query(Name).filter(Name.gender.in_(eligible)).all()
                }
                q = q.filter(
                    NameCombo.first_id.in_(eligible_ids),
                    NameCombo.middle_id.in_(eligible_ids),
                )

            rows = (
                q.group_by(NameCombo.first_id, NameCombo.middle_id)
                .order_by(func.avg(NameCombo.elo_score).desc())
                .limit(TOP_N)
                .all()
            )

            result = []
            for first_id, middle_id, avg_elo in rows:
                fn = s.get(Name, first_id)
                mn = s.get(Name, middle_id)
                result.append((fn.text, mn.text, avg_elo))
        return result

    def _populate(
        self, tbl: QTableWidget, rows: list[tuple[str, str, float]], color: str
    ):
        tbl.setRowCount(0)
        get_setting("surname") or "Smith"
        for rank, (first, middle, elo) in enumerate(rows, 1):
            tbl.insertRow(rank - 1)
            rank_item = QTableWidgetItem(str(rank))
            rank_item.setTextAlignment(Qt.AlignCenter)
            first_item = QTableWidgetItem(first)
            middle_item = QTableWidgetItem(middle)
            elo_item = QTableWidgetItem(f"{elo:.0f}")
            elo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if rank == 1:
                for item in (rank_item, first_item, middle_item, elo_item):
                    item.setForeground(QColor(color))

            tbl.setItem(rank - 1, 0, rank_item)
            tbl.setItem(rank - 1, 1, first_item)
            tbl.setItem(rank - 1, 2, middle_item)
            tbl.setItem(rank - 1, 3, elo_item)

    # ── Filters ───────────────────────────────────────────────────────────────

    def _set_gender(self, mode: str | None, btn: QPushButton):
        self._gender_filter = mode
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

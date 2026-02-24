"""Match (this-or-that) screen."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
    QRadioButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from database.db import get_session
from database.models import Name, ProfileName
from logic.matchmaker import pick_pair
from logic.elo import update_elo, record_skip
from styles.theme import COLORS


class MatchScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._profile_id = 1  # default: Husband
        self._name_a: Name | None = None
        self._name_b: Name | None = None
        self._build_ui()
        self._ensure_profile_names()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Match")
        title.setObjectName("h1")
        hdr.addWidget(title)
        hdr.addStretch()

        # Profile selector
        self._profile_group = QButtonGroup(self)
        for pid, label, color in (
            (1, "Husband", COLORS["blue"]),
            (2, "Wife", COLORS["pink"]),
        ):
            rb = QRadioButton(label)
            rb.setStyleSheet(
                f"QRadioButton::indicator:checked {{ background: {color}; border-color: {color}; }}"
                f"QRadioButton {{ color: {color}; font-weight: bold; }}"
            )
            rb.setChecked(pid == 1)
            rb.toggled.connect(
                lambda checked, p=pid: self._set_profile(p) if checked else None
            )
            self._profile_group.addButton(rb, pid)
            hdr.addWidget(rb)
            hdr.addSpacing(8)

        root.addLayout(hdr)

        # Session stats
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("muted")
        self._stats_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self._stats_label)

        # Battle area
        battle = QHBoxLayout()
        battle.setSpacing(24)

        self._btn_a = QPushButton("")
        self._btn_a.setObjectName("name_card_a")
        self._btn_a.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._btn_a.clicked.connect(lambda: self._choose("a"))

        vs = QLabel("VS")
        vs.setAlignment(Qt.AlignCenter)
        vs.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 20px; font-weight: bold;"
        )
        vs.setFixedWidth(40)

        self._btn_b = QPushButton("")
        self._btn_b.setObjectName("name_card_b")
        self._btn_b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._btn_b.clicked.connect(lambda: self._choose("b"))

        battle.addWidget(self._btn_a)
        battle.addWidget(vs)
        battle.addWidget(self._btn_b)
        root.addLayout(battle, stretch=1)

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.addStretch()

        self._skip_btn = QPushButton("Skip  (↑)")
        self._skip_btn.setObjectName("skip_btn")
        self._skip_btn.clicked.connect(self._skip)
        ctrl.addWidget(self._skip_btn)
        ctrl.addStretch()

        root.addLayout(ctrl)

        # Hint
        hint = QLabel(
            "← Left arrow  /  Right arrow →  to choose  ·  ↑ Up arrow to skip"
        )
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

        # Feedback label
        self._feedback = QLabel("")
        self._feedback.setAlignment(Qt.AlignCenter)
        self._feedback.setStyleSheet("font-size: 13px;")
        root.addWidget(self._feedback)

        self.setFocusPolicy(Qt.StrongFocus)

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Left:
            self._choose("a")
        elif key == Qt.Key_Right:
            self._choose("b")
        elif key == Qt.Key_Up:
            self._skip()
        else:
            super().keyPressEvent(event)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _set_profile(self, pid: int):
        self._profile_id = pid
        self._session_wins = 0
        self._session_total = 0
        self._ensure_profile_names()
        self.refresh()

    def _ensure_profile_names(self):
        """Make sure every Name has a ProfileName row for the active profile."""
        with get_session() as s:
            all_names = s.query(Name).all()
            existing = {
                pn.name_id
                for pn in s.query(ProfileName)
                .filter_by(profile_id=self._profile_id)
                .all()
            }
            new_rows = [
                ProfileName(profile_id=self._profile_id, name_id=n.id)
                for n in all_names
                if n.id not in existing
            ]
            if new_rows:
                s.add_all(new_rows)
                s.commit()

    def refresh(self):
        self._session_wins = getattr(self, "_session_wins", 0)
        self._session_total = getattr(self, "_session_total", 0)
        self._load_next_pair()

    def _load_next_pair(self):
        pair = pick_pair(self._profile_id)
        if not pair:
            self._btn_a.setText("Add more\nnames to play!")
            self._btn_b.setText("")
            self._btn_b.setEnabled(False)
            self._skip_btn.setEnabled(False)
            return

        self._btn_b.setEnabled(True)
        self._skip_btn.setEnabled(True)

        id_a, id_b = pair
        with get_session() as s:
            self._name_a = s.get(Name, id_a)
            self._name_b = s.get(Name, id_b)

        self._btn_a.setText(self._name_a.text)
        self._btn_b.setText(self._name_b.text)
        self._feedback.setText("")
        self._update_stats()
        self.setFocus()

    def _choose(self, side: str):
        if not self._name_a or not self._name_b:
            return
        winner = self._name_a if side == "a" else self._name_b
        loser = self._name_b if side == "a" else self._name_a
        update_elo(self._profile_id, winner.id, loser.id)
        self._session_wins += 1
        self._session_total += 1
        color = COLORS["blue"] if side == "a" else COLORS["pink"]
        self._flash_feedback(f"✓  {winner.text} wins this round", color)
        QTimer.singleShot(350, self._load_next_pair)

    def _skip(self):
        if not self._name_a or not self._name_b:
            return
        record_skip(self._profile_id, self._name_a.id, self._name_b.id)
        self._session_total += 1
        self._flash_feedback("Skipped — both names re-queued", COLORS["muted"])
        QTimer.singleShot(350, self._load_next_pair)

    def _flash_feedback(self, msg: str, color: str):
        self._feedback.setText(msg)
        self._feedback.setStyleSheet(f"font-size: 13px; color: {color};")

    def _update_stats(self):
        total = self._session_total
        self._stats_label.setText(
            f"Session: {total} match{'es' if total != 1 else ''} played"
        )

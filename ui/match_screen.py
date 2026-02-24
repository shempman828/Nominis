"""Match (this-or-that) screen — votes on (first, middle, surname) combos."""

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
from database.db import get_session, get_setting
from database.models import NameCombo, Name
from logic.matchmaker import pick_combo_pair
from logic.elo import update_elo, record_skip
from styles.theme import COLORS


class MatchScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._profile_id = 1  # 1 = Husband, 2 = Wife
        self._gender_mode = "M"  # "M" or "F"
        self._combo_a: NameCombo | None = None
        self._combo_b: NameCombo | None = None
        self._session_total = 0
        self._build_ui()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        # ── Header row ────────────────────────────────────────────────────────
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

        hdr.addSpacing(16)

        # Gender mode selector
        self._gender_group = QButtonGroup(self)
        for gid, label, color in (
            ("M", "♂ Masculine", COLORS["blue"]),
            ("F", "♀ Feminine", COLORS["pink"]),
        ):
            rb = QRadioButton(label)
            rb.setStyleSheet(
                f"QRadioButton::indicator:checked {{ background: {color}; border-color: {color}; }}"
                f"QRadioButton {{ color: {color}; }}"
            )
            rb.setChecked(gid == "M")
            rb.toggled.connect(
                lambda checked, g=gid: self._set_gender(g) if checked else None
            )
            self._gender_group.addButton(rb)
            hdr.addWidget(rb)
            hdr.addSpacing(6)

        root.addLayout(hdr)

        # ── Session stats ─────────────────────────────────────────────────────
        self._stats_label = QLabel("")
        self._stats_label.setObjectName("muted")
        self._stats_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self._stats_label)

        # ── Battle area ───────────────────────────────────────────────────────
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

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.addStretch()
        self._skip_btn = QPushButton("Skip  (↑)")
        self._skip_btn.setObjectName("skip_btn")
        self._skip_btn.clicked.connect(self._skip)
        ctrl.addWidget(self._skip_btn)
        ctrl.addStretch()
        root.addLayout(ctrl)

        hint = QLabel(
            "← Left arrow  /  Right arrow →  to choose  ·  ↑ Up arrow to skip"
        )
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

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

    # ── State changes ─────────────────────────────────────────────────────────

    def _set_profile(self, pid: int):
        self._profile_id = pid
        self._session_total = 0
        self._load_next_pair()

    def _set_gender(self, mode: str):
        self._gender_mode = mode
        self._load_next_pair()

    def refresh(self):
        self._load_next_pair()

    # ── Combo loading ─────────────────────────────────────────────────────────

    def _combo_label(self, combo: NameCombo) -> str:
        surname = get_setting("surname") or "Smith"
        return f"{combo.first.text}\n{combo.middle.text}\n{surname}"

    def _load_next_pair(self):
        pair = pick_combo_pair(self._profile_id, self._gender_mode)

        if not pair:
            self._btn_a.setText("Add more names\nto play!")
            self._btn_b.setText("")
            self._btn_b.setEnabled(False)
            self._skip_btn.setEnabled(False)
            self._update_stats()
            return

        self._btn_b.setEnabled(True)
        self._skip_btn.setEnabled(True)

        id_a, id_b = pair
        with get_session() as s:
            combo_a = s.get(NameCombo, id_a)
            combo_b = s.get(NameCombo, id_b)
            # Eagerly load relationships before session closes
            self._combo_a_id = combo_a.id
            self._combo_b_id = combo_b.id
            first_a = s.get(Name, combo_a.first_id).text
            mid_a = s.get(Name, combo_a.middle_id).text
            first_b = s.get(Name, combo_b.first_id).text
            mid_b = s.get(Name, combo_b.middle_id).text

        surname = get_setting("surname") or "Smith"
        self._btn_a.setText(f"{first_a}\n{mid_a}\n{surname}")
        self._btn_b.setText(f"{first_b}\n{mid_b}\n{surname}")
        self._feedback.setText("")
        self._update_stats()
        self.setFocus()

    # ── Vote / skip ───────────────────────────────────────────────────────────

    def _choose(self, side: str):
        if not hasattr(self, "_combo_a_id") or not hasattr(self, "_combo_b_id"):
            return
        winner_id = self._combo_a_id if side == "a" else self._combo_b_id
        loser_id = self._combo_b_id if side == "a" else self._combo_a_id

        # Get winner name for feedback
        with get_session() as s:
            w = s.get(NameCombo, winner_id)
            first_text = s.get(Name, w.first_id).text
            mid_text = s.get(Name, w.middle_id).text

        update_elo(self._profile_id, winner_id, loser_id)
        self._session_total += 1
        color = COLORS["blue"] if side == "a" else COLORS["pink"]
        self._flash_feedback(f"✓  {first_text} {mid_text} wins this round", color)
        QTimer.singleShot(350, self._load_next_pair)

    def _skip(self):
        if not hasattr(self, "_combo_a_id") or not hasattr(self, "_combo_b_id"):
            return
        record_skip(self._profile_id, self._combo_a_id, self._combo_b_id)
        self._session_total += 1
        self._flash_feedback("Skipped — both combos re-queued", COLORS["muted"])
        QTimer.singleShot(350, self._load_next_pair)

    def _flash_feedback(self, msg: str, color: str):
        self._feedback.setText(msg)
        self._feedback.setStyleSheet(f"font-size: 13px; color: {color};")

    def _update_stats(self):
        total = self._session_total
        self._stats_label.setText(
            f"Session: {total} match{'es' if total != 1 else ''} played"
        )

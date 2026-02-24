"""Name combo generator screen."""

import random
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QButtonGroup,
    QRadioButton,
    QSpinBox,
    QScrollArea,
)
from sqlalchemy import func
from database.db import get_session, get_setting
from database.models import ProfileName, Name, Gender
from styles.theme import COLORS


class ComboScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Name Combos")
        title.setObjectName("h1")
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        sub = QLabel(
            "Randomly generated first · middle · last combinations drawn from top-ranked names."
        )
        sub.setObjectName("muted")
        root.addWidget(sub)

        # Options row
        opts = QHBoxLayout()
        opts.setSpacing(24)

        # Profile source
        opts.addWidget(QLabel("Source:"))
        self._src_group = QButtonGroup(self)
        for i, (lbl, color) in enumerate(
            [
                ("Husband", COLORS["blue"]),
                ("Wife", COLORS["pink"]),
                ("Combined", COLORS["laven"]),
            ]
        ):
            rb = QRadioButton(lbl)
            rb.setStyleSheet(
                f"QRadioButton {{ color: {color}; }}"
                f"QRadioButton::indicator:checked {{ background: {color}; border-color: {color}; }}"
            )
            rb.setChecked(i == 2)
            self._src_group.addButton(rb, i)
            opts.addWidget(rb)

        opts.addSpacing(16)

        # Gender filter
        opts.addWidget(QLabel("Gender:"))
        self._gen_group = QButtonGroup(self)
        for i, lbl in enumerate(["Any", "♂", "♀", "⚥"]):
            rb = QRadioButton(lbl)
            rb.setChecked(i == 0)
            self._gen_group.addButton(rb, i)
            opts.addWidget(rb)

        opts.addSpacing(16)

        # Count
        opts.addWidget(QLabel("Count:"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 20)
        self._count_spin.setValue(5)
        self._count_spin.setFixedWidth(60)
        opts.addWidget(self._count_spin)

        opts.addStretch()

        gen_btn = QPushButton("Generate  ✨")
        gen_btn.setObjectName("primary")
        gen_btn.clicked.connect(self._generate)
        opts.addWidget(gen_btn)

        root.addLayout(opts)

        # Scroll area for results
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setSpacing(10)
        self._results_layout.addStretch()
        self._scroll.setWidget(self._results_widget)
        root.addWidget(self._scroll, stretch=1)

    def refresh(self):
        pass  # no auto-refresh needed

    def _generate(self):
        # Clear old results
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        surname = get_setting("surname") or "Smith"
        src_id = self._src_group.checkedId()  # 0=Husband,1=Wife,2=Combined
        gen_id = self._gen_group.checkedId()  # 0=Any,1=M,2=F,3=N
        count = self._count_spin.value()

        gender_map = {0: None, 1: Gender.M, 2: Gender.F, 3: Gender.N}
        gender = gender_map[gen_id]

        pool = self._get_pool(src_id, gender)

        if len(pool) < 2:
            lbl = QLabel("Not enough names — add more or adjust filters.")
            lbl.setObjectName("muted")
            self._results_layout.insertWidget(0, lbl)
            return

        colors = [COLORS["blue"], COLORS["pink"], COLORS["laven"]]
        color = colors[src_id]

        for i in range(count):
            first, middle = random.sample(pool, 2)
            combo = f"{first}  {middle}  {surname}"
            card = self._make_card(i + 1, combo, color)
            self._results_layout.insertWidget(i, card)

    def _get_pool(self, src_id: int, gender: Gender | None) -> list[str]:
        """Return top-ranked names for the selected source."""
        with get_session() as s:
            if src_id == 2:  # Combined
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
                    .limit(30)
                    .all()
                )
                return [r[0] for r in rows]
            else:
                pid = src_id + 1  # 0→1 (Husband), 1→2 (Wife)
                q = (
                    s.query(Name.text)
                    .join(ProfileName, ProfileName.name_id == Name.id)
                    .filter(ProfileName.profile_id == pid)
                )
                if gender:
                    q = q.filter(Name.gender == gender)
                rows = q.order_by(ProfileName.elo_score.desc()).limit(30).all()
                return [r[0] for r in rows]

    def _make_card(self, rank: int, combo: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)

        num = QLabel(str(rank))
        num.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 13px; min-width: 24px;"
        )
        layout.addWidget(num)

        name_lbl = QLabel(combo)
        name_lbl.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold; letter-spacing: 2px;"
        )
        layout.addWidget(name_lbl, stretch=1)

        return card

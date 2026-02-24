"""Name combo generator screen — shows top-ranked first+middle+surname combinations."""

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
from database.models import NameCombo, Name, Gender
from styles.theme import COLORS


class ComboScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        hdr = QHBoxLayout()
        title = QLabel("Top Name Combos")
        title.setObjectName("h1")
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        sub = QLabel("Browse your highest-ranked first · middle · last combinations.")
        sub.setObjectName("muted")
        root.addWidget(sub)

        # Options row
        opts = QHBoxLayout()
        opts.setSpacing(24)

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

        opts.addWidget(QLabel("Gender:"))
        self._gen_group = QButtonGroup(self)
        for i, lbl in enumerate(["Any", "♂ Masc", "♀ Fem"]):
            rb = QRadioButton(lbl)
            rb.setChecked(i == 0)
            self._gen_group.addButton(rb, i)
            opts.addWidget(rb)

        opts.addSpacing(16)

        opts.addWidget(QLabel("Show top:"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 50)
        self._count_spin.setValue(10)
        self._count_spin.setFixedWidth(60)
        opts.addWidget(self._count_spin)

        opts.addStretch()

        gen_btn = QPushButton("Refresh  ✨")
        gen_btn.setObjectName("primary")
        gen_btn.clicked.connect(self._generate)
        opts.addWidget(gen_btn)

        root.addLayout(opts)

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
        self._generate()

    def _generate(self):
        # Clear old results
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        surname = get_setting("surname") or "Smith"
        src_id = self._src_group.checkedId()  # 0=Husband, 1=Wife, 2=Combined
        gen_id = self._gen_group.checkedId()  # 0=Any, 1=M, 2=F
        count = self._count_spin.value()

        gender_mode_map = {0: None, 1: "M", 2: "F"}
        gender_mode = gender_mode_map[gen_id]

        combos = self._get_top_combos(src_id, gender_mode, count)

        if not combos:
            lbl = QLabel("No combos yet — add names and start voting!")
            lbl.setObjectName("muted")
            self._results_layout.insertWidget(0, lbl)
            return

        colors = [COLORS["blue"], COLORS["pink"], COLORS["laven"]]
        color = colors[src_id]

        for i, (first, middle, elo) in enumerate(combos):
            full = f"{first}  {middle}  {surname}"
            card = self._make_card(i + 1, full, f"{elo:.0f}", color)
            self._results_layout.insertWidget(i, card)

    def _eligible_ids(self, s, mode: str | None) -> set[int] | None:
        if mode == "M":
            genders = [Gender.M, Gender.N]
        elif mode == "F":
            genders = [Gender.F, Gender.N]
        else:
            return None  # no filter
        return {n.id for n in s.query(Name).filter(Name.gender.in_(genders)).all()}

    def _get_top_combos(
        self, src_id: int, gender_mode: str | None, limit: int
    ) -> list[tuple[str, str, float]]:
        with get_session() as s:
            eligible = self._eligible_ids(s, gender_mode)

            if src_id == 2:  # Combined
                q = s.query(
                    NameCombo.first_id,
                    NameCombo.middle_id,
                    func.avg(NameCombo.elo_score).label("avg_elo"),
                ).filter(NameCombo.profile_id.in_([1, 2]))
                if eligible is not None:
                    q = q.filter(
                        NameCombo.first_id.in_(eligible),
                        NameCombo.middle_id.in_(eligible),
                    )
                rows = (
                    q.group_by(NameCombo.first_id, NameCombo.middle_id)
                    .order_by(func.avg(NameCombo.elo_score).desc())
                    .limit(limit)
                    .all()
                )
            else:
                pid = src_id + 1  # 0→1 (Husband), 1→2 (Wife)
                q = s.query(
                    NameCombo.first_id,
                    NameCombo.middle_id,
                    NameCombo.elo_score,
                ).filter(NameCombo.profile_id == pid)
                if eligible is not None:
                    q = q.filter(
                        NameCombo.first_id.in_(eligible),
                        NameCombo.middle_id.in_(eligible),
                    )
                rows = q.order_by(NameCombo.elo_score.desc()).limit(limit).all()

            result = []
            for first_id, middle_id, elo in rows:
                fn = s.get(Name, first_id)
                mn = s.get(Name, middle_id)
                result.append((fn.text, mn.text, float(elo)))
        return result

    def _make_card(self, rank: int, combo: str, elo: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)

        num = QLabel(str(rank))
        num.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 13px; min-width: 28px;"
        )
        layout.addWidget(num)

        name_lbl = QLabel(combo)
        name_lbl.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold; letter-spacing: 2px;"
        )
        layout.addWidget(name_lbl, stretch=1)

        elo_lbl = QLabel(f"Elo {elo}")
        elo_lbl.setStyleSheet(f"color: {COLORS['muted']}; font-size: 12px;")
        layout.addWidget(elo_lbl)

        return card

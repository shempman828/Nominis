"""Add names screen — single add + batch import."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QPlainTextEdit,
    QButtonGroup, QRadioButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from database.db import get_session
from database.models import Name, ProfileName, Gender
from styles.theme import COLORS


GENDER_OPTIONS = [("♂ Masculine", Gender.M), ("♀ Feminine", Gender.F), ("⚥ Neutral", Gender.N)]


class AddNamesScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(24)

        title = QLabel("Add Names")
        title.setObjectName("h1")
        root.addWidget(title)

        # ── Quick single add ──────────────────────────────────────────────────
        single_card = QFrame()
        single_card.setObjectName("card")
        sc_layout = QVBoxLayout(single_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)
        sc_layout.setSpacing(12)

        sc_title = QLabel("Quick Add")
        sc_title.setObjectName("h2")
        sc_layout.addWidget(sc_title)

        row = QHBoxLayout()
        self._single_input = QLineEdit()
        self._single_input.setPlaceholderText("Enter a name…")
        self._single_input.returnPressed.connect(self._add_single)
        row.addWidget(self._single_input, stretch=1)

        self._single_gender = self._gender_selector()
        row.addLayout(self._single_gender["layout"])

        add_btn = QPushButton("Add")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._add_single)
        row.addWidget(add_btn)
        sc_layout.addLayout(row)

        self._single_status = QLabel("")
        self._single_status.setObjectName("muted")
        sc_layout.addWidget(self._single_status)
        root.addWidget(single_card)

        # ── Batch add ─────────────────────────────────────────────────────────
        batch_card = QFrame()
        batch_card.setObjectName("card")
        bc_layout = QVBoxLayout(batch_card)
        bc_layout.setContentsMargins(20, 16, 20, 16)
        bc_layout.setSpacing(12)

        bc_title = QLabel("Batch Import")
        bc_title.setObjectName("h2")
        bc_layout.addWidget(bc_title)

        hint = QLabel(
            "One name per line. Optionally tag gender with  ,M  ,F  or  ,N  at the end.\n"
            "Example:  Aurora,F     River,N     James,M     Sage"
        )
        hint.setObjectName("muted")
        bc_layout.addWidget(hint)

        self._batch_input = QPlainTextEdit()
        self._batch_input.setPlaceholderText("Aurora,F\nRiver,N\nJames,M\nSage")
        self._batch_input.setMinimumHeight(140)
        bc_layout.addWidget(self._batch_input)

        batch_row = QHBoxLayout()
        batch_row.addStretch()

        self._batch_gender = self._gender_selector(label="Default gender:")
        batch_row.addLayout(self._batch_gender["layout"])

        batch_btn = QPushButton("Import Batch")
        batch_btn.setObjectName("primary")
        batch_btn.clicked.connect(self._add_batch)
        batch_row.addWidget(batch_btn)
        bc_layout.addLayout(batch_row)

        self._batch_status = QLabel("")
        self._batch_status.setObjectName("muted")
        bc_layout.addWidget(self._batch_status)

        root.addWidget(batch_card)
        root.addStretch()

    # ── Gender selector helper ────────────────────────────────────────────────

    def _gender_selector(self, label: str = "Gender:") -> dict:
        layout = QHBoxLayout()
        layout.setSpacing(8)
        lbl = QLabel(label)
        lbl.setObjectName("muted")
        layout.addWidget(lbl)
        group = QButtonGroup()
        for i, (lbl_text, g) in enumerate(GENDER_OPTIONS):
            rb = QRadioButton(lbl_text)
            rb.setChecked(i == 2)   # default Neutral
            group.addButton(rb, i)
            layout.addWidget(rb)
        return {"layout": layout, "group": group}

    def _selected_gender(self, selector: dict) -> Gender:
        return GENDER_OPTIONS[selector["group"].checkedId()][1]

    # ── Add logic ─────────────────────────────────────────────────────────────

    def _add_single(self):
        text = self._single_input.text().strip().title()
        if not text:
            return
        gender = self._selected_gender(self._single_gender)
        ok, msg = self._insert_name(text, gender)
        color = COLORS["blue"] if ok else COLORS["pink"]
        self._single_status.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._single_status.setText(msg)
        if ok:
            self._single_input.clear()

    def _add_batch(self):
        raw     = self._batch_input.toPlainText().strip()
        lines   = [l.strip() for l in raw.splitlines() if l.strip()]
        default = self._selected_gender(self._batch_gender)

        added = skipped = errors = 0
        for line in lines:
            parts = [p.strip() for p in line.rsplit(",", 1)]
            name_text = parts[0].title()
            if not name_text:
                continue
            if len(parts) == 2 and parts[1].upper() in ("M", "F", "N"):
                gender = Gender(parts[1].upper())
            else:
                gender = default
            ok, _ = self._insert_name(name_text, gender)
            if ok:
                added += 1
            else:
                skipped += 1

        msg = f"✓ {added} added"
        if skipped:
            msg += f"  ·  {skipped} skipped (duplicate)"
        self._batch_status.setText(msg)
        self._batch_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 12px;")
        if added:
            self._batch_input.clear()

    def _insert_name(self, text: str, gender: Gender) -> tuple[bool, str]:
        with get_session() as s:
            existing = s.query(Name).filter(Name.text == text).first()
            if existing:
                return False, f""{text}" already exists."
            name = Name(text=text, gender=gender)
            s.add(name)
            s.flush()
            # Create ProfileName rows for both profiles
            for pid in (1, 2):
                s.add(ProfileName(profile_id=pid, name_id=name.id))
            s.commit()
        return True, f"✓ "{text}" added."

    def refresh(self):
        pass

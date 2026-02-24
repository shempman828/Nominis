"""Settings screen."""

from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from database.db import get_setting, set_setting


class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(24)

        title = QLabel("Settings")
        title.setObjectName("h1")
        root.addWidget(title)

        # ── General ───────────────────────────────────────────────────────────
        gen_card = self._section_card("General")
        gen_form = QFormLayout()
        gen_form.setSpacing(12)

        self._surname_input = QLineEdit()
        self._surname_input.setMaximumWidth(200)
        gen_form.addRow("Family surname:", self._surname_input)

        gen_card.layout().addLayout(gen_form)
        root.addWidget(gen_card)

        # ── Matchmaking ───────────────────────────────────────────────────────
        mm_card = self._section_card("Matchmaking")
        mm_form = QFormLayout()
        mm_form.setSpacing(12)

        self._rand_pct = QSpinBox()
        self._rand_pct.setRange(0, 100)
        self._rand_pct.setSuffix(" %")
        self._rand_pct.setMaximumWidth(100)
        self._rand_pct.setToolTip(
            "Probability of a random distal match (calibration). Default: 30%"
        )
        mm_form.addRow("Random match %:", self._rand_pct)

        self._spread_thresh = QSpinBox()
        self._spread_thresh.setRange(0, 500)
        self._spread_thresh.setMaximumWidth(100)
        self._spread_thresh.setToolTip(
            "Elo std dev before blended matching activates. Default: 50"
        )
        mm_form.addRow("Spread threshold:", self._spread_thresh)

        mm_card.layout().addLayout(mm_form)
        root.addWidget(mm_card)

        # ── Elo ───────────────────────────────────────────────────────────────
        elo_card = self._section_card("Elo System")
        elo_form = QFormLayout()
        elo_form.setSpacing(12)

        self._k_default = QSpinBox()
        self._k_default.setRange(1, 128)
        self._k_default.setMaximumWidth(100)
        self._k_default.setToolTip(
            "K-factor for new names (< stable threshold). Default: 32"
        )
        elo_form.addRow("K-factor (new):", self._k_default)

        self._k_stable = QSpinBox()
        self._k_stable.setRange(1, 128)
        self._k_stable.setMaximumWidth(100)
        self._k_stable.setToolTip("K-factor for established names. Default: 16")
        elo_form.addRow("K-factor (stable):", self._k_stable)

        self._k_threshold = QSpinBox()
        self._k_threshold.setRange(1, 200)
        self._k_threshold.setMaximumWidth(100)
        self._k_threshold.setToolTip(
            "Matches before a name is considered stable. Default: 20"
        )
        elo_form.addRow("Stability threshold:", self._k_threshold)

        elo_card.layout().addLayout(elo_form)
        root.addWidget(elo_card)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primary")
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

        root.addStretch()
        self.refresh()

    def _section_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        lbl = QLabel(title)
        lbl.setObjectName("h2")
        layout.addWidget(lbl)
        return card

    def refresh(self):
        self._surname_input.setText(get_setting("surname") or "Smith")
        self._rand_pct.setValue(int(get_setting("match_random_pct") or 30))
        self._spread_thresh.setValue(int(get_setting("elo_spread_thresh") or 50))
        self._k_default.setValue(int(get_setting("k_factor_default") or 32))
        self._k_stable.setValue(int(get_setting("k_factor_stable") or 16))
        self._k_threshold.setValue(int(get_setting("k_stable_threshold") or 20))

    def _save(self):
        set_setting("surname", self._surname_input.text().strip() or "Smith")
        set_setting("match_random_pct", str(self._rand_pct.value()))
        set_setting("elo_spread_thresh", str(self._spread_thresh.value()))
        set_setting("k_factor_default", str(self._k_default.value()))
        set_setting("k_factor_stable", str(self._k_stable.value()))
        set_setting("k_stable_threshold", str(self._k_threshold.value()))

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Saved")
        dlg.setText("Settings saved successfully.")
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

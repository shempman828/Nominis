"""Global dark theme — baby blue/pink accent palette."""

BLUE = "#89cff0"
PINK = "#ffb6c1"
LAVEN = "#c3b1e1"

BG0 = "#12121e"  # window background
BG1 = "#1a1a2e"  # card / panel background
BG2 = "#22223a"  # input / hover background
BORDER = "#2e2e4a"
TEXT = "#e8e8f0"
MUTED = "#888899"

STYLESHEET = f"""
/* ── Global ─────────────────────────────────────────── */
QWidget {{
    background-color: {BG0};
    color: {TEXT};
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 14px;
}}

QMainWindow, QDialog {{
    background-color: {BG0};
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background-color: {BG2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 20px;
}}
QPushButton:hover {{
    background-color: #2e2e50;
    border-color: {BLUE};
}}
QPushButton:pressed {{
    background-color: #1e1e38;
}}
QPushButton#primary {{
    background-color: {BLUE};
    color: {BG0};
    border: none;
    font-weight: bold;
}}
QPushButton#primary:hover {{
    background-color: #a8dff7;
}}
QPushButton#husband {{
    border: 2px solid {BLUE};
    color: {BLUE};
    background: transparent;
    font-size: 18px;
    font-weight: bold;
    border-radius: 12px;
    padding: 24px 40px;
}}
QPushButton#husband:hover {{
    background-color: rgba(137, 207, 240, 0.12);
}}
QPushButton#wife {{
    border: 2px solid {PINK};
    color: {PINK};
    background: transparent;
    font-size: 18px;
    font-weight: bold;
    border-radius: 12px;
    padding: 24px 40px;
}}
QPushButton#wife:hover {{
    background-color: rgba(255, 182, 193, 0.12);
}}
QPushButton#skip_btn {{
    background: transparent;
    border: 1px solid {MUTED};
    color: {MUTED};
    border-radius: 6px;
    padding: 4px 16px;
    font-size: 12px;
}}
QPushButton#skip_btn:hover {{
    border-color: {LAVEN};
    color: {LAVEN};
}}

/* ── Cards ───────────────────────────────────────────── */
QFrame#card {{
    background-color: {BG1};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

/* ── Name battle cards ───────────────────────────────── */
QPushButton#name_card_a {{
    background-color: {BG1};
    border: 2px solid {BLUE};
    border-radius: 16px;
    color: {TEXT};
    font-size: 26px;
    font-weight: bold;
    padding: 40px 32px;
    min-width: 200px;
    min-height: 120px;
}}
QPushButton#name_card_a:hover {{
    background-color: rgba(137, 207, 240, 0.10);
    border-color: #a8dff7;
}}
QPushButton#name_card_b {{
    background-color: {BG1};
    border: 2px solid {PINK};
    border-radius: 16px;
    color: {TEXT};
    font-size: 26px;
    font-weight: bold;
    padding: 40px 32px;
    min-width: 200px;
    min-height: 120px;
}}
QPushButton#name_card_b:hover {{
    background-color: rgba(255, 182, 193, 0.10);
    border-color: #ffd0d8;
}}

/* ── Inputs ──────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG2};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {BLUE};
}}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {{
    background-color: {BG2};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    color: {TEXT};
}}
QComboBox QAbstractItemView {{
    background-color: {BG1};
    selection-background-color: {BG2};
    border: 1px solid {BORDER};
    color: {TEXT};
}}

/* ── Tables ──────────────────────────────────────────── */
QTableWidget {{
    background-color: {BG1};
    gridline-color: {BORDER};
    border: none;
    border-radius: 8px;
}}
QTableWidget::item {{
    padding: 6px 12px;
}}
QTableWidget::item:selected {{
    background-color: {BG2};
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {BG0};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 12px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Labels ──────────────────────────────────────────── */
QLabel#h1 {{
    font-size: 28px;
    font-weight: bold;
    color: {TEXT};
}}
QLabel#h2 {{
    font-size: 18px;
    font-weight: bold;
    color: {TEXT};
}}
QLabel#muted {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#blue {{
    color: {BLUE};
    font-weight: bold;
}}
QLabel#pink {{
    color: {PINK};
    font-weight: bold;
}}
QLabel#lavender {{
    color: {LAVEN};
    font-weight: bold;
}}

/* ── Tab bar ─────────────────────────────────────────── */
QTabBar::tab {{
    background: transparent;
    color: {MUTED};
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {BLUE};
}}
QTabBar::tab:hover {{
    color: {TEXT};
}}
QTabWidget::pane {{
    border: none;
}}

/* ── Scrollbar ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG0};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── Radio buttons ───────────────────────────────────── */
QRadioButton {{
    spacing: 6px;
    color: {TEXT};
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid {BORDER};
    background: {BG2};
}}
QRadioButton::indicator:checked {{
    background: {BLUE};
    border-color: {BLUE};
}}

/* ── Separator ───────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}
"""

# Expose colors for programmatic use
COLORS = {
    "blue": BLUE,
    "pink": PINK,
    "laven": LAVEN,
    "bg0": BG0,
    "bg1": BG1,
    "bg2": BG2,
    "border": BORDER,
    "text": TEXT,
    "muted": MUTED,
}

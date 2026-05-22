"""
views/styles.py
───────────────
Centralised Qt stylesheet for the entire STASH application.
Import APP_STYLE and pass it to QApplication.setStyleSheet() in main.py,
or apply per-window via self.setStyleSheet(APP_STYLE).
"""

APP_STYLE = """
/* ── Global ──────────────────────────────────────── */
QMainWindow, QDialog { background: #f0f2f5; }
QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: #2d3748; }

/* ── Sidebar ─────────────────────────────────────── */
QWidget#sidebar {
    background-color: #16213e;
    min-width: 215px;
    max-width: 215px;
}
QLabel#brand_lbl {
    color: #c0392b;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 5px;
}
QLabel#user_name  { color: #ffffff; font-size: 13px; font-weight: bold; }
QLabel#user_role  { color: #90cdf4; font-size: 11px; }
QLabel#user_dept  { color: #68d391; font-size: 11px; }

QPushButton#nav_btn {
    background: transparent;
    color: #a0aec0;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    text-align: left;
    font-size: 13px;
}
QPushButton#nav_btn:hover              { background: #1e3a6e; color: #ffffff; }
QPushButton#nav_btn[active="true"]     { background: #c0392b; color: #ffffff;
                                         font-weight: bold; }

QPushButton#logout_btn {
    background: #c0392b; color: white;
    border: none; border-radius: 8px;
    padding: 10px 14px; font-size: 13px; font-weight: bold;
}
QPushButton#logout_btn:hover { background: #922b21; }

/* ── Content ─────────────────────────────────────── */
QWidget#content_area { background: #f0f2f5; }

QLabel#page_title  { font-size: 22px; font-weight: bold; color: #1a202c; }
QLabel#section_title { font-size: 15px; font-weight: bold; color: #2d3748; }
QLabel#form_label    { font-size: 12px; color: #4a5568; font-weight: 600; }
QLabel#dlg_title     { font-size: 17px; font-weight: bold; color: #1a202c; }

/* ── Stat cards ──────────────────────────────────── */
QWidget#stat_card {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}
QLabel#stat_value {
    font-size: 28px; font-weight: bold; color: #c0392b;
}
QLabel#stat_label { font-size: 12px; color: #718096; font-weight: 500; }

/* ── Buttons ─────────────────────────────────────── */
QPushButton#action_btn {
    background:#c0392b; color:white; border:none;
    border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
}
QPushButton#action_btn:hover  { background:#922b21; }

QPushButton#secondary_btn {
    background:#2b6cb0; color:white; border:none;
    border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
}
QPushButton#secondary_btn:hover { background:#2c5282; }

QPushButton#success_btn {
    background:#276749; color:white; border:none;
    border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
}
QPushButton#success_btn:hover { background:#1e4d36; }

QPushButton#warning_btn {
    background:#d69e2e; color:white; border:none;
    border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
}
QPushButton#warning_btn:hover { background:#b7791f; }

QPushButton#danger_btn {
    background:#9b2335; color:white; border:none;
    border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
}
QPushButton#danger_btn:hover { background:#7b1d2a; }

/* ── Tables ──────────────────────────────────────── */
QTableWidget {
    background:#ffffff; border:1px solid #e2e8f0;
    border-radius:8px; gridline-color:#f0f0f0; font-size:12px;
}
QTableWidget::item          { padding:7px 10px; }
QTableWidget::item:selected { background:#fdecea; color:#922b21; }
QHeaderView::section {
    background:#2d3748; color:white; padding:9px 10px;
    border:none; font-weight:bold; font-size:12px;
}
QTableWidget { alternate-background-color: #fafafa; }

/* ── Inputs ──────────────────────────────────────── */
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    border:1.5px solid #cbd5e0; border-radius:6px;
    padding:7px 11px; background:white;
    font-size:13px; color:#2d3748;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border-color:#c0392b; }
QComboBox::drop-down { border:none; width:20px; }

/* ── Dividers / separators ───────────────────────── */
QFrame#h_sep { background:#e2e8f0; max-height:1px; }

/* ── Tab widget ──────────────────────────────────── */
QTabBar::tab {
    padding:8px 18px; font-size:13px; color:#718096;
}
QTabBar::tab:selected {
    color:#c0392b; font-weight:bold;
    border-bottom:2px solid #c0392b;
}

/* ── Scrollbar ───────────────────────────────────── */
QScrollBar:vertical {
    background:#f0f2f5; width:8px; border-radius:4px;
}
QScrollBar::handle:vertical {
    background:#cbd5e0; border-radius:4px; min-height:20px;
}
QScrollBar::handle:vertical:hover { background:#a0aec0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
"""

LOGIN_STYLE = """
QMainWindow, QWidget#bg   { background: #16213e; }
QWidget#card  { background:#ffffff; border-radius:16px; }
QLabel#brand  { color:#c0392b; font-size:40px; font-weight:900; letter-spacing:8px; }
QLabel#tagline { color:#90cdf4; font-size:14px; }
QLabel#welcome { color:#1a202c; font-size:22px; font-weight:bold; }
QLabel#form_label { color:#4a5568; font-size:12px; font-weight:600; }
QLineEdit {
    border:1.5px solid #e2e8f0; border-radius:8px;
    padding:10px 14px; font-size:14px;
    color:#2d3748; background:#f8fafc;
}
QLineEdit:focus { border-color:#c0392b; background:white; }
QPushButton#login_btn {
    background:#c0392b; color:white; border:none;
    border-radius:8px; padding:12px; font-size:15px; font-weight:bold;
}
QPushButton#login_btn:hover   { background:#922b21; }
QPushButton#login_btn:pressed { background:#7b2419; }
QLabel#footer_lbl { color:#a0aec0; font-size:11px; }
QFrame#h_sep { background:#e2e8f0; max-height:1px; }
"""
"""
views/owner_view.py
───────────────────
Owner / Director UI: Dashboard · Transaction History · Dept Overview
                     Reports · Messages
Pure UI – no DB calls, no logic.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox,
    QTextEdit, QDialog, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont, QColor

from views.styles import APP_STYLE

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except Exception:
    HAS_MPL = False


# ── Shared helpers (local copies so this file is self-contained) ──────────────
def _h_sep() -> QFrame:
    f = QFrame(); f.setObjectName("h_sep")
    f.setFrameShape(QFrame.Shape.HLine); f.setMaximumHeight(1)
    return f


def _stat_card(value: str, label: str) -> QWidget:
    w = QWidget(); w.setObjectName("stat_card"); w.setMinimumHeight(110)
    lo = QVBoxLayout(w); lo.setContentsMargins(20, 18, 20, 18); lo.setSpacing(4)
    v = QLabel(value); v.setObjectName("stat_value"); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l = QLabel(label);  l.setObjectName("stat_label"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lo.addWidget(v); lo.addWidget(l)
    return w


def _make_table(headers: list[str]) -> QTableWidget:
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setAlternatingRowColors(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def _btn(text, obj="secondary_btn"):
    b = QPushButton(text); b.setObjectName(obj)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


# ═══════════════════════════════════════════════════════════════════════════════
# OWNER MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class OwnerView(QMainWindow):

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("STASH – Owner / Director Panel")
        self.setMinimumSize(1100, 680)
        self.setStyleSheet(APP_STYLE)

        self.dashboard_page    = OwnerDashboardPage()
        self.trans_page        = OwnerTransHistoryPage()
        self.dept_page         = OwnerDeptOverviewPage()
        self.reports_page      = OwnerReportsPage()
        self.messages_page     = OwnerMessagesPage()

        self._build_ui()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        main = QHBoxLayout(root); main.setContentsMargins(0, 0, 0, 0); main.setSpacing(0)

        sb = QWidget(); sb.setObjectName("sidebar")
        sb_lo = QVBoxLayout(sb); sb_lo.setContentsMargins(12, 20, 12, 20); sb_lo.setSpacing(6)

        brand = QLabel("STASH"); brand.setObjectName("brand_lbl")
        brand.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(self.user["full_name"]); name_lbl.setObjectName("user_name")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_lbl = QLabel("Hotel Owner / Director"); role_lbl.setObjectName("user_role")
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sb_lo.addWidget(brand); sb_lo.addSpacing(8)
        sb_lo.addWidget(name_lbl); sb_lo.addWidget(role_lbl)
        sb_lo.addSpacing(10); sb_lo.addWidget(_h_sep()); sb_lo.addSpacing(10)

        nav_defs = [
            ("📊  Dashboard",         self.dashboard_page),
            ("📋  Trans. History",     self.trans_page),
            ("🏨  Dept Overview",      self.dept_page),
            ("📈  Reports",            self.reports_page),
            ("✉️   Messages",          self.messages_page),
        ]

        self.stack = QStackedWidget()
        self.nav_buttons: list[QPushButton] = []

        for label, page in nav_defs:
            self.stack.addWidget(page)
            btn = QPushButton(label); btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_buttons.append(btn)
            sb_lo.addWidget(btn)

        sb_lo.addStretch()
        self.logout_btn = _btn("Logout", "logout_btn")
        sb_lo.addWidget(self.logout_btn)

        content = QWidget(); content.setObjectName("content_area")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(self.stack)

        main.addWidget(sb); main.addWidget(content, 1)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn); btn.style().polish(btn)


# ─── Pages ────────────────────────────────────────────────────────────────────

class OwnerDashboardPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30, 30, 30, 30); lo.setSpacing(20)
        lo.addWidget(QLabel("DASHBOARD", objectName="page_title"))
        lo.addWidget(_h_sep())

        self._card_row = QHBoxLayout(); self._card_row.setSpacing(16)
        lo.addLayout(self._card_row)
        lo.addStretch()

        self._cards = []
        for val, lbl in [
            ("₱0.00","Inventory Value"),("0","Low Stock Alerts"),
            ("0","Wastages"),("0","Total Items"),
        ]:
            card = _stat_card(val, lbl)
            self._cards.append(card.findChild(QLabel, "stat_value"))
            self._card_row.addWidget(card)

    def show_stats(self, inv_value, low_stock, wastages, total_items):
        for lbl, val in zip(self._cards, [inv_value, low_stock, wastages, total_items]):
            lbl.setText(str(val))


class OwnerTransHistoryPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30, 30, 30, 30); lo.setSpacing(16)
        lo.addWidget(QLabel("TRANSACTION HISTORY", objectName="page_title"))
        lo.addWidget(_h_sep())
        self.table = _make_table(
            ["ID","Date","Supplier","Created By","Expected","Total (₱)","Status"]
        )
        lo.addWidget(self.table)

    def populate(self, rows: list[dict]):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["id"], str(row["created_at"])[:10],
                row["supplier"], row["created_by"] or "",
                str(row["expected_date"]) if row["expected_date"] else "",
                f"{float(row['total_amount']):,.2f}", row["status"],
            ]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)


class OwnerDeptOverviewPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30, 30, 30, 30); lo.setSpacing(16)
        lo.addWidget(QLabel("DEPARTMENT OVERVIEW", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout()
        self.dept_combo = QComboBox(); self.dept_combo.setMinimumWidth(180)
        top.addWidget(QLabel("Department:")); top.addWidget(self.dept_combo)
        top.addStretch()
        lo.addLayout(top)

        self._card_row = QHBoxLayout(); self._card_row.setSpacing(16)
        lo.addLayout(self._card_row)

        self.table = _make_table(
            ["Item","Category","Stock","Min Stock","Status"]
        )
        lo.addWidget(self.table)
        self._cards_vals = []

    def set_departments(self, depts: list[str]):
        self.dept_combo.blockSignals(True)
        self.dept_combo.clear()
        self.dept_combo.addItem("All Departments")
        for d in depts: self.dept_combo.addItem(d)
        self.dept_combo.blockSignals(False)

    def show_dept_stats(self, inv_value: str, total_items: str, wastages: str):
        while self._card_row.count():
            item = self._card_row.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for val, lbl in [(inv_value,"Inventory Value"),(total_items,"Inventory Items"),(wastages,"Wastages")]:
            self._card_row.addWidget(_stat_card(val, lbl))

    def populate_items(self, rows: list[dict]):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            status = "Low Stock" if row["stock_qty"] < row["min_stock"] else "OK"
            for c, val in enumerate([
                row["name"], row["category"],
                row["stock_qty"], row["min_stock"], status,
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if status == "Low Stock": cell.setBackground(QColor("#fdecea"))
                self.table.setItem(r, c, cell)


class OwnerReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30, 30, 30, 30); lo.setSpacing(16)
        lo.addWidget(QLabel("REPORTS", objectName="page_title"))
        lo.addWidget(_h_sep())

        tabs = QTabWidget()
        tabs.addTab(self._tab_stock(),    "📊 Stock Distribution")
        tabs.addTab(self._tab_movement(), "🔄 Movement Overview")
        tabs.addTab(self._tab_lowstock(), "⚠️ Low Stock")
        lo.addWidget(tabs)

    def _tab_stock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_stock     = _btn("📄 Export Inventory CSV", "secondary_btn")
        self.btn_export_stock_pdf = _btn("📑 Export PDF", "action_btn")
        er.addStretch()
        er.addWidget(self.btn_export_stock)
        er.addWidget(self.btn_export_stock_pdf)
        lo.addLayout(er)
        if HAS_MPL:
            self.fig_dist    = Figure(figsize=(8, 4), facecolor="white")
            self.canvas_dist = FigureCanvas(self.fig_dist)
            lo.addWidget(self.canvas_dist)
        else:
            lo.addWidget(QLabel("Install matplotlib to view charts."))
        return w

    def _tab_movement(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_purchase     = _btn("📄 Export Purchase CSV", "secondary_btn")
        self.btn_export_purchase_pdf = _btn("📑 Export PDF", "action_btn")
        er.addStretch()
        er.addWidget(self.btn_export_purchase)
        er.addWidget(self.btn_export_purchase_pdf)
        lo.addLayout(er)
        if HAS_MPL:
            self.fig_move    = Figure(figsize=(8, 4), facecolor="white")
            self.canvas_move = FigureCanvas(self.fig_move)
            lo.addWidget(self.canvas_move)
        else:
            lo.addWidget(QLabel("Install matplotlib to view charts."))
        return w

    def _tab_lowstock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_low     = _btn("📄 Export Low-Stock CSV", "secondary_btn")
        self.btn_export_low_pdf = _btn("📑 Export PDF", "action_btn")
        er.addStretch()
        er.addWidget(self.btn_export_low)
        er.addWidget(self.btn_export_low_pdf)
        lo.addLayout(er)
        self.low_table = _make_table(["Item","Category","Stock","Min Stock","Deficit"])
        lo.addWidget(self.low_table)
        return w

    def draw_stock_dist(self, names: list[str], qtys: list[int]):
        if not HAS_MPL: return
        self.fig_dist.clear()
        ax = self.fig_dist.add_subplot(111)
        if names:
            clrs = ["#c0392b","#2b6cb0","#276749","#d69e2e","#805ad5",
                    "#e53e3e","#3182ce","#38a169","#ecc94b","#9f7aea"]
            ax.pie(qtys, labels=[n[:12] for n in names],
                   colors=clrs[:len(names)], autopct="%1.1f%%", startangle=140)
        ax.set_title("Stock Distribution by Item", fontsize=12, fontweight="bold")
        self.fig_dist.tight_layout(); self.canvas_dist.draw()

    def draw_movement(self, labels: list[str], values: list[int]):
        if not HAS_MPL: return
        self.fig_move.clear()
        ax = self.fig_move.add_subplot(111)
        colors = ["#c0392b","#2b6cb0","#276749","#d69e2e"]
        ax.bar(labels, values, color=colors[:len(labels)])
        ax.set_title("Inventory Movement Summary", fontsize=12, fontweight="bold")
        ax.set_ylabel("Total Quantity")
        self.fig_move.tight_layout(); self.canvas_move.draw()

    def populate_low_stock(self, rows: list[dict]):
        self.low_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["name"], row["category"],
                row["stock_qty"], row["min_stock"], row["deficit"],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(QColor("#fdecea"))
                self.low_table.setItem(r, c, cell)


class OwnerMessagesPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30, 30, 30, 30); lo.setSpacing(16)
        lo.addWidget(QLabel("MESSAGES", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout()
        self.btn_compose = _btn("✉️  Compose Message", "action_btn")
        top.addWidget(self.btn_compose); top.addStretch()
        lo.addLayout(top)

        self.table = _make_table(
            ["ID","From","To","Category","Subject","Preview","Date","Status"]
        )
        lo.addWidget(self.table)

    def populate(self, rows: list[dict], current_user_name: str):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            preview = (row["body"] or "")[:50] + "…"
            unread  = (not row["is_read"]) and row["recipient"] == current_user_name
            for c, val in enumerate([
                row["id"], row["sender"], row["recipient"],
                row["category"], row["title"] or "", preview,
                str(row["created_at"])[:16],
                "✓ Read" if row["is_read"] else "● Unread",
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if unread: cell.setBackground(QColor("#ebf8ff"))
                self.table.setItem(r, c, cell)

    def get_selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())


# ── Compose dialog (shared) ───────────────────────────────────────────────────
class OwnerComposeDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compose Message")
        self.setMinimumWidth(430)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        lo = QVBoxLayout(self); lo.setContentsMargins(28, 24, 28, 24); lo.setSpacing(12)
        lo.addWidget(QLabel("Compose Message", objectName="dlg_title"))
        lo.addWidget(_h_sep())

        self.to_combo  = QComboBox()
        self.cat_combo = QComboBox()
        for c in ["General","Inventory","Purchase","Request","Report","Urgent"]:
            self.cat_combo.addItem(c)
        self.subj_inp  = QLineEdit()
        self.body_inp  = QTextEdit(); self.body_inp.setMinimumHeight(100)

        for lbl_txt, w in [("To *",self.to_combo),("Category",self.cat_combo),
                            ("Subject *",self.subj_inp),("Body *",self.body_inp)]:
            row = QVBoxLayout(); row.setSpacing(4)
            row.addWidget(QLabel(lbl_txt, objectName="form_label")); row.addWidget(w)
            lo.addLayout(row)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.setObjectName("secondary_btn")
        send   = QPushButton("Send");   send.setObjectName("action_btn")
        cancel.clicked.connect(self.reject)
        self.send_btn = send
        btns.addWidget(cancel); btns.addWidget(send)
        lo.addLayout(btns)

    def load_recipients(self, users: list[dict]):
        for u in users:
            self.to_combo.addItem(f"{u['full_name']} ({u['role'].title()})", u["id"])

    def get_data(self) -> dict:
        return {
            "recipient_id": self.to_combo.currentData(),
            "category":     self.cat_combo.currentText(),
            "title":        self.subj_inp.text().strip(),
            "body":         self.body_inp.toPlainText().strip(),
        }
"""
views/dept_view.py
──────────────────
Department Manager UI.
Includes: Dashboard · Inventory (with history + stock adjustment) ·
          Requests · Reports · Messages
Pure UI – no DB calls.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox,
    QTextEdit, QSpinBox, QDialog, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont, QColor

from views.styles import APP_STYLE

try:
    import matplotlib; matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except Exception:
    HAS_MPL = False


def _h_sep():
    f = QFrame(); f.setObjectName("h_sep")
    f.setFrameShape(QFrame.Shape.HLine); f.setMaximumHeight(1)
    return f

def _stat_card(value, label, colour="#c0392b"):
    w = QWidget(); w.setObjectName("stat_card"); w.setMinimumHeight(110)
    lo = QVBoxLayout(w); lo.setContentsMargins(20,18,20,14); lo.setSpacing(4)
    v = QLabel(value)
    v.setAlignment(Qt.AlignmentFlag.AlignCenter)
    v.setStyleSheet(f"font-size:26px; font-weight:bold; color:{colour};")
    l = QLabel(label); l.setObjectName("stat_label"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lo.addWidget(v); lo.addWidget(l)
    return w

def _make_table(headers):
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
# DEPT MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class DeptView(QMainWindow):

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        dept = user.get("department", "Department")
        self.setWindowTitle(f"STASH – {dept} Manager")
        self.setMinimumSize(1120, 700)
        self.setStyleSheet(APP_STYLE)

        self.dashboard_page = DeptDashboardPage()
        self.inventory_page = DeptInventoryPage()
        self.requests_page  = DeptRequestsPage()
        self.reports_page   = DeptReportsPage()
        self.messages_page  = DeptMessagesPage()
        self._build_ui(dept)

    def _build_ui(self, dept: str):
        root = QWidget(); self.setCentralWidget(root)
        main = QHBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        sb = QWidget(); sb.setObjectName("sidebar")
        sl = QVBoxLayout(sb); sl.setContentsMargins(12,20,12,20); sl.setSpacing(6)

        brand = QLabel("STASH"); brand.setObjectName("brand_lbl")
        brand.setFont(QFont("Segoe UI",18,QFont.Weight.Black))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(self.user["full_name"]); name_lbl.setObjectName("user_name")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_lbl = QLabel(f"{dept} Manager"); role_lbl.setObjectName("user_role")
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dept_lbl = QLabel(dept); dept_lbl.setObjectName("user_dept")
        dept_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sl.addWidget(brand); sl.addSpacing(8)
        sl.addWidget(name_lbl); sl.addWidget(role_lbl); sl.addWidget(dept_lbl)
        sl.addSpacing(10); sl.addWidget(_h_sep()); sl.addSpacing(10)

        nav_defs = [
            ("📊  Dashboard",  self.dashboard_page),
            ("📦  Inventory",  self.inventory_page),
            ("📋  Requests",   self.requests_page),
            ("📈  Reports",    self.reports_page),
            ("✉️   Messages",  self.messages_page),
        ]
        self.stack = QStackedWidget()
        self.nav_buttons: list[QPushButton] = []
        for label, page in nav_defs:
            self.stack.addWidget(page)
            btn = QPushButton(label); btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_buttons.append(btn); sl.addWidget(btn)

        sl.addStretch()
        self.logout_btn = _btn("Logout", "logout_btn")
        sl.addWidget(self.logout_btn)

        content = QWidget(); content.setObjectName("content_area")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.addWidget(self.stack)
        main.addWidget(sb); main.addWidget(content, 1)

    def switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn); btn.style().polish(btn)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
class DeptDashboardPage(QWidget):

    _CARD_DEFS = [
        ("₱0.00", "💰 Inventory Value",   "#c0392b"),
        ("0",     "📋 Pending Requests",  "#e67e22"),
        ("0",     "🗑️  Wastages",         "#8e44ad"),
        ("0",     "📦 Items in Stock",    "#2980b9"),
    ]

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(22)
        lo.addWidget(QLabel("DASHBOARD", objectName="page_title"))
        lo.addWidget(_h_sep())

        row = QHBoxLayout(); row.setSpacing(16)
        self._val_labels: list[QLabel] = []
        for val, lbl, clr in self._CARD_DEFS:
            card = _stat_card(val, lbl, clr)
            self._val_labels.append(card.findChild(QLabel))
            row.addWidget(card)
        lo.addLayout(row)
        lo.addStretch()

    def show_stats(self, inv_value, pending_req, wastages, total_items):
        for lbl, v in zip(self._val_labels, [inv_value, pending_req, wastages, total_items]):
            lbl.setText(str(v))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INVENTORY  (with +/− adjustment + history)
# ═══════════════════════════════════════════════════════════════════════════════
class DeptInventoryPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("INVENTORY", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout(); top.setSpacing(10)
        self.btn_history = _btn("📋 Movement History", "secondary_btn")
        self.btn_damage  = _btn("⚠️  Report Damage",   "danger_btn")
        for b in [self.btn_history, self.btn_damage]:
            top.addWidget(b)
        top.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search items…")
        self.search_input.setMaximumWidth(220)
        top.addWidget(self.search_input)
        lo.addLayout(top)

        notice = QLabel(
            "ℹ️  Use ➖ on each row to record consumption (stock goes down)."
        )
        notice.setStyleSheet(
            "color:#2b6cb0; background:#ebf8ff; border-radius:5px; "
            "padding:6px 12px; font-size:11px;"
        )
        notice.setWordWrap(True)
        lo.addWidget(notice)

        # Default no-op callbacks; overwritten by controller via populate()
        self._use_cb = lambda iid, nm: None

        self.table = _make_table(
            ["ID","Name","SKU","Category","Unit","Stock","Min Stock","Status","Action"]
        )
        self.table.verticalHeader().setDefaultSectionSize(36)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 80)
        lo.addWidget(self.table)

    def populate(self, rows: list[dict], use_cb=None, restock_cb=None):
        """
        use_cb(item_id, item_name) — called when ➖ is clicked.
        restock_cb is accepted but ignored (kept for API compatibility).
        Stored on first call and reused on filter refreshes (pass None to reuse).
        """
        if use_cb is not None:
            self._use_cb = use_cb

        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            status = "Low Stock" if row["stock_qty"] < row["min_stock"] else "OK"
            bg = QColor("#fdecea") if status == "Low Stock" else QColor("#f0fff4")

            for c, val in enumerate([
                row["id"], row["name"], row["sku"] or "", row["category"],
                row["unit"] or "", row["stock_qty"], row["min_stock"], status,
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(bg)
                self.table.setItem(r, c, cell)

            # ── Inline ➖ action button ────────────────────────────────────
            item_id   = row["id"]
            item_name = row["name"]

            btn_use = QPushButton("➖ Use")
            btn_use.setToolTip("Mark as used (reduce stock)")
            btn_use.setFixedSize(64, 26)
            btn_use.setStyleSheet(
                "QPushButton{background:#d69e2e;color:white;border:none;"
                "border-radius:5px;font-size:11px;font-weight:bold;}"
                "QPushButton:hover{background:#b7791f;}"
            )
            btn_use.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_use.clicked.connect(
                lambda _, iid=item_id, nm=item_name: self._use_cb(iid, nm)
            )

            cell_widget = QWidget()
            cell_lo = QHBoxLayout(cell_widget)
            cell_lo.setContentsMargins(4, 4, 4, 4)
            cell_lo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_lo.addWidget(btn_use)
            self.table.setCellWidget(r, 8, cell_widget)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())

    def get_selected_name(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self.table.item(row, 1).text()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════
class DeptRequestsPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("REQUESTS", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout(); top.setSpacing(10)
        self.btn_new    = _btn("＋ New Request",    "action_btn")
        self.btn_cancel = _btn("✖  Cancel Request", "danger_btn")
        top.addWidget(self.btn_new); top.addWidget(self.btn_cancel); top.addStretch()
        lo.addLayout(top)

        self.table = _make_table(["ID","Item","Qty","Unit","Reason","Status","Date","Notes"])
        lo.addWidget(self.table)

    def populate(self, rows: list[dict]):
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        STATUS_CLR = {"Pending": QColor("#fefcbf"), "Approved": QColor("#f0fff4"),
                      "Rejected": QColor("#fdecea"), "Cancelled": QColor("#edf2f7")}
        for r, row in enumerate(rows):
            bg = STATUS_CLR.get(row["status"], QColor("#ffffff"))
            for c, val in enumerate([
                row["id"], row["item_name"], row["quantity"],
                row["unit"] or "", row["reason"] or "",
                row["status"], str(row["created_at"])[:10], row["notes"] or "",
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(bg); self.table.setItem(r, c, cell)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())

    def get_selected_status(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self.table.item(row, 5).text()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
class DeptReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("REPORTS", objectName="page_title"))
        lo.addWidget(_h_sep())

        tabs = QTabWidget()
        tabs.addTab(self._tab_stock(),       "📊 Stock Levels")
        tabs.addTab(self._tab_consumption(), "📉 Consumption")
        tabs.addTab(self._tab_lowstock(),    "⚠️  Low Stock")
        lo.addWidget(tabs)

    def _tab_stock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_stock = _btn("📄 Export CSV", "secondary_btn")
        er.addStretch(); er.addWidget(self.btn_export_stock); lo.addLayout(er)
        if HAS_MPL:
            self.fig_stock    = Figure(figsize=(8,4), facecolor="white")
            self.canvas_stock = FigureCanvas(self.fig_stock)
            lo.addWidget(self.canvas_stock)
        else:
            lo.addWidget(QLabel("pip install matplotlib to view charts."))
        return w

    def _tab_consumption(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_con = _btn("📄 Export CSV", "secondary_btn")
        er.addStretch(); er.addWidget(self.btn_export_con); lo.addLayout(er)
        if HAS_MPL:
            self.fig_con    = Figure(figsize=(8,4), facecolor="white")
            self.canvas_con = FigureCanvas(self.fig_con)
            lo.addWidget(self.canvas_con)
        else:
            lo.addWidget(QLabel("pip install matplotlib to view charts."))
        return w

    def _tab_lowstock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        er = QHBoxLayout()
        self.btn_export_low = _btn("📄 Export CSV", "secondary_btn")
        er.addStretch(); er.addWidget(self.btn_export_low); lo.addLayout(er)
        self.low_table = _make_table(["Item","Category","Stock","Min Stock","Deficit"])
        lo.addWidget(self.low_table)
        return w

    def draw_stock_chart(self, names, qtys, min_stocks):
        if not HAS_MPL: return
        self.fig_stock.clear()
        ax = self.fig_stock.add_subplot(111)
        colors = ["#c0392b" if q < m else "#2b6cb0" for q, m in zip(qtys, min_stocks)]
        ax.bar([n[:16] for n in names], qtys, color=colors)
        ax.set_title("Department Stock Levels", fontsize=12, fontweight="bold")
        ax.set_ylabel("Quantity"); ax.tick_params(axis="x", rotation=30, labelsize=8)
        self.fig_stock.tight_layout(); self.canvas_stock.draw()

    def draw_consumption_chart(self, names, totals):
        if not HAS_MPL: return
        self.fig_con.clear()
        ax = self.fig_con.add_subplot(111)
        if names:
            clrs = ["#c0392b","#2b6cb0","#276749","#d69e2e","#805ad5"]
            ax.barh([n[:20] for n in names], totals,
                    color=[clrs[i % len(clrs)] for i in range(len(names))])
        ax.set_title("Item Consumption (marked as used)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Total Quantity Used")
        self.fig_con.tight_layout(); self.canvas_con.draw()

    def populate_low_stock(self, rows):
        self.low_table.setRowCount(0); self.low_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["name"], row["category"],
                row["stock_qty"], row["min_stock"], row["deficit"],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(QColor("#fdecea")); self.low_table.setItem(r, c, cell)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════
class DeptMessagesPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
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
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
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

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())


# ═══════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ═══════════════════════════════════════════════════════════════════════════════
class _BaseDlg(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title); self.setMinimumWidth(420)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        self._lo = QVBoxLayout(self)
        self._lo.setContentsMargins(28,24,28,24); self._lo.setSpacing(12)
        lbl = QLabel(title); lbl.setObjectName("dlg_title"); self._lo.addWidget(lbl)
        self._lo.addWidget(_h_sep())

    def _field(self, lbl_text, widget):
        sub = QVBoxLayout(); sub.setSpacing(4)
        sub.addWidget(QLabel(lbl_text, objectName="form_label")); sub.addWidget(widget)
        self._lo.addLayout(sub); return widget

    def _ok_cancel(self, ok_text="Save"):
        row = QHBoxLayout(); row.addStretch()
        self.cancel_btn = QPushButton("Cancel"); self.cancel_btn.setObjectName("secondary_btn")
        self.ok_btn     = QPushButton(ok_text);  self.ok_btn.setObjectName("action_btn")
        self.cancel_btn.clicked.connect(self.reject)
        row.addWidget(self.cancel_btn); row.addWidget(self.ok_btn)
        self._lo.addLayout(row)


class NewRequestDialog(_BaseDlg):
    """
    New inventory request dialog.
    Uses blockSignals + setSizeAdjustPolicy + fixed heights to prevent the
    Windows PyQt6 recursive-repaint stack overflow (exit code 0xC0000409).
    """

    _UNITS = ["pcs", "kg", "g", "L", "mL", "box", "pack", "set",
              "roll", "pair", "bottle", "bag", "sheet", "tube", "pad"]
    _NEW_ITEM_SENTINEL = "── Type new item name below ──"

    def __init__(self, parent=None):
        super().__init__("New Inventory Request", parent)
        # Fix dialog width so layout never recalculates during combo population
        self.setFixedWidth(460)

        # Item selection combo
        lbl_item = QLabel("Item *", objectName="form_label")
        self._item_combo = QComboBox()
        self._item_combo.setEditable(False)
        # CRITICAL: prevent combo from resizing the dialog when items are added
        self._item_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._item_combo.setFixedHeight(34)
        self._item_combo.addItem("Loading items…")  # placeholder
        self._lo.addWidget(lbl_item)
        self._lo.addWidget(self._item_combo)

        # New item name field
        lbl_new = QLabel("New item name (fill only if requesting a new item)",
                         objectName="form_label")
        lbl_new.setStyleSheet("color:#2b6cb0; font-size:11px;")
        self._new_item_inp = QLineEdit()
        self._new_item_inp.setPlaceholderText(
            "Leave blank to use selected item above…"
        )
        self._new_item_inp.setFixedHeight(34)
        self._lo.addWidget(lbl_new)
        self._lo.addWidget(self._new_item_inp)

        # Quantity
        lbl_qty = QLabel("Quantity *", objectName="form_label")
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(9999)
        self.qty_spin.setFixedHeight(34)
        self._lo.addWidget(lbl_qty)
        self._lo.addWidget(self.qty_spin)

        # Unit dropdown
        lbl_unit = QLabel("Unit *", objectName="form_label")
        self.unit_combo = QComboBox()
        self.unit_combo.setEditable(False)
        self.unit_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.unit_combo.setFixedHeight(34)
        for u in self._UNITS:
            self.unit_combo.addItem(u)
        self._lo.addWidget(lbl_unit)
        self._lo.addWidget(self.unit_combo)

        # Reason — setFixedHeight prevents layout thrashing on Windows
        lbl_reason = QLabel("Reason", objectName="form_label")
        self.reason_inp = QTextEdit()
        self.reason_inp.setFixedHeight(72)
        self.reason_inp.setPlaceholderText("Why do you need this item?")
        self._lo.addWidget(lbl_reason)
        self._lo.addWidget(self.reason_inp)

        self._ok_cancel("Submit Request")

    def load_items(self, items: list[dict]):
        # blockSignals prevents recursive layout events during population
        self._item_combo.blockSignals(True)
        self._item_combo.clear()
        for it in items:
            self._item_combo.addItem(it["name"], it["id"])
        self._item_combo.addItem(self._NEW_ITEM_SENTINEL, None)
        self._item_combo.blockSignals(False)

    def get_data(self) -> dict:
        new_name = self._new_item_inp.text().strip()
        selected_text = self._item_combo.currentText()
        is_sentinel = (selected_text == self._NEW_ITEM_SENTINEL)

        if new_name:
            # User typed a new name → treat as new item regardless of combo
            item_name = new_name
            item_id   = None
            is_new    = True
        elif is_sentinel:
            item_name = ""   # will fail validation in controller
            item_id   = None
            is_new    = True
        else:
            item_name = selected_text
            item_id   = self._item_combo.currentData()
            is_new    = False

        return {
            "item_name": item_name,
            "item_id":   item_id,
            "is_new":    is_new,
            "quantity":  self.qty_spin.value(),
            "unit":      self.unit_combo.currentText(),
            "reason":    self.reason_inp.toPlainText().strip(),
        }


class StockAdjustDialog(_BaseDlg):
    """Used for both Mark Used (−) and Restock (+)."""

    def __init__(self, item_name: str, action: str, parent=None):
        # action = "use" or "restock"
        title = f"{'Mark Used' if action == 'use' else 'Restock'}: {item_name}"
        super().__init__(title, parent)
        self.action = action

        self.qty_spin  = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999)
        self.notes_inp = QLineEdit()
        self.notes_inp.setPlaceholderText(
            "e.g. used for Room 201" if action == "use" else "e.g. received from admin"
        )
        self._field("Quantity", self.qty_spin)
        self._field("Notes (optional)", self.notes_inp)
        self._ok_cancel("Confirm")

    def get_data(self):
        return {
            "quantity": self.qty_spin.value(),
            "notes":    self.notes_inp.text().strip(),
        }


class DeptDamageReportDialog(_BaseDlg):
    """Department reports damage on items they received into inventory."""

    def __init__(self, parent=None):
        super().__init__("Report Damaged Item", parent)

        self.item_combo  = QComboBox()
        self.qty_spin    = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999)
        self.reason_inp  = QTextEdit(); self.reason_inp.setMaximumHeight(80)
        self.reason_inp.setPlaceholderText("Describe the damage or defect…")

        self._field("Damaged Item *",      self.item_combo)
        self._field("Quantity Damaged",    self.qty_spin)
        self._field("Description *",       self.reason_inp)

        info = QLabel(
            "ℹ️  This report will be recorded in the system and visible to the admin."
        )
        info.setStyleSheet("color:#2b6cb0; font-size:11px;"); info.setWordWrap(True)
        self._lo.addWidget(info)
        self._ok_cancel("Submit Report")

    def load_items(self, items: list[dict]):
        for it in items:
            self.item_combo.addItem(it["name"], it["id"])

    def get_data(self):
        return {
            "item_id":   self.item_combo.currentData(),
            "item_name": self.item_combo.currentText(),
            "quantity":  self.qty_spin.value(),
            "reason":    self.reason_inp.toPlainText().strip(),
        }


class InventoryHistoryDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Movement History")
        self.setMinimumSize(820, 420)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        lo = QVBoxLayout(self); lo.setContentsMargins(20,20,20,20); lo.setSpacing(12)

        top = QHBoxLayout()
        self.btn_export = _btn("📄 Export CSV", "secondary_btn")
        top.addStretch(); top.addWidget(self.btn_export); lo.addLayout(top)

        self.table = _make_table(
            ["ID","Item","Movement","Qty","User","Notes","Date"]
        )
        self.table.setMinimumHeight(300); lo.addWidget(self.table)
        self._rows: list[dict] = []

        close_btn = _btn("Close","secondary_btn"); close_btn.clicked.connect(self.accept)
        lo.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def populate(self, rows: list[dict]):
        self._rows = rows
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["id"], row["item_name"], row["movement_type"],
                row["quantity"], row["user_name"],
                row["notes"] or "", str(row["created_at"])[:16],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, cell)


class DeptComposeDialog(_BaseDlg):

    def __init__(self, parent=None):
        super().__init__("Compose Message", parent)
        self.to_combo  = QComboBox()
        self.cat_combo = QComboBox()
        for c in ["General","Inventory","Request","Report","Urgent"]:
            self.cat_combo.addItem(c)
        self.subj_inp = QLineEdit()
        self.body_inp = QTextEdit(); self.body_inp.setMinimumHeight(100)
        self._field("To *",       self.to_combo)
        self._field("Category",   self.cat_combo)
        self._field("Subject *",  self.subj_inp)
        self._field("Body *",     self.body_inp)
        self._ok_cancel("Send Message")
        self.send_btn = self.ok_btn   # alias

    def load_recipients(self, users: list[dict]):
        for u in users:
            self.to_combo.addItem(f"{u['full_name']} ({u['role'].title()})", u["id"])

    def get_data(self):
        return {
            "recipient_id": self.to_combo.currentData(),
            "category":     self.cat_combo.currentText(),
            "title":        self.subj_inp.text().strip(),
            "body":         self.body_inp.toPlainText().strip(),
        }
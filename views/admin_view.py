"""
views/admin_view.py
───────────────────
Admin UI — all pages and dialogs.
Changes from v1:
  • Purchase table correctly clears approve button after approval
  • Suppliers dialog has Delete button
  • Damage dialog simplified (purchase-based reporting to supplier)
  • ItemDialog: only name / unit / cost / min-stock / category
    SKU is auto-generated (shown read-only); no manual stock entry
  • Edit item button removed — items are immutable after creation
  • User dialog: hashlib hint removed
  • Dashboard shows 6 enriched KPI cards
  • Reports pages have Export CSV buttons
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox,
    QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QDialog,
    QTabWidget, QGridLayout,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui  import QFont, QColor

from views.styles import APP_STYLE

try:
    import matplotlib; matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except Exception:
    HAS_MPL = False


# ── Shared helpers ────────────────────────────────────────────────────────────
def _h_sep():
    f = QFrame(); f.setObjectName("h_sep")
    f.setFrameShape(QFrame.Shape.HLine); f.setMaximumHeight(1)
    return f

def _btn(text, obj="secondary_btn"):
    b = QPushButton(text); b.setObjectName(obj)
    b.setCursor(Qt.CursorShape.PointingHandCursor); return b

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


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class AdminView(QMainWindow):

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("STASH – Admin Panel")
        self.setMinimumSize(1160, 720)
        self.setStyleSheet(APP_STYLE)

        self.dashboard_page  = AdminDashboardPage()
        self.purchase_page   = AdminPurchasePage()
        self.inventory_page  = AdminInventoryPage()
        self.requests_page   = AdminRequestsPage()
        self.reports_page    = AdminReportsPage()
        self.messages_page   = AdminMessagesPage()
        self.user_mgmt_page  = AdminUserManagementPage()
        self._build_ui()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        main = QHBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        sb = QWidget(); sb.setObjectName("sidebar")
        sl = QVBoxLayout(sb); sl.setContentsMargins(12,20,12,20); sl.setSpacing(6)

        brand = QLabel("STASH"); brand.setObjectName("brand_lbl")
        brand.setFont(QFont("Segoe UI",18,QFont.Weight.Black))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(self.user["full_name"]); name_lbl.setObjectName("user_name")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_lbl = QLabel("Purchase Admin"); role_lbl.setObjectName("user_role")
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sl.addWidget(brand); sl.addSpacing(8)
        sl.addWidget(name_lbl); sl.addWidget(role_lbl)
        sl.addSpacing(10); sl.addWidget(_h_sep()); sl.addSpacing(10)

        pages = [
            ("📊  Dashboard",       self.dashboard_page),
            ("🛒  Purchase",         self.purchase_page),
            ("📦  Inventory",        self.inventory_page),
            ("📋  Requests",         self.requests_page),
            ("📈  Reports",          self.reports_page),
            ("✉️   Messages",        self.messages_page),
            ("👥  User Management",  self.user_mgmt_page),
        ]
        self.stack = QStackedWidget()
        self.nav_buttons: list[QPushButton] = []
        for label, page in pages:
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
# PAGE: DASHBOARD  (6 enriched KPI cards)
# ═══════════════════════════════════════════════════════════════════════════════
class AdminDashboardPage(QWidget):

    _CARD_DEFS = [
        ("₱0.00",  "💰 Inventory Value",      "#c0392b"),
        ("0",      "⚠️  Low Stock Alerts",     "#e67e22"),
        ("0",      "🗑️  Wastages Reported",    "#8e44ad"),
        ("0",      "📦 Total Items",           "#2980b9"),
        ("—",      "✅ Stock Health",          "#27ae60"),
        ("0",      "📋 Pending Requests",      "#16a085"),
    ]

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(22)
        lo.addWidget(QLabel("DASHBOARD", objectName="page_title"))
        lo.addWidget(_h_sep())

        grid = QGridLayout(); grid.setSpacing(16)
        self._value_labels: list[QLabel] = []

        for i, (val, lbl, colour) in enumerate(self._CARD_DEFS):
            card = QWidget(); card.setObjectName("stat_card")
            card.setMinimumHeight(110)
            cl = QVBoxLayout(card); cl.setContentsMargins(20,18,20,14); cl.setSpacing(4)

            v = QLabel(val)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.setStyleSheet(f"font-size:26px; font-weight:bold; color:{colour};")
            l = QLabel(lbl)
            l.setObjectName("stat_label"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(v); cl.addWidget(l)
            self._value_labels.append(v)
            grid.addWidget(card, i // 3, i % 3)

        lo.addLayout(grid)
        lo.addStretch()

    def show_stats(self, inv_value, low_stock, wastages,
                   total_items, stock_health, pending_req):
        vals = [inv_value, low_stock, wastages, total_items, stock_health, pending_req]
        for lbl, v in zip(self._value_labels, vals):
            lbl.setText(str(v))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PURCHASE
# ═══════════════════════════════════════════════════════════════════════════════
class AdminPurchasePage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("PURCHASE", objectName="page_title"))
        lo.addWidget(_h_sep())

        row = QHBoxLayout(); row.setSpacing(10)
        self.btn_order    = _btn("＋ Order Stocks",    "action_btn")
        self.btn_supplier = _btn("🏭 Suppliers",        "secondary_btn")
        self.btn_refresh  = _btn("🔄 Refresh",          "secondary_btn")
        self.btn_damage   = _btn("⚠️  Report Damage",   "warning_btn")
        for b in [self.btn_order, self.btn_supplier, self.btn_refresh, self.btn_damage]:
            row.addWidget(b)
        row.addStretch()
        lo.addLayout(row)

        lo.addWidget(QLabel("Purchase Transaction History", objectName="section_title"))
        self.table = _make_table(
            ["ID","Date","Supplier","Created By","Expected","Items","Total (₱)","Status","Action"]
        )
        lo.addWidget(self.table)

    def populate_table(self, rows: list[dict], approve_callback):
        # ── Clear ALL existing rows including cell widgets ─────────────────
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            cells = [
                str(row["id"]),
                str(row["created_at"])[:10],
                row["supplier"],
                row["created_by"] or "",
                str(row["expected_date"]) if row["expected_date"] else "",
                str(row["item_count"]),
                f"{float(row['total_amount']):,.2f}",
                row["status"].title(),
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # colour row by status
                if row["status"] == "approved":
                    item.setBackground(QColor("#f0fff4"))
                elif row["status"] == "rejected":
                    item.setBackground(QColor("#fdecea"))
                self.table.setItem(r, c, item)

            # Action column — only pending rows get a Deliver button
            if row["status"] == "pending":
                pid = row["id"]
                deliver_btn = QPushButton("Deliver")
                deliver_btn.setStyleSheet(
                    "background:#276749;color:white;border-radius:4px;"
                    "padding:3px 10px;font-size:11px;font-weight:bold;"
                )
                deliver_btn.clicked.connect(lambda _, p=pid: approve_callback(p))
                self.table.setCellWidget(r, 8, deliver_btn)
            else:
                self.table.removeCellWidget(r, 8)
                status_lbl = QLabel(row["status"].title())
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                colour = "#276749" if row["status"] == "delivered" else "#c0392b"
                status_lbl.setStyleSheet(f"color:{colour}; font-weight:bold; font-size:11px;")
                self.table.setCellWidget(r, 8, status_lbl)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INVENTORY
# ═══════════════════════════════════════════════════════════════════════════════
class AdminInventoryPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("INVENTORY", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout(); top.setSpacing(10)
        self.btn_add     = _btn("＋ Add Item",    "action_btn")
        self.btn_delete  = _btn("🗑️  Delete Item", "danger_btn")
        self.btn_history = _btn("📋 History",      "secondary_btn")
        for b in [self.btn_add, self.btn_delete, self.btn_history]:
            top.addWidget(b)
        top.addStretch()

        notice = QLabel("ℹ️  Stock levels are managed through approved Purchase Orders only.")
        notice.setStyleSheet(
            "color:#2b6cb0; background:#ebf8ff; border-radius:5px;"
            "padding:6px 12px; font-size:11px;"
        )
        top.addWidget(notice)
        lo.addLayout(top)

        filter_row = QHBoxLayout(); filter_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search items…")
        self.search_input.setMaximumWidth(220)
        self.cat_combo = QComboBox(); self.cat_combo.addItem("All Categories")
        self.cat_combo.setMinimumWidth(160)
        filter_row.addWidget(self.search_input); filter_row.addWidget(self.cat_combo)
        filter_row.addStretch()
        lo.addLayout(filter_row)

        self.table = _make_table(
            ["ID","Name","SKU","Category","Unit","Unit Cost (₱)","Stock","Min Stock","Status"]
        )
        lo.addWidget(self.table)

    def populate_table(self, rows):
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            status = "Low Stock" if row["stock_qty"] < row["min_stock"] else "OK"
            bg = QColor("#fdecea") if status == "Low Stock" else QColor("#f0fff4")
            for c, val in enumerate([
                row["id"], row["name"], row["sku"] or "", row["category"],
                row["unit"] or "", f"{float(row['unit_cost']):,.2f}",
                row["stock_qty"], row["min_stock"], status,
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(bg); self.table.setItem(r, c, cell)

    def set_categories(self, cats):
        self.cat_combo.blockSignals(True); self.cat_combo.clear()
        self.cat_combo.addItem("All Categories")
        for c in cats: self.cat_combo.addItem(c)
        self.cat_combo.blockSignals(False)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())

    def get_search_text(self): return self.search_input.text().lower()
    def get_selected_category(self): return self.cat_combo.currentText()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS  (with Export CSV buttons)
# ═══════════════════════════════════════════════════════════════════════════════
class AdminReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("REPORTS", objectName="page_title"))
        lo.addWidget(_h_sep())

        tabs = QTabWidget()
        tabs.addTab(self._tab_stock(),    "📊 Stock Levels")
        tabs.addTab(self._tab_movement(), "🔄 Movement")
        tabs.addTab(self._tab_lowstock(), "⚠️ Low Stock")
        tabs.addTab(self._tab_damage(),   "🗑️ Damage Log")
        lo.addWidget(tabs)

    def _tab_stock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        export_row = QHBoxLayout()
        self.btn_export_inv = _btn("📄 Export Inventory CSV", "secondary_btn")
        export_row.addStretch(); export_row.addWidget(self.btn_export_inv)
        lo.addLayout(export_row)
        if HAS_MPL:
            self.fig_stock    = Figure(figsize=(8,4), facecolor="white")
            self.canvas_stock = FigureCanvas(self.fig_stock)
            lo.addWidget(self.canvas_stock)
        else:
            lo.addWidget(QLabel("pip install matplotlib to view charts."))
        return w

    def _tab_movement(self):
        w = QWidget(); lo = QVBoxLayout(w)
        export_row = QHBoxLayout()
        self.btn_export_move = _btn("📄 Export Movement CSV", "secondary_btn")
        export_row.addStretch(); export_row.addWidget(self.btn_export_move)
        lo.addLayout(export_row)
        if HAS_MPL:
            self.fig_move    = Figure(figsize=(8,4), facecolor="white")
            self.canvas_move = FigureCanvas(self.fig_move)
            lo.addWidget(self.canvas_move)
        else:
            lo.addWidget(QLabel("pip install matplotlib to view charts."))
        return w

    def _tab_lowstock(self):
        w = QWidget(); lo = QVBoxLayout(w)
        export_row = QHBoxLayout()
        self.btn_export_low = _btn("📄 Export Low-Stock CSV", "secondary_btn")
        export_row.addStretch(); export_row.addWidget(self.btn_export_low)
        lo.addLayout(export_row)
        self.low_table = _make_table(["Item","Category","Stock","Min Stock","Deficit"])
        lo.addWidget(self.low_table)
        return w

    def _tab_damage(self):
        w = QWidget(); lo = QVBoxLayout(w)
        export_row = QHBoxLayout()
        self.btn_export_dmg = _btn("📄 Export Damage CSV", "secondary_btn")
        export_row.addStretch(); export_row.addWidget(self.btn_export_dmg)
        lo.addLayout(export_row)
        self.dmg_table = _make_table(
            ["ID","Item","Category","Qty","Reason","Reported By","Status","Date"]
        )
        lo.addWidget(self.dmg_table)
        return w

    # ── Setters ───────────────────────────────────────────────────────────────
    def draw_stock_chart(self, names, qtys, min_stocks):
        if not HAS_MPL: return
        self.fig_stock.clear()
        ax = self.fig_stock.add_subplot(111)
        colors = ["#c0392b" if q < m else "#2b6cb0" for q, m in zip(qtys, min_stocks)]
        ax.bar([n[:14] for n in names], qtys, color=colors)
        ax.set_title("Stock Levels – All Items", fontsize=12, fontweight="bold")
        ax.set_ylabel("Quantity"); ax.tick_params(axis="x", rotation=30, labelsize=8)
        self.fig_stock.tight_layout(); self.canvas_stock.draw()

    def draw_movement_chart(self, labels, values):
        if not HAS_MPL: return
        self.fig_move.clear()
        ax = self.fig_move.add_subplot(111)
        if labels:
            clrs = ["#c0392b","#2b6cb0","#276749","#d69e2e","#805ad5"]
            ax.pie(values, labels=labels, colors=clrs[:len(labels)],
                   autopct="%1.1f%%", startangle=140)
        ax.set_title("Inventory Movement Distribution", fontsize=12, fontweight="bold")
        self.fig_move.tight_layout(); self.canvas_move.draw()

    def populate_low_stock(self, rows):
        self.low_table.setRowCount(0); self.low_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([row["name"],row["category"],
                                     row["stock_qty"],row["min_stock"],row["deficit"]]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(QColor("#fdecea")); self.low_table.setItem(r, c, cell)

    def populate_damage_log(self, rows):
        self.dmg_table.setRowCount(0); self.dmg_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["id"], row.get("item_name",""), row.get("category",""),
                row["quantity"], row.get("reason",""), row.get("created_by",""),
                row["status"], str(row["created_at"])[:16],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.dmg_table.setItem(r, c, cell)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MESSAGES
# ═══════════════════════════════════════════════════════════════════════════════
class AdminMessagesPage(QWidget):

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

    def populate_table(self, rows, current_user_name):
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            preview = (row["body"] or "")[:50] + "…"
            unread  = (not row["is_read"]) and row["recipient"] == current_user_name
            for c, val in enumerate([
                row["id"], row["sender"], row["recipient"], row["category"],
                row["title"] or "", preview, str(row["created_at"])[:16],
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
# PAGE: USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
class AdminUserManagementPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("USER MANAGEMENT", objectName="page_title"))
        lo.addWidget(_h_sep())

        top = QHBoxLayout(); top.setSpacing(10)
        self.btn_add    = _btn("＋ Add User",     "action_btn")
        self.btn_edit   = _btn("✏️  Edit User",    "secondary_btn")
        self.btn_delete = _btn("🗑️  Delete User",  "danger_btn")
        self.btn_reset  = _btn("🔑 Reset Password","warning_btn")
        for b in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_reset]:
            top.addWidget(b)
        top.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search users…")
        self.search_input.setMaximumWidth(220)
        top.addWidget(self.search_input)
        lo.addLayout(top)

        self.table = _make_table(
            ["ID","Full Name","Email","Role","Department","Created At"]
        )
        lo.addWidget(self.table)

    def populate_table(self, rows):
        CLR = {"admin": QColor("#ebf8ff"), "owner": QColor("#fefcbf"),
               "department": QColor("#f0fff4")}
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            bg = CLR.get(row["role"], QColor("#ffffff"))
            for c, val in enumerate([
                row["id"], row["full_name"], row["email"],
                row["role"].title(), row["department"] or "—",
                str(row["created_at"])[:10],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(bg); self.table.setItem(r, c, cell)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())

    def get_search_text(self): return self.search_input.text().lower()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REQUESTS  (admin view — approve / decline department requests)
# ═══════════════════════════════════════════════════════════════════════════════
class AdminRequestsPage(QWidget):

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(self); lo.setContentsMargins(30,30,30,30); lo.setSpacing(16)
        lo.addWidget(QLabel("DEPARTMENT REQUESTS", objectName="page_title"))
        lo.addWidget(_h_sep())

        filter_row = QHBoxLayout(); filter_row.setSpacing(10)
        self.status_combo = QComboBox()
        for s in ["All","Pending","Approved","Completed","Rejected","Cancelled"]:
            self.status_combo.addItem(s)
        self.status_combo.setMinimumWidth(140)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search item or department…")
        self.search_input.setMaximumWidth(240)
        filter_row.addWidget(QLabel("Filter:", objectName="form_label"))
        filter_row.addWidget(self.status_combo)
        filter_row.addWidget(self.search_input)
        filter_row.addStretch()
        lo.addLayout(filter_row)

        self.table = _make_table(
            ["ID","Department","Requested By","Item","Qty","Unit",
             "New Item?","Status","Date","Notes"]
        )
        self.table.setMinimumHeight(350)
        lo.addWidget(self.table)

        hint = QLabel("Double-click a request to view details and approve / decline.")
        hint.setStyleSheet("color:#718096; font-size:11px;")
        lo.addWidget(hint)

    def populate(self, rows: list[dict]):
        STATUS_CLR = {
            "Pending":   QColor("#fefcbf"),
            "Approved":  QColor("#c6f6d5"),
            "Completed": QColor("#f0fff4"),
            "Rejected":  QColor("#fdecea"),
            "Cancelled": QColor("#edf2f7"),
        }
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            bg = STATUS_CLR.get(row["status"], QColor("#ffffff"))
            is_new = "⚠️ Yes" if row.get("is_new_item") else "No"
            for c, val in enumerate([
                row["id"], row["department"], row["requested_by"],
                row["item_name"], row["quantity"], row["unit"] or "",
                is_new, row["status"],
                str(row["created_at"])[:10], row["notes"] or "",
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(bg)
                self.table.setItem(r, c, cell)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())


# ── Request Detail Dialog ──────────────────────────────────────────────────────
class RequestDetailDialog(QDialog):
    """Shows full request info; Approve / Decline buttons at the bottom."""

    def __init__(self, req: dict, parent=None):
        super().__init__(parent)
        self.req = req
        self.setWindowTitle(f"Request #{req['id']} – {req['item_name']}")
        self.setMinimumWidth(480)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")

        lo = QVBoxLayout(self); lo.setContentsMargins(28,24,28,24); lo.setSpacing(12)

        title_lbl = QLabel(f"Request #{req['id']}")
        title_lbl.setObjectName("dlg_title"); lo.addWidget(title_lbl)
        lo.addWidget(_h_sep())

        is_new = bool(req.get("is_new_item"))
        if is_new:
            warn = QLabel("⚠️  This is a NEW item not currently in the inventory list.")
            warn.setStyleSheet(
                "background:#fefcbf;color:#b7791f;border-radius:5px;"
                "padding:8px 12px;font-size:12px;font-weight:bold;"
            )
            warn.setWordWrap(True); lo.addWidget(warn)

        def _row(label, value):
            h = QHBoxLayout()
            lbl = QLabel(label); lbl.setObjectName("form_label"); lbl.setFixedWidth(120)
            val = QLabel(str(value)); val.setWordWrap(True)
            val.setStyleSheet("color:#1a202c;font-size:13px;")
            h.addWidget(lbl); h.addWidget(val, 1); lo.addLayout(h)

        _row("Department:",    req["department"])
        _row("Requested By:",  req["requested_by"])
        _row("Item:",          req["item_name"])
        _row("Quantity:",      f"{req['quantity']} {req.get('unit') or ''}")
        _row("Reason:",        req.get("reason") or "—")
        _row("Status:",        req["status"])
        _row("Submitted:",     str(req["created_at"])[:16])
        if req.get("notes"):
            _row("Notes:", req["notes"])

        lo.addWidget(_h_sep())

        btn_row = QHBoxLayout(); btn_row.addStretch()

        self.btn_close   = _btn("Close",   "secondary_btn")
        self.btn_decline = _btn("✖  Decline", "danger_btn")
        self.btn_approve = _btn("✔  Approve", "success_btn")

        self.btn_close.clicked.connect(self.reject)

        for b in [self.btn_close, self.btn_decline, self.btn_approve]:
            btn_row.addWidget(b)

        # Hide action buttons if request is no longer pending
        if req["status"] != "Pending":
            self.btn_approve.setVisible(False)
            self.btn_decline.setVisible(False)

        lo.addLayout(btn_row)


# ═══════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ═══════════════════════════════════════════════════════════════════════════════
class _Base(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title); self.setMinimumWidth(430)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        self._lo = QVBoxLayout(self)
        self._lo.setContentsMargins(28,24,28,24); self._lo.setSpacing(12)
        lbl = QLabel(title); lbl.setObjectName("dlg_title"); self._lo.addWidget(lbl)
        self._lo.addWidget(_h_sep())

    def _field(self, label, widget):
        sub = QVBoxLayout(); sub.setSpacing(4)
        sub.addWidget(QLabel(label, objectName="form_label")); sub.addWidget(widget)
        self._lo.addLayout(sub); return widget

    def _ok_cancel(self, ok_text="Save"):
        row = QHBoxLayout(); row.addStretch()
        self.cancel_btn = _btn("Cancel","secondary_btn")
        self.ok_btn     = _btn(ok_text,"action_btn")
        self.cancel_btn.clicked.connect(self.reject)
        row.addWidget(self.cancel_btn); row.addWidget(self.ok_btn)
        self._lo.addLayout(row)


# ── Add Item Dialog (no stock input, auto-SKU) ────────────────────────────────
class ItemDialog(_Base):
    CATS = ["General","Housekeeping","Dining","Maintenance","Laundry","Front Office","Security"]

    def __init__(self, parent=None):
        super().__init__("Add New Item", parent)

        self.name_inp = QLineEdit()
        self.unit_combo = QComboBox()
        for u in ["pcs", "kg", "g", "L", "mL", "box", "pack", "set",
                  "roll", "pair", "bottle", "bag", "sheet", "tube", "pad"]:
            self.unit_combo.addItem(u)
        self.unit_combo.setEditable(False)
        self.cost_inp = QDoubleSpinBox()
        self.cost_inp.setMinimum(0.01)
        self.cost_inp.setMaximum(999999)
        self.cost_inp.setDecimals(2)
        self.cost_inp.setValue(1.00)
        self.min_inp  = QSpinBox(); self.min_inp.setMaximum(9999); self.min_inp.setValue(10)
        self.cat_inp  = QComboBox()
        for c in self.CATS: self.cat_inp.addItem(c)
        self.cat_inp.setEditable(True)

        # SKU preview label (read-only, auto-generated)
        self.sku_preview = QLabel("—")
        self.sku_preview.setStyleSheet(
            "background:#f0fff4; color:#276749; border-radius:5px;"
            "padding:6px 10px; font-weight:bold; font-size:13px;"
        )
        self.cat_inp.currentTextChanged.connect(self._update_sku_preview)

        self._field("Item Name *",        self.name_inp)
        self._field("Unit (pcs, kg, L…)", self.unit_combo)
        self._field("Unit Cost (₱)",      self.cost_inp)
        self._field("Min Stock Alert",     self.min_inp)
        self._field("Category *",          self.cat_inp)

        sku_lbl_row = QVBoxLayout(); sku_lbl_row.setSpacing(4)
        sku_lbl_row.addWidget(QLabel("Auto-Generated SKU", objectName="form_label"))
        sku_lbl_row.addWidget(self.sku_preview)
        self._lo.addLayout(sku_lbl_row)

        info = QLabel("ℹ️ Initial stock is 0. Add stock via Purchase Orders.")
        info.setStyleSheet("color:#2b6cb0; font-size:11px;")
        info.setWordWrap(True)
        self._lo.addWidget(info)

        self._ok_cancel("Add Item")
        self._update_sku_preview()

    def _update_sku_preview(self):
        """Ask controller to preview the SKU; controller may call set_sku_preview()."""
        self.sku_preview.setText("(will be generated on save)")

    def set_sku_preview(self, sku: str):
        self.sku_preview.setText(sku)

    def get_data(self) -> dict:
        return {
            "name":      self.name_inp.text().strip(),
            "unit":      self.unit_combo.currentText().strip(),
            "unit_cost": self.cost_inp.value(),
            "min_stock": self.min_inp.value(),
            "category":  self.cat_inp.currentText(),
        }


# ── Order Stocks Dialog ───────────────────────────────────────────────────────
class OrderStocksDialog(_Base):

    def __init__(self, parent=None):
        super().__init__("Create Purchase Order", parent)
        self.setMinimumWidth(620)
        self.supplier_combo = QComboBox()
        self.date_input     = QDateEdit(QDate.currentDate()); self.date_input.setCalendarPopup(True)
        self._field("Supplier *",                self.supplier_combo)
        self._field("Expected Delivery Date",    self.date_input)

        lo_lbl = QLabel("Order Items"); lo_lbl.setObjectName("section_title")
        self._lo.addWidget(lo_lbl)

        self.items_table = _make_table(["Item","Qty","Unit Price (₱)","Total (₱)"])
        self.items_table.setMaximumHeight(180); self._lo.addWidget(self.items_table)

        row = QHBoxLayout(); row.setSpacing(8)
        self.item_combo  = QComboBox(); self.item_combo.setMinimumWidth(180)
        self.qty_spin    = QSpinBox()
        self.qty_spin.setMinimum(0)   # allow 0 so we can catch it with an error
        self.qty_spin.setMaximum(9999)
        self.qty_spin.setValue(0)
        # Price is auto-filled from inventory unit cost — not editable by user
        self.price_spin  = QDoubleSpinBox(); self.price_spin.setMaximum(999999); self.price_spin.setDecimals(2)
        self.price_spin.setReadOnly(True)
        self.price_spin.setStyleSheet(
            "QDoubleSpinBox{background:#f0f2f5; color:#718096;}"
        )
        self.price_spin.setToolTip("Unit cost is set from Inventory and cannot be edited here.")
        self.add_row_btn = _btn("＋ Add", "success_btn")
        row.addWidget(QLabel("Item:")); row.addWidget(self.item_combo, 2)
        row.addWidget(QLabel("Qty:")); row.addWidget(self.qty_spin)
        row.addWidget(QLabel("Unit Cost (₱):")); row.addWidget(self.price_spin)
        row.addWidget(self.add_row_btn)
        self._lo.addLayout(row)
        self._ok_cancel("Place Order")


# ── Report Damage Dialog  (purchase-based — simplified) ──────────────────────
class ReportDamageDialog(_Base):
    """
    Admin reports damage on items received from a supplier.
    Step 1: select approved purchase order.
    Step 2: select item from that order.
    Step 3: enter quantity damaged + description.
    The damage is recorded and linked to the original supplier.
    """
    def __init__(self, parent=None):
        super().__init__("Report Supplier Damage", parent)

        self.purchase_combo = QComboBox()
        self.item_combo     = QComboBox()
        self.qty_spin       = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(9999)
        self.reason_inp     = QTextEdit(); self.reason_inp.setMaximumHeight(80)
        self.reason_inp.setPlaceholderText("Describe the damage (e.g. broken packaging, wrong items…)")

        self._field("Purchase Order (Approved) *", self.purchase_combo)
        self._field("Damaged Item *",               self.item_combo)
        self._field("Quantity Damaged",             self.qty_spin)
        self._field("Damage Description *",         self.reason_inp)

        # Supplier info label (read-only)
        self.supplier_lbl = QLabel("")
        self.supplier_lbl.setStyleSheet(
            "background:#fefcbf; color:#b7791f; border-radius:5px;"
            "padding:6px 10px; font-size:12px;"
        )
        self.supplier_lbl.setWordWrap(True)
        self._lo.addWidget(self.supplier_lbl)

        self._ok_cancel("Submit Damage Report")

    def get_data(self) -> dict:
        return {
            "purchase_id": self.purchase_combo.currentData(),
            "item_id":     self.item_combo.currentData(),
            "item_name":   self.item_combo.currentText(),
            "quantity":    self.qty_spin.value(),
            "reason":      self.reason_inp.toPlainText().strip(),
        }


# ── Suppliers List Dialog ─────────────────────────────────────────────────────
class SuppliersListDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Suppliers"); self.setMinimumSize(740, 440)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        lo = QVBoxLayout(self); lo.setContentsMargins(24,20,24,20); lo.setSpacing(12)

        top = QHBoxLayout()
        self.btn_add    = _btn("＋ Add Supplier",    "action_btn")
        self.btn_delete = _btn("🗑️  Delete Supplier", "danger_btn")
        top.addWidget(self.btn_add); top.addWidget(self.btn_delete); top.addStretch()
        lo.addLayout(top)

        self.table = _make_table(
            ["ID","Name","Contact","Email","Phone","Address"]
        )
        self.table.setMinimumHeight(300); lo.addWidget(self.table)
        close_btn = _btn("Close","secondary_btn"); close_btn.clicked.connect(self.accept)
        lo.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def populate(self, rows):
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["id"], row["name"], row["contact_name"] or "",
                row["email"] or "", row["phone"] or "", row["address"] or "",
            ]):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return int(self.table.item(row, 0).text())


# ── Supplier Form Dialog ──────────────────────────────────────────────────────
class SupplierFormDialog(_Base):

    def __init__(self, title="Add Supplier", parent=None):
        super().__init__(title, parent)
        self.name_inp    = QLineEdit()
        self.contact_inp = QLineEdit()
        self.email_inp   = QLineEdit()
        self.phone_inp   = QLineEdit()
        self.addr_inp    = QTextEdit(); self.addr_inp.setMaximumHeight(70)
        self._field("Supplier Name *", self.name_inp)
        self._field("Contact Person",  self.contact_inp)
        self._field("Email",           self.email_inp)
        self._field("Phone",           self.phone_inp)
        self._field("Address",         self.addr_inp)
        self._ok_cancel("Save Supplier")

    def load(self, s):
        self.name_inp.setText(s["name"])
        self.contact_inp.setText(s["contact_name"] or "")
        self.email_inp.setText(s["email"] or "")
        self.phone_inp.setText(s["phone"] or "")
        self.addr_inp.setPlainText(s["address"] or "")

    def get_data(self):
        return {
            "name":         self.name_inp.text().strip(),
            "contact_name": self.contact_inp.text().strip(),
            "email":        self.email_inp.text().strip(),
            "phone":        self.phone_inp.text().strip(),
            "address":      self.addr_inp.toPlainText().strip(),
        }


# ── Compose Message Dialog ────────────────────────────────────────────────────
class ComposeMessageDialog(_Base):

    def __init__(self, parent=None):
        super().__init__("Compose Message", parent)
        self.to_combo  = QComboBox()
        self.cat_combo = QComboBox()
        for c in ["General","Inventory","Purchase","Request","Report","Urgent"]:
            self.cat_combo.addItem(c)
        self.subj_inp = QLineEdit()
        self.body_inp = QTextEdit(); self.body_inp.setMinimumHeight(100)
        self._field("To *",         self.to_combo)
        self._field("Category",     self.cat_combo)
        self._field("Subject *",    self.subj_inp)
        self._field("Message Body *",self.body_inp)
        self._ok_cancel("Send Message")

    def load_recipients(self, users):
        for u in users:
            self.to_combo.addItem(f"{u['full_name']} ({u['role'].title()})", u["id"])

    def get_data(self):
        return {
            "recipient_id": self.to_combo.currentData(),
            "category":     self.cat_combo.currentText(),
            "title":        self.subj_inp.text().strip(),
            "body":         self.body_inp.toPlainText().strip(),
        }


# ── User Dialog ───────────────────────────────────────────────────────────────
class UserDialog(_Base):
    ROLES = [("Admin","admin"),("Owner","owner"),("Department Manager","department")]
    DEPTS = ["","Housekeeping","Dining","Maintenance","Laundry","Front Office","Security"]

    def __init__(self, title="Add User", parent=None):
        super().__init__(title, parent)
        self.name_inp  = QLineEdit()
        self.email_inp = QLineEdit()
        self.role_inp  = QComboBox()
        for label, val in self.ROLES: self.role_inp.addItem(label, val)
        self.dept_inp  = QComboBox()
        for d in self.DEPTS: self.dept_inp.addItem(d if d else "— N/A —", d)
        self.pw_inp    = QLineEdit(); self.pw_inp.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw2_inp   = QLineEdit(); self.pw2_inp.setEchoMode(QLineEdit.EchoMode.Password)

        self._field("Full Name *",          self.name_inp)
        self._field("Email Address *",       self.email_inp)
        self._field("Role *",                self.role_inp)
        self._field("Department (if dept)",  self.dept_inp)
        self._field("Password *",            self.pw_inp)
        self._field("Confirm Password",      self.pw2_inp)
        self._ok_cancel("Save User")

    def load(self, user):
        self.name_inp.setText(user.get("full_name",""))
        self.email_inp.setText(user.get("email",""))
        idx = self.role_inp.findData(user.get("role",""))
        if idx >= 0: self.role_inp.setCurrentIndex(idx)
        idx2 = self.dept_inp.findData(user.get("department") or "")
        if idx2 >= 0: self.dept_inp.setCurrentIndex(idx2)
        self.pw_inp.setPlaceholderText("Leave blank to keep unchanged")
        self.pw2_inp.setPlaceholderText("Leave blank to keep unchanged")

    def get_data(self):
        return {
            "full_name":  self.name_inp.text().strip(),
            "email":      self.email_inp.text().strip(),
            "role":       self.role_inp.currentData(),
            "department": self.dept_inp.currentData() or None,
            "password":   self.pw_inp.text(),
            "password2":  self.pw2_inp.text(),
        }


# ── Inventory History Dialog ──────────────────────────────────────────────────
class InventoryHistoryDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory Movement History")
        self.setMinimumSize(840, 440)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")
        lo = QVBoxLayout(self); lo.setContentsMargins(20,20,20,20); lo.setSpacing(12)

        top = QHBoxLayout()
        self.btn_export = _btn("📄 Export CSV","secondary_btn")
        top.addStretch(); top.addWidget(self.btn_export)
        lo.addLayout(top)

        self.table = _make_table(
            ["ID","Item","Movement","Qty","User","Dept","Notes","Date"]
        )
        self.table.setMinimumHeight(320); lo.addWidget(self.table)
        close_btn = _btn("Close","secondary_btn"); close_btn.clicked.connect(self.accept)
        lo.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self._rows = []

    def populate(self, rows):
        self._rows = rows
        self.table.setRowCount(0); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["id"], row["item_name"], row["movement_type"],
                row["quantity"], row["user_name"],
                row["department"] or "—", row["notes"] or "",
                str(row["created_at"])[:16],
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, cell)


# ── Purchase Order Detail Dialog ──────────────────────────────────────────────
class PurchaseDetailDialog(QDialog):
    """Popup that shows full details of a purchase order, including line items."""

    def __init__(self, purchase: dict, items: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Purchase Order #{purchase['id']} Details")
        self.setMinimumSize(680, 480)
        self.setStyleSheet(APP_STYLE + "QDialog{background:white;}")

        lo = QVBoxLayout(self)
        lo.setContentsMargins(28, 24, 28, 24)
        lo.setSpacing(14)

        # ── Title ─────────────────────────────────────────────────────────────
        title_lbl = QLabel(f"Purchase Order #{purchase['id']}")
        title_lbl.setObjectName("dlg_title")
        lo.addWidget(title_lbl)
        lo.addWidget(_h_sep())

        # ── Header info grid ──────────────────────────────────────────────────
        STATUS_CLR = {
            "pending":   ("#b7791f", "#fefcbf"),
            "delivered": ("#276749", "#f0fff4"),
            "rejected":  ("#c0392b", "#fdecea"),
        }
        fg, bg = STATUS_CLR.get(purchase["status"], ("#2d3748", "#f0f2f5"))

        status_badge = QLabel(purchase["status"].title())
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_badge.setStyleSheet(
            f"color:{fg}; background:{bg}; border-radius:6px;"
            f"padding:5px 14px; font-weight:bold; font-size:13px;"
        )
        lo.addWidget(status_badge, alignment=Qt.AlignmentFlag.AlignLeft)

        def _info_row(label: str, value: str):
            h = QHBoxLayout()
            lbl = QLabel(label); lbl.setObjectName("form_label"); lbl.setFixedWidth(140)
            val = QLabel(value); val.setWordWrap(True)
            val.setStyleSheet("color:#1a202c; font-size:13px;")
            h.addWidget(lbl); h.addWidget(val, 1)
            lo.addLayout(h)

        _info_row("Supplier:",       purchase.get("supplier") or "—")
        _info_row("Created By:",     purchase.get("created_by") or "—")
        _info_row("Order Date:",     str(purchase.get("created_at") or "")[:10])
        _info_row("Expected Date:",  str(purchase.get("expected_date") or "—"))
        _info_row("Total Amount:",   f"₱{float(purchase.get('total_amount', 0)):,.2f}")

        lo.addWidget(_h_sep())

        # ── Line items table ──────────────────────────────────────────────────
        items_lbl = QLabel("Order Items")
        items_lbl.setObjectName("section_title")
        lo.addWidget(items_lbl)

        tbl = _make_table(["Item Name", "Qty", "Unit Price (₱)", "Total (₱)", "In Inventory"])
        tbl.setMinimumHeight(180)
        tbl.setRowCount(len(items))
        for r, row in enumerate(items):
            in_inv = "✔ Yes" if row.get("in_inventory") else "Pending"
            in_clr = QColor("#f0fff4") if row.get("in_inventory") else QColor("#fefcbf")
            for c, val in enumerate([
                row.get("item_name", ""),
                row.get("quantity", ""),
                f"{float(row.get('unit_price', 0)):,.2f}",
                f"{float(row.get('total', 0)):,.2f}",
                in_inv,
            ]):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(in_clr)
                tbl.setItem(r, c, cell)
        lo.addWidget(tbl)

        # ── Close button ──────────────────────────────────────────────────────
        close_btn = _btn("Close", "secondary_btn")
        close_btn.clicked.connect(self.accept)
        lo.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
"""
controllers/owner_controller.py
────────────────────────────────
All business logic for the Hotel Owner / Director role.
"""

from PyQt6.QtWidgets import QMessageBox
from models.item_model              import ItemModel
from models.purchase_model          import PurchaseModel
from models.damage_model            import DamageModel
from models.message_model           import MessageModel
from models.user_model              import UserModel
from models.inventory_history_model import InventoryHistoryModel
from utils.report_generator         import (
    export_inventory_report, export_purchase_report,
    export_low_stock_report, export_movement_report,
)


class OwnerController:

    def __init__(self, view, user: dict):
        self.view = view
        self.user = user

        for idx, btn in enumerate(self.view.nav_buttons):
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
        self.view.logout_btn.clicked.connect(self._logout)

        self._wire_dept_overview()
        self._wire_reports()
        self._wire_messages()
        self._navigate(0)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate(self, idx: int):
        self.view.switch_page(idx)
        [self._load_dashboard, self._load_trans_history, self._load_dept_overview,
         self._load_reports,   self._load_messages][idx]()

    def _logout(self):
        from views.login_view            import LoginView
        from controllers.auth_controller import AuthController
        v = LoginView(); self._auth = AuthController(v); v.show(); self.view.close()

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _load_dashboard(self):
        self.view.dashboard_page.show_stats(
            f"₱{ItemModel.get_total_value():,.2f}",
            str(len(ItemModel.get_low_stock())),
            str(DamageModel.get_total_count()),
            str(ItemModel.get_total_count()),
        )

    # ── TRANSACTION HISTORY ───────────────────────────────────────────────────
    def _load_trans_history(self):
        self.view.trans_page.populate(PurchaseModel.get_for_owner())

    # ── DEPT OVERVIEW ─────────────────────────────────────────────────────────
    def _wire_dept_overview(self):
        dp = self.view.dept_page
        depts = self._get_departments()
        dp.set_departments(depts)
        dp.dept_combo.currentTextChanged.connect(self._filter_dept)

    def _get_departments(self) -> list[str]:
        from models.database import fetch_all
        rows = fetch_all(
            "SELECT DISTINCT department FROM users "
            "WHERE role='department' AND department IS NOT NULL ORDER BY department"
        )
        return [r["department"] for r in rows]

    def _load_dept_overview(self):
        self._filter_dept(self.view.dept_page.dept_combo.currentText())

    def _filter_dept(self, dept_text: str):
        dp = self.view.dept_page
        all_items = ItemModel.get_all()

        if dept_text and dept_text != "All Departments":
            items = [i for i in all_items if i["category"] == dept_text]
        else:
            items = all_items

        inv_value   = sum(float(i["unit_cost"]) * i["stock_qty"] for i in items)
        total_items = len(items)

        from models.database import fetch_one
        if dept_text and dept_text != "All Departments":
            dmg = fetch_one(
                "SELECT COUNT(*) cnt FROM damages d "
                "JOIN items i ON d.item_id=i.id WHERE i.category=%s",
                (dept_text,),
            )
        else:
            dmg = fetch_one("SELECT COUNT(*) cnt FROM damages")

        wastages = int(dmg["cnt"]) if dmg else 0

        dp.show_dept_stats(
            f"₱{inv_value:,.2f}",
            str(total_items),
            str(wastages),
        )
        dp.populate_items(items)

    # ── REPORTS ───────────────────────────────────────────────────────────────
    def _wire_reports(self):
        rp = self.view.reports_page

        def _pdf_stock():
            from utils.report_generator import export_inventory_pdf
            export_inventory_pdf(self.view, ItemModel.get_all())

        def _pdf_purchase():
            from utils.report_generator import export_purchase_pdf
            export_purchase_pdf(self.view, PurchaseModel.get_for_owner())

        def _pdf_low():
            from utils.report_generator import export_low_stock_pdf
            export_low_stock_pdf(self.view, ItemModel.get_low_stock())

        rp.btn_export_stock.clicked.connect(
            lambda: export_inventory_report(self.view, ItemModel.get_all())
        )
        if hasattr(rp, "btn_export_stock_pdf"):
            rp.btn_export_stock_pdf.clicked.connect(_pdf_stock)
        rp.btn_export_purchase.clicked.connect(
            lambda: export_purchase_report(self.view, PurchaseModel.get_for_owner())
        )
        if hasattr(rp, "btn_export_purchase_pdf"):
            rp.btn_export_purchase_pdf.clicked.connect(_pdf_purchase)
        rp.btn_export_low.clicked.connect(
            lambda: export_low_stock_report(self.view, ItemModel.get_low_stock())
        )
        if hasattr(rp, "btn_export_low_pdf"):
            rp.btn_export_low_pdf.clicked.connect(_pdf_low)

    def _load_reports(self):
        rp = self.view.reports_page

        items = ItemModel.get_all()[:12]
        rp.draw_stock_dist(
            [i["name"]      for i in items],
            [i["stock_qty"] for i in items],
        )

        mv = InventoryHistoryModel.get_movement_summary()
        rp.draw_movement(
            [r["movement_type"] for r in mv],
            [int(r["total"])    for r in mv],
        )

        rp.populate_low_stock(ItemModel.get_low_stock())

    # ── MESSAGES ──────────────────────────────────────────────────────────────
    def _wire_messages(self):
        mp = self.view.messages_page
        mp.btn_compose.clicked.connect(self._compose_message)
        mp.table.cellDoubleClicked.connect(self._view_message)

    def _load_messages(self):
        rows = MessageModel.get_for_user(self.user["id"])
        self.view.messages_page.populate(rows, self.user["full_name"])

    def _compose_message(self):
        from views.owner_view import OwnerComposeDialog
        dlg = OwnerComposeDialog(self.view)
        dlg.load_recipients(UserModel.get_all_for_messaging(self.user["id"]))

        def _send():
            d = dlg.get_data()
            if not d["title"] or not d["body"]:
                QMessageBox.warning(dlg, "Validation", "Subject and body are required.")
                return
            MessageModel.create(self.user["id"], d["recipient_id"],
                                d["category"], d["title"], d["body"])
            QMessageBox.information(dlg, "Sent", "Message sent.")
            dlg.accept(); self._load_messages()

        dlg.send_btn.clicked.connect(_send)
        dlg.exec()

    def _view_message(self, _row: int, _col: int):
        msg_id = self.view.messages_page.get_selected_id()
        if msg_id is None: return
        msg = MessageModel.get_by_id(msg_id)
        if not msg: return
        MessageModel.mark_read(msg_id)

        from views.message_dialog import MessageDetailDialog
        dlg = MessageDetailDialog(msg, self.user, self.view)

        def _on_reply(recipient_id: int, body: str):
            MessageModel.create(
                self.user["id"], recipient_id,
                msg.get("category", "General"),
                f"Re: {msg.get('title', '')}",
                body,
            )
            QMessageBox.information(self.view, "Sent", "Reply sent.")
            self._load_messages()

        dlg.reply_sent.connect(_on_reply)
        dlg.exec()
        self._load_messages()
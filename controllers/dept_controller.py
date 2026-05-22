"""
controllers/dept_controller.py
───────────────────────────────
Connects DeptView ↔ Models.
Business logic for the Department Manager role:
  • Dashboard stats (own department)
  • Inventory  (read-only view of their category)
  • Requests   (submit / cancel)
  • Reports    (stock chart, consumption chart, low-stock table) ← professor req.
  • Messages   (compose + view)
"""

from PyQt6.QtWidgets import QMessageBox

from models.item_model              import ItemModel
from models.request_model           import RequestModel
from models.damage_model            import DamageModel
from models.message_model           import MessageModel
from models.user_model              import UserModel
from models.inventory_history_model import InventoryHistoryModel


class DeptController:

    def __init__(self, view, user: dict):
        self.view = view
        self.user = user
        self.dept = user.get("department", "")

        # ── Wire navigation ───────────────────────────────────────────────────
        for idx, btn in enumerate(self.view.nav_buttons):
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))

        self.view.logout_btn.clicked.connect(self._logout)

        # ── Wire page actions ─────────────────────────────────────────────────
        self._wire_inventory()
        self._wire_requests()
        self._wire_reports()
        self._wire_messages()

        # Boot on dashboard
        self._navigate(0)

    # ═════════════════════════════════════════════════════════════════════════
    # Navigation
    # ═════════════════════════════════════════════════════════════════════════
    def _navigate(self, index: int):
        self.view.switch_page(index)
        loaders = [
            self._load_dashboard,
            self._load_inventory,
            self._load_requests,
            self._load_reports,
            self._load_messages,
        ]
        if index < len(loaders):
            loaders[index]()

    def _logout(self):
        from views.login_view            import LoginView
        from controllers.auth_controller import AuthController
        login_view  = LoginView()
        self._auth  = AuthController(login_view)
        login_view.show()
        self.view.close()

    # ═════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ═════════════════════════════════════════════════════════════════════════
    def _load_dashboard(self):
        dept_items  = self._get_dept_items()
        inv_value   = sum(float(i["unit_cost"]) * i["stock_qty"] for i in dept_items)
        pending_req = len(RequestModel.get_pending())
        wastages    = DamageModel.get_total_count()
        total_items = len(dept_items)

        self.view.dashboard_page.show_stats(
            f"₱{inv_value:,.2f}",
            str(pending_req),
            str(wastages),
            str(total_items),
        )

    # ═════════════════════════════════════════════════════════════════════════
    # INVENTORY  (read-only – department sees items in their category)
    # ═════════════════════════════════════════════════════════════════════════
    def _wire_inventory(self):
        ip = self.view.inventory_page
        ip.search_input.textChanged.connect(self._filter_inventory)
        ip.btn_history.clicked.connect(self._show_history)
        ip.btn_damage.clicked.connect(self._report_damage)
        self._all_dept_items: list[dict] = []

    def _load_inventory(self):
        self._all_dept_items = self._get_dept_items()
        self.view.inventory_page.populate(
            self._all_dept_items,
            use_cb=self._mark_used,
            restock_cb=self._restock,
        )

    def _filter_inventory(self):
        kw = self.view.inventory_page.search_input.text().lower()
        filtered = [
            r for r in self._all_dept_items
            if kw in r["name"].lower() or kw in (r["sku"] or "").lower()
        ]
        # Pass None so the stored callbacks are reused
        self.view.inventory_page.populate(filtered)

    # ── Stock adjustment actions (called by inline row buttons) ───────────────
    def _mark_used(self, item_id: int, item_name: str):
        from views.dept_view import StockAdjustDialog
        dlg = StockAdjustDialog(item_name, "use", self.view)

        def _confirm():
            d = dlg.get_data()
            from models.item_model import ItemModel
            ItemModel.adjust_stock(item_id, -d["quantity"])
            from models.inventory_history_model import InventoryHistoryModel
            InventoryHistoryModel.log(
                item_name, "distributed", d["quantity"],
                self.user["full_name"], d["notes"] or None, self.dept,
            )
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(dlg, "Recorded",
                                    f"Marked {d['quantity']} unit(s) of '{item_name}' as used.")
            dlg.accept()
            self._load_inventory()

        dlg.ok_btn.clicked.connect(_confirm)
        dlg.exec()

    def _restock(self, item_id: int, item_name: str):
        from views.dept_view import StockAdjustDialog
        dlg = StockAdjustDialog(item_name, "restock", self.view)

        def _confirm():
            d = dlg.get_data()
            from models.item_model import ItemModel
            ItemModel.adjust_stock(item_id, d["quantity"])
            from models.inventory_history_model import InventoryHistoryModel
            InventoryHistoryModel.log(
                item_name, "stock_in", d["quantity"],
                self.user["full_name"], d["notes"] or None, self.dept,
            )
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(dlg, "Recorded",
                                    f"Added {d['quantity']} unit(s) to '{item_name}'.")
            dlg.accept()
            self._load_inventory()

        dlg.ok_btn.clicked.connect(_confirm)
        dlg.exec()

    def _show_history(self):
        from views.dept_view import InventoryHistoryDialog
        from models.inventory_history_model import InventoryHistoryModel
        from utils.report_generator import export_movement_report
        dlg = InventoryHistoryDialog(self.view)
        rows = InventoryHistoryModel.get_by_department(self.dept)
        dlg.populate(rows)
        dlg.btn_export.clicked.connect(
            lambda: export_movement_report(dlg, dlg._rows)
        )
        dlg.exec()

    def _report_damage(self):
        from views.dept_view import DeptDamageReportDialog
        from models.damage_model import DamageModel
        from models.item_model import ItemModel
        from models.inventory_history_model import InventoryHistoryModel
        from PyQt6.QtWidgets import QMessageBox

        dlg = DeptDamageReportDialog(self.view)
        dlg.load_items(self._get_dept_items())

        def _submit():
            d = dlg.get_data()
            if not d["item_id"]:
                QMessageBox.warning(dlg, "Validation", "Select an item.")
                return
            if not d["reason"].strip():
                QMessageBox.warning(dlg, "Validation", "Description is required.")
                return
            DamageModel.create(
                d["item_id"], d["quantity"], self.dept,
                d["reason"], self.user["full_name"],
            )
            ItemModel.adjust_stock(d["item_id"], -d["quantity"])
            InventoryHistoryModel.log(
                d["item_name"], "damage", d["quantity"],
                self.user["full_name"],
                f"Damage: {d['reason'][:60]}", self.dept,
            )
            QMessageBox.information(dlg, "Reported", "Damage report submitted.")
            dlg.accept()
            self._load_inventory()

        dlg.ok_btn.clicked.connect(_submit)
        dlg.exec()

    def _get_dept_items(self) -> list[dict]:
        """Return all items whose category matches this dept, or all if no dept set."""
        if self.dept:
            return ItemModel.get_by_department(self.dept)
        return ItemModel.get_all()

    # ═════════════════════════════════════════════════════════════════════════
    # REQUESTS
    # ═════════════════════════════════════════════════════════════════════════
    def _wire_requests(self):
        rp = self.view.requests_page
        rp.btn_new.clicked.connect(self._new_request)
        rp.btn_cancel.clicked.connect(self._cancel_request)

    def _load_requests(self):
        rows = RequestModel.get_by_department(self.dept)
        self.view.requests_page.populate(rows)

    def _new_request(self):
        from views.dept_view import NewRequestDialog
        from PyQt6.QtWidgets import QApplication

        dlg = NewRequestDialog(self.view)

        # Populate combo BEFORE exec() so all addItem calls happen while the
        # dialog is not yet visible — avoids the Windows recursive-repaint crash.
        all_items = ItemModel.get_all()
        dlg.load_items(all_items)

        # Flush any pending layout/paint events before opening the modal loop
        QApplication.processEvents()

        def _submit():
            d = dlg.get_data()
            if not d["item_name"]:
                QMessageBox.warning(dlg, "Validation", "Item name is required.")
                return
            RequestModel.create(
                self.dept,
                self.user["full_name"],
                d["item_name"],
                d["quantity"],
                d["unit"],
                d["reason"],
                is_new_item=d["is_new"],
            )
            QMessageBox.information(dlg, "Submitted",
                                    "Request submitted and is pending approval.")
            # Close dialog FIRST, then reload — never reload while dialog is live
            dlg.accept()
            self._load_requests()

        dlg.ok_btn.clicked.connect(_submit)
        dlg.exec()

    def _cancel_request(self):
        req_id = self.view.requests_page.get_selected_id()
        if req_id is None:
            QMessageBox.warning(self.view, "Select", "Please select a request first.")
            return
        req = RequestModel.get_by_id(req_id)
        if req["status"] != "Pending":
            QMessageBox.warning(self.view, "Cannot Cancel",
                                "Only pending requests can be cancelled.")
            return
        reply = QMessageBox.question(
            self.view, "Cancel Request",
            "Cancel this request?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            RequestModel.update_status(req_id, "Cancelled", "Cancelled by department manager")
            self._load_requests()

    # ═════════════════════════════════════════════════════════════════════════
    # REPORTS  (professor requirement: report system on department manager side)
    # ═════════════════════════════════════════════════════════════════════════
    def _wire_reports(self):
        rp = self.view.reports_page

        def _csv_stock():
            from utils.report_generator import export_inventory_report
            export_inventory_report(self.view, self._get_dept_items())

        def _pdf_stock():
            from utils.report_generator import export_inventory_pdf
            export_inventory_pdf(self.view, self._get_dept_items())

        def _csv_con():
            from utils.report_generator import export_dept_consumption
            export_dept_consumption(
                self.view,
                InventoryHistoryModel.get_dept_consumption(self.dept),
                self.dept,
            )

        def _pdf_con():
            from utils.report_generator import export_dept_consumption_pdf
            export_dept_consumption_pdf(
                self.view,
                InventoryHistoryModel.get_dept_consumption(self.dept),
                self.dept,
            )

        def _csv_low():
            from utils.report_generator import export_low_stock_report
            export_low_stock_report(self.view, [
                {**i, "deficit": i["min_stock"] - i["stock_qty"]}
                for i in self._get_dept_items()
                if i["stock_qty"] < i["min_stock"]
            ])

        def _pdf_low():
            from utils.report_generator import export_low_stock_pdf
            export_low_stock_pdf(self.view, [
                {**i, "deficit": i["min_stock"] - i["stock_qty"]}
                for i in self._get_dept_items()
                if i["stock_qty"] < i["min_stock"]
            ])

        rp.btn_export_stock.clicked.connect(_csv_stock)
        if hasattr(rp, "btn_export_stock_pdf"):
            rp.btn_export_stock_pdf.clicked.connect(_pdf_stock)
        rp.btn_export_con.clicked.connect(_csv_con)
        if hasattr(rp, "btn_export_con_pdf"):
            rp.btn_export_con_pdf.clicked.connect(_pdf_con)
        rp.btn_export_low.clicked.connect(_csv_low)
        if hasattr(rp, "btn_export_low_pdf"):
            rp.btn_export_low_pdf.clicked.connect(_pdf_low)

    def _load_reports(self):
        rp = self.view.reports_page

        # 1. Stock levels bar chart (dept items)
        items = self._get_dept_items()
        rp.draw_stock_chart(
            [i["name"]      for i in items],
            [i["stock_qty"] for i in items],
            [i["min_stock"] for i in items],
        )

        # 2. Consumption chart (distributed movements for this dept)
        consumption = InventoryHistoryModel.get_dept_consumption(self.dept)
        rp.draw_consumption_chart(
            [r["item_name"]   for r in consumption],
            [int(r["total_used"]) for r in consumption],
        )

        # 3. Low-stock table (dept items only)
        low = [
            {**i, "deficit": i["min_stock"] - i["stock_qty"]}
            for i in items if i["stock_qty"] < i["min_stock"]
        ]
        rp.populate_low_stock(low)

    # ═════════════════════════════════════════════════════════════════════════
    # MESSAGES
    # ═════════════════════════════════════════════════════════════════════════
    def _wire_messages(self):
        mp = self.view.messages_page
        mp.btn_compose.clicked.connect(self._compose_message)
        mp.table.cellDoubleClicked.connect(self._view_message)

    def _load_messages(self):
        rows = MessageModel.get_for_user(self.user["id"])
        self.view.messages_page.populate(rows, self.user["full_name"])

    def _compose_message(self):
        from views.dept_view import DeptComposeDialog
        dlg = DeptComposeDialog(self.view)
        dlg.load_recipients(UserModel.get_all_for_messaging(self.user["id"]))

        def _send():
            d = dlg.get_data()
            if not d["title"] or not d["body"]:
                QMessageBox.warning(dlg, "Validation",
                                    "Subject and body are required.")
                return
            MessageModel.create(
                self.user["id"], d["recipient_id"],
                d["category"], d["title"], d["body"],
            )
            QMessageBox.information(dlg, "Sent", "Message sent successfully.")
            dlg.accept()
            self._load_messages()

        dlg.send_btn.clicked.connect(_send)
        dlg.exec()

    def _view_message(self, row: int, _col: int):
        msg_id = self.view.messages_page.get_selected_id()
        if msg_id is None:
            return
        msg = MessageModel.get_by_id(msg_id)
        if not msg:
            return
        MessageModel.mark_read(msg_id)
        box = QMessageBox(self.view)
        box.setWindowTitle(f"Message – {msg['title']}")
        box.setText(
            f"<b>From:</b> {msg['sender_name']}<br>"
            f"<b>To:</b> {msg['recipient_name']}<br>"
            f"<b>Category:</b> {msg['category']}<br>"
            f"<b>Subject:</b> {msg['title']}<br><br>"
            f"{msg['body']}"
        )
        box.exec()
        self._load_messages()
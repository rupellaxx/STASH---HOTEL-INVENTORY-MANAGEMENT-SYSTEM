"""
controllers/admin_controller.py
────────────────────────────────
All business logic for the Purchase Admin role.
"""

from PyQt6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from models.item_model              import ItemModel
from models.purchase_model          import PurchaseModel
from models.supplier_model          import SupplierModel
from models.damage_model            import DamageModel
from models.message_model           import MessageModel
from models.user_model              import UserModel
from models.inventory_history_model import InventoryHistoryModel
from models.request_model           import RequestModel
from utils.report_generator         import (
    export_inventory_report, export_movement_report,
    export_low_stock_report, export_damage_report,
)

import re

# ── Validation helpers ────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_PHONE_RE = re.compile(r"^[\d\s\+\-\(\)\.]{7,20}$")

def _valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))

def _valid_phone(phone: str) -> bool:
    return bool(_PHONE_RE.match(phone))


class AdminController:

    def __init__(self, view, user: dict):
        self.view = view
        self.user = user
        self._all_items: list[dict] = []
        self._all_users: list[dict] = []

        for idx, btn in enumerate(self.view.nav_buttons):
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
        self.view.logout_btn.clicked.connect(self._logout)

        self._wire_purchase()
        self._wire_inventory()
        self._wire_requests()
        self._wire_reports()
        self._wire_messages()
        self._wire_user_mgmt()
        self._navigate(0)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate(self, idx: int):
        self.view.switch_page(idx)
        [self._load_dashboard, self._load_purchase, self._load_inventory,
         self._load_requests,  self._load_reports,
         self._load_messages,  self._load_user_mgmt][idx]()

    def _logout(self):
        from views.login_view            import LoginView
        from controllers.auth_controller import AuthController
        v = LoginView(); self._auth = AuthController(v); v.show(); self.view.close()

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    def _load_dashboard(self):
        ok, total = ItemModel.get_stock_health().replace("%",""), "100"
        self.view.dashboard_page.show_stats(
            f"₱{ItemModel.get_total_value():,.2f}",
            str(len(ItemModel.get_low_stock())),
            str(DamageModel.get_total_count()),
            str(ItemModel.get_total_count()),
            ItemModel.get_stock_health(),
            str(len(RequestModel.get_pending())),
        )

    # ── PURCHASE ──────────────────────────────────────────────────────────────
    def _wire_purchase(self):
        pp = self.view.purchase_page
        pp.btn_order.clicked.connect(self._open_order_dialog)
        pp.btn_supplier.clicked.connect(self._open_suppliers_dialog)
        pp.btn_refresh.clicked.connect(self._load_purchase)
        pp.btn_damage.clicked.connect(self._open_damage_dialog)
        pp.table.cellDoubleClicked.connect(self._open_purchase_detail)

    def _load_purchase(self):
        rows = PurchaseModel.get_all()
        self.view.purchase_page.populate_table(rows, self._deliver_purchase)

    def _open_purchase_detail(self, _row: int, _col: int):
        """Double-click on purchase row → show full order details popup."""
        from views.admin_view import PurchaseDetailDialog
        pid = self.view.purchase_page.get_selected_id()
        if pid is None:
            return
        purchase = PurchaseModel.get_by_id(pid)
        if not purchase:
            return
        # get_by_id returns supplier_name; map to 'supplier' key for the dialog
        purchase.setdefault("supplier", purchase.get("supplier_name", "—"))
        items = PurchaseModel.get_items(pid)
        dlg = PurchaseDetailDialog(purchase, items, self.view)
        dlg.exec()

    def _deliver_purchase(self, purchase_id: int):
        reply = QMessageBox.question(
            self.view, "Mark as Delivered",
            "Mark this purchase as delivered and add all items to inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        pending = PurchaseModel.get_pending_items(purchase_id)
        item_names_added = []
        for pi in pending:
            if pi["item_id"]:
                ItemModel.adjust_stock(pi["item_id"], pi["quantity"])
                item = ItemModel.get_by_id(pi["item_id"])
                if item:
                    item_names_added.append(item["name"])
                    InventoryHistoryModel.log(
                        item["name"], "stock_in", pi["quantity"],
                        self.user["full_name"], f"Purchase #{purchase_id}",
                    )
            PurchaseModel.mark_item_in_inventory(pi["id"], pi["quantity"])
        PurchaseModel.deliver(purchase_id)

        # Auto-complete any Approved requests whose item was just restocked
        if item_names_added:
            all_approved = RequestModel.get_pending()
            for req in all_approved:
                if req["status"] == "Approved" and req["item_name"] in item_names_added:
                    RequestModel.complete(req["id"])

        QMessageBox.information(self.view, "Delivered",
                                "Purchase marked as delivered — inventory updated.")
        self._load_purchase()
        self._load_requests()

    def _open_order_dialog(self):
        from views.admin_view import OrderStocksDialog
        suppliers = SupplierModel.get_all()
        if not suppliers:
            QMessageBox.warning(self.view, "No Suppliers",
                                "Please add at least one supplier first.")
            return
        items = ItemModel.get_all()
        if not items:
            QMessageBox.warning(self.view, "No Items",
                                "Please add at least one item to inventory first.")
            return

        dlg = OrderStocksDialog(self.view)
        for s in suppliers:
            dlg.supplier_combo.addItem(s["name"], s["id"])
        for it in items:
            dlg.item_combo.addItem(it["name"], {"id": it["id"], "cost": float(it["unit_cost"])})

        def _autofill():
            d = dlg.item_combo.currentData()
            if d:
                dlg.price_spin.setValue(d["cost"])
                dlg.qty_spin.setValue(1)

        dlg.item_combo.currentIndexChanged.connect(_autofill)
        _autofill()

        dlg._order_rows = []

        def _add_row():
            name  = dlg.item_combo.currentText()
            qty   = dlg.qty_spin.value()
            price = dlg.price_spin.value()

            if qty < 1:
                QMessageBox.warning(dlg, "Invalid Quantity",
                                    "Quantity must be at least 1.\n"
                                    "Please enter a valid quantity before adding.")
                dlg.qty_spin.setValue(1)
                dlg.qty_spin.setFocus()
                return

            total = qty * price
            data  = dlg.item_combo.currentData()
            dlg._order_rows.append(
                {"name": name, "item_id": data["id"],
                 "qty": qty, "price": price, "total": total}
            )
            from PyQt6.QtWidgets import QTableWidgetItem
            r = dlg.items_table.rowCount()
            dlg.items_table.insertRow(r)
            for c, v in enumerate([name, qty, f"{price:,.2f}", f"{total:,.2f}"]):
                dlg.items_table.setItem(r, c, QTableWidgetItem(str(v)))

        dlg.add_row_btn.clicked.connect(_add_row)

        def _place_order():
            if not dlg._order_rows:
                QMessageBox.warning(dlg, "Validation", "Add at least one item.")
                return
            total  = sum(r["total"] for r in dlg._order_rows)
            sup_id = dlg.supplier_combo.currentData()
            exp    = dlg.date_input.date().toPyDate()
            pid    = PurchaseModel.create(sup_id, exp, total, self.user["full_name"])
            for row in dlg._order_rows:
                PurchaseModel.add_item(pid, row["name"], row["item_id"],
                                       row["qty"], row["price"], row["total"])
            QMessageBox.information(dlg, "Created",
                                    f"Purchase Order #{pid} created (pending approval).")
            dlg.accept()
            self._load_purchase()

        dlg.ok_btn.clicked.connect(_place_order)
        dlg.exec()

    def _open_suppliers_dialog(self):
        from views.admin_view import SuppliersListDialog, SupplierFormDialog

        dlg = SuppliersListDialog(self.view)
        dlg.populate(SupplierModel.get_all())

        def _add():
            form = SupplierFormDialog("Add Supplier", dlg)
            def _save():
                d = form.get_data()
                if not d["name"]:
                    QMessageBox.warning(form, "Validation", "Supplier name is required.")
                    return
                if d["email"] and not _valid_email(d["email"]):
                    QMessageBox.warning(form, "Invalid Email",
                                        "Please enter a valid email address.\n"
                                        "Example: supplier@company.com")
                    return
                if d["phone"] and not _valid_phone(d["phone"]):
                    QMessageBox.warning(form, "Invalid Phone",
                                        "Phone number can only contain digits, spaces,\n"
                                        "and the symbols: + - ( ) .\n"
                                        "Example: +63 912 345 6789")
                    return
                SupplierModel.create(d["name"], d["contact_name"],
                                     d["email"], d["phone"], d["address"])
                form.accept()
                dlg.populate(SupplierModel.get_all())
            form.ok_btn.clicked.connect(_save)
            form.exec()

        def _delete():
            sid = dlg.get_selected_id()
            if sid is None:
                QMessageBox.warning(dlg, "Select", "Select a supplier first.")
                return
            sup = SupplierModel.get_by_id(sid)
            reply = QMessageBox.question(
                dlg, "Delete Supplier",
                f"Delete supplier '{sup['name']}'?\n"
                "Existing purchase orders linked to them will remain.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                SupplierModel.delete(sid)
                dlg.populate(SupplierModel.get_all())

        dlg.btn_add.clicked.connect(_add)
        dlg.btn_delete.clicked.connect(_delete)
        dlg.exec()

    def _open_damage_dialog(self):
        from views.admin_view import ReportDamageDialog

        approved = PurchaseModel.get_approved()
        if not approved:
            QMessageBox.information(
                self.view, "No Approved Orders",
                "There are no approved purchase orders to report damage against.\n"
                "Damage is reported against received (approved) purchases only.",
            )
            return

        dlg = ReportDamageDialog(self.view)
        for p in approved:
            dlg.purchase_combo.addItem(
                f"PO #{p['id']} — {p['supplier']} ({str(p['created_at'])[:10]})",
                p["id"],
            )

        def _load_items_for_purchase():
            purchase_id = dlg.purchase_combo.currentData()
            dlg.item_combo.clear()
            if purchase_id is None:
                return
            p_info = PurchaseModel.get_by_id(purchase_id)
            if p_info:
                dlg.supplier_lbl.setText(
                    f"📦 Supplier: {p_info['supplier_name']}  "
                    f"| Contact: {p_info['supplier_contact'] or 'N/A'}  "
                    f"| Email: {p_info['supplier_email'] or 'N/A'}"
                )
            p_items = PurchaseModel.get_items(purchase_id)
            for pi in p_items:
                if pi["item_id"]:
                    item = ItemModel.get_by_id(pi["item_id"])
                    if item:
                        dlg.item_combo.addItem(item["name"], pi["item_id"])

        dlg.purchase_combo.currentIndexChanged.connect(_load_items_for_purchase)
        _load_items_for_purchase()

        def _submit():
            d = dlg.get_data()
            if not d["purchase_id"] or not d["item_id"]:
                QMessageBox.warning(dlg, "Validation",
                                    "Select a purchase order and an item.")
                return
            if not d["reason"].strip():
                QMessageBox.warning(dlg, "Validation", "Description is required.")
                return
            DamageModel.create(
                d["item_id"], d["quantity"], "Supplier Damage",
                d["reason"], self.user["full_name"], d["purchase_id"],
            )
            ItemModel.adjust_stock(d["item_id"], -d["quantity"])
            InventoryHistoryModel.log(
                d["item_name"], "damage", d["quantity"],
                self.user["full_name"],
                f"Damage report — PO #{d['purchase_id']}: {d['reason'][:60]}",
            )
            QMessageBox.information(dlg, "Reported",
                                    "Damage report submitted and stock adjusted.")
            dlg.accept()
            self._load_purchase()

        dlg.ok_btn.clicked.connect(_submit)
        dlg.exec()

    # ── REQUESTS ──────────────────────────────────────────────────────────────
    def _wire_requests(self):
        rp = self.view.requests_page
        rp.table.cellDoubleClicked.connect(self._open_request_detail)
        rp.status_combo.currentTextChanged.connect(self._filter_requests)
        rp.search_input.textChanged.connect(self._filter_requests)
        self._all_requests: list[dict] = []

    def _load_requests(self):
        self._all_requests = RequestModel.get_all()
        self._filter_requests()

    def _filter_requests(self):
        status = self.view.requests_page.status_combo.currentText()
        kw     = self.view.requests_page.search_input.text().lower()
        filtered = [
            r for r in self._all_requests
            if (status == "All" or r["status"] == status)
            and (not kw or kw in r["item_name"].lower()
                 or kw in r["department"].lower())
        ]
        self.view.requests_page.populate(filtered)

    def _open_request_detail(self, _row: int, _col: int):
        from views.admin_view import RequestDetailDialog
        req_id = self.view.requests_page.get_selected_id()
        if req_id is None:
            return
        req = RequestModel.get_by_id(req_id)
        if not req:
            return

        dlg = RequestDetailDialog(req, self.view)

        def _approve():
            RequestModel.update_status(req_id, "Approved",
                                       f"Approved by {self.user['full_name']}")
            dlg.accept()
            self._load_requests()

            # Check both the flag AND whether the item actually exists in inventory
            flagged_new   = bool(req.get("is_new_item"))
            item_in_stock = ItemModel.get_by_name(req["item_name"]) is not None

            if flagged_new or not item_in_stock:
                # Item does not exist in inventory — navigate and open Add Item
                self._navigate(2)
                QMessageBox.information(
                    self.view, "Request Approved — Add the Item",
                    f"✔ Request approved!\n\n"
                    f"'{req['item_name']}' is not yet in inventory.\n\n"
                    "The Add Item form will open now so you can add it directly.",
                )
                self._add_item_prefilled(
                    name=req["item_name"],
                    unit=req.get("unit") or "pcs",
                )
            else:
                QMessageBox.information(
                    self.view, "Request Approved",
                    f"✔ Request approved!\n\n"
                    f"'{req['item_name']}' is already in inventory.\n"
                    "Create a Purchase Order to restock it if needed.",
                )

        def _decline():
            RequestModel.update_status(req_id, "Rejected",
                                       f"Declined by {self.user['full_name']}")
            QMessageBox.information(dlg, "Declined", "Request has been declined.")
            dlg.accept()
            self._load_requests()

        dlg.btn_approve.clicked.connect(_approve)
        dlg.btn_decline.clicked.connect(_decline)
        dlg.exec()
    def _wire_inventory(self):
        ip = self.view.inventory_page
        ip.btn_add.clicked.connect(self._add_item)
        ip.btn_delete.clicked.connect(self._delete_item)
        ip.btn_history.clicked.connect(self._show_history)
        ip.search_input.textChanged.connect(self._filter_inventory)
        ip.cat_combo.currentTextChanged.connect(self._filter_inventory)

    def _load_inventory(self):
        self._all_items = ItemModel.get_all()
        cats = ItemModel.get_categories()
        self.view.inventory_page.set_categories(cats)
        self.view.inventory_page.populate_table(self._all_items)

    def _filter_inventory(self):
        kw  = self.view.inventory_page.get_search_text()
        cat = self.view.inventory_page.get_selected_category()
        filtered = [
            r for r in self._all_items
            if (kw in r["name"].lower() or kw in (r["sku"] or "").lower())
            and (cat == "All Categories" or r["category"] == cat)
        ]
        self.view.inventory_page.populate_table(filtered)

    def _add_item(self):
        from views.admin_view import ItemDialog
        dlg = ItemDialog(self.view)
        # Show live SKU preview when category changes
        def _preview():
            cat = dlg.cat_inp.currentText()
            dlg.set_sku_preview(ItemModel.generate_sku(cat))
        dlg.cat_inp.currentTextChanged.connect(_preview)
        _preview()

        def _save():
            d = dlg.get_data()
            if not d["name"]:
                QMessageBox.warning(dlg, "Validation", "Item name is required.")
                return
            # Check for duplicate name
            existing = ItemModel.get_by_name(d["name"])
            if existing:
                QMessageBox.warning(
                    dlg, "Duplicate Item",
                    f"An item named '{d['name']}' already exists in inventory "
                    f"(SKU: {existing['sku']}, Category: {existing['category']}).\n\n"
                    "Please use a different name or find the existing item in Inventory.",
                )
                return
            iid = ItemModel.create(d["name"], d["unit"], d["unit_cost"],
                                   d["min_stock"], d["category"])
            item = ItemModel.get_by_id(iid)
            QMessageBox.information(dlg, "Item Added",
                                    f"✔ Item '{item['name']}' added successfully!\n"
                                    f"SKU: {item['sku']}\n\n"
                                    "Stock starts at 0. Create a Purchase Order to add stock.")
            dlg.accept()
            self._load_inventory()

        dlg.ok_btn.clicked.connect(_save)
        dlg.exec()

    def _add_item_prefilled(self, name: str = "", unit: str = "pcs"):
        """Open the Add Item dialog with name and unit pre-filled (used after approving a new-item request)."""
        from views.admin_view import ItemDialog

        # Map unit from request to the combo index if it exists
        _UNITS = ["pcs", "kg", "g", "L", "mL", "box", "pack", "set",
                  "roll", "pair", "bottle", "bag", "sheet", "tube", "pad"]

        dlg = ItemDialog(self.view)

        # Pre-fill name
        dlg.name_inp.setText(name)

        # Pre-select unit if it matches a known option, else default to pcs
        unit_lower = (unit or "pcs").lower()
        matched = next((u for u in _UNITS if u.lower() == unit_lower), "pcs")
        idx = dlg.unit_combo.findText(matched)
        if idx >= 0:
            dlg.unit_combo.setCurrentIndex(idx)

        def _preview():
            dlg.set_sku_preview(ItemModel.generate_sku(dlg.cat_inp.currentText()))
        dlg.cat_inp.currentTextChanged.connect(_preview)
        _preview()

        def _save():
            d = dlg.get_data()
            if not d["name"]:
                QMessageBox.warning(dlg, "Validation", "Item name is required.")
                return
            if d["unit_cost"] <= 0:
                QMessageBox.warning(dlg, "Invalid Cost",
                                    "Unit cost must be greater than ₱0.00.\n"
                                    "Please enter a valid price.")
                return
            existing = ItemModel.get_by_name(d["name"])
            if existing:
                QMessageBox.warning(
                    dlg, "Already Exists",
                    f"'{d['name']}' is already in inventory (SKU: {existing['sku']}).\n"
                    "No need to add it again.",
                )
                dlg.accept()
                return
            iid = ItemModel.create(d["name"], d["unit"], d["unit_cost"],
                                   d["min_stock"], d["category"])
            item = ItemModel.get_by_id(iid)
            QMessageBox.information(
                dlg, "Item Added",
                f"✔ '{item['name']}' added to inventory!\n"
                f"SKU: {item['sku']}\n\n"
                "Now create a Purchase Order to stock it.",
            )
            dlg.accept()
            self._load_inventory()

        dlg.ok_btn.clicked.connect(_save)
        dlg.exec()

    def _delete_item(self):
        iid = self.view.inventory_page.get_selected_id()
        if iid is None:
            QMessageBox.warning(self.view, "Select Item", "Please select an item first.")
            return
        item = ItemModel.get_by_id(iid)
        if item is None:
            return

        # Check if any dept uses this category
        from models.database import fetch_one
        has_dept = fetch_one(
            "SELECT id FROM users WHERE role='department' AND department=%s LIMIT 1",
            (item["category"],),
        )
        if has_dept:
            reply = QMessageBox.question(
                self.view, "Department Approval Required",
                f"'{item['name']}' belongs to the {item['category']} department.\n\n"
                f"Deleting it will remove it from their inventory.\n"
                f"Are you sure the {item['category']} manager has approved this removal?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        confirm = QMessageBox.question(
            self.view, "Delete Item",
            f"Permanently delete '{item['name']}' (SKU: {item['sku']})?\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ItemModel.delete(iid)
            self._load_inventory()

    def _show_history(self):
        from views.admin_view import InventoryHistoryDialog
        dlg = InventoryHistoryDialog(self.view)
        rows = InventoryHistoryModel.get_all()
        dlg.populate(rows)
        dlg.btn_export.clicked.connect(
            lambda: export_movement_report(dlg, dlg._rows)
        )
        dlg.exec()

    # ── REPORTS ───────────────────────────────────────────────────────────────
    def _wire_reports(self):
        rp = self.view.reports_page
        rp.btn_export_inv.clicked.connect(
            lambda: export_inventory_report(self.view, ItemModel.get_all())
        )
        rp.btn_export_move.clicked.connect(
            lambda: export_movement_report(self.view, InventoryHistoryModel.get_all())
        )
        rp.btn_export_low.clicked.connect(
            lambda: export_low_stock_report(self.view, ItemModel.get_low_stock())
        )
        rp.btn_export_dmg.clicked.connect(
            lambda: export_damage_report(self.view, DamageModel.get_all())
        )

    def _load_reports(self):
        rp = self.view.reports_page
        items = ItemModel.get_all()
        top = items[:20]
        rp.draw_stock_chart(
            [r["name"][:14] for r in top],
            [r["stock_qty"]  for r in top],
            [r["min_stock"]  for r in top],
        )
        mv = InventoryHistoryModel.get_movement_summary()
        rp.draw_movement_chart(
            [r["movement_type"] for r in mv],
            [int(r["total"])    for r in mv],
        )
        rp.populate_low_stock(ItemModel.get_low_stock())
        rp.populate_damage_log(DamageModel.get_all())

    # ── MESSAGES ──────────────────────────────────────────────────────────────
    def _wire_messages(self):
        mp = self.view.messages_page
        mp.btn_compose.clicked.connect(self._compose_message)
        mp.table.cellDoubleClicked.connect(self._view_message)

    def _load_messages(self):
        rows = MessageModel.get_for_user(self.user["id"])
        self.view.messages_page.populate_table(rows, self.user["full_name"])

    def _compose_message(self):
        from views.admin_view import ComposeMessageDialog
        dlg = ComposeMessageDialog(self.view)
        dlg.load_recipients(UserModel.get_all_for_messaging(self.user["id"]))

        def _send():
            d = dlg.get_data()
            if not d["title"] or not d["body"]:
                QMessageBox.warning(dlg, "Validation",
                                    "Subject and body are required.")
                return
            MessageModel.create(self.user["id"], d["recipient_id"],
                                d["category"], d["title"], d["body"])
            QMessageBox.information(dlg, "Sent", "Message sent.")
            dlg.accept(); self._load_messages()

        dlg.ok_btn.clicked.connect(_send)
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

    # ── USER MANAGEMENT ───────────────────────────────────────────────────────
    def _wire_user_mgmt(self):
        um = self.view.user_mgmt_page
        um.btn_add.clicked.connect(self._add_user)
        um.btn_edit.clicked.connect(self._edit_user)
        um.btn_delete.clicked.connect(self._delete_user)
        um.btn_reset.clicked.connect(self._reset_password)
        um.search_input.textChanged.connect(self._filter_users)

    def _load_user_mgmt(self):
        self._all_users = UserModel.get_all()
        self.view.user_mgmt_page.populate_table(self._all_users)

    def _filter_users(self):
        kw = self.view.user_mgmt_page.get_search_text()
        self.view.user_mgmt_page.populate_table([
            u for u in self._all_users
            if kw in u["full_name"].lower() or kw in u["email"].lower()
        ])

    def _add_user(self):
        from views.admin_view import UserDialog
        dlg = UserDialog("Add User", self.view)

        def _save():
            d = dlg.get_data()
            if not d["full_name"] or not d["email"]:
                QMessageBox.warning(dlg, "Validation", "Name and email are required.")
                return
            if not _valid_email(d["email"]):
                QMessageBox.warning(dlg, "Invalid Email",
                                    "Please enter a valid email address.\n"
                                    "Example: user@hotel.com")
                return
            if not d["password"]:
                QMessageBox.warning(dlg, "Validation", "Password is required.")
                return
            if d["password"] != d["password2"]:
                QMessageBox.warning(dlg, "Validation", "Passwords do not match.")
                return
            if UserModel.email_exists(d["email"]):
                QMessageBox.warning(dlg, "Validation", "Email already in use.")
                return
            UserModel.create(d["full_name"], d["email"], d["password"],
                             d["role"], d["department"])
            QMessageBox.information(dlg, "Created", "User account created successfully.")
            dlg.accept(); self._load_user_mgmt()

        dlg.ok_btn.clicked.connect(_save)
        dlg.exec()

    def _edit_user(self):
        uid = self.view.user_mgmt_page.get_selected_id()
        if uid is None:
            QMessageBox.warning(self.view, "Select", "Select a user first.")
            return
        user = UserModel.get_by_id(uid)
        from views.admin_view import UserDialog
        dlg = UserDialog("Edit User", self.view)
        dlg.load(user)

        def _save():
            d = dlg.get_data()
            if not d["full_name"] or not d["email"]:
                QMessageBox.warning(dlg, "Validation", "Name and email are required.")
                return
            if not _valid_email(d["email"]):
                QMessageBox.warning(dlg, "Invalid Email",
                                    "Please enter a valid email address.\n"
                                    "Example: user@hotel.com")
                return
            if d["password"] and d["password"] != d["password2"]:
                QMessageBox.warning(dlg, "Validation", "Passwords do not match.")
                return
            if UserModel.email_exists(d["email"], exclude_id=uid):
                QMessageBox.warning(dlg, "Validation", "Email already used by another account.")
                return
            UserModel.update(uid, d["full_name"], d["email"], d["role"], d["department"])
            if d["password"]:
                UserModel.update_password(uid, d["password"])
            QMessageBox.information(dlg, "Saved", "User updated successfully.")
            dlg.accept(); self._load_user_mgmt()

        dlg.ok_btn.clicked.connect(_save)
        dlg.exec()

    def _delete_user(self):
        uid = self.view.user_mgmt_page.get_selected_id()
        if uid is None:
            QMessageBox.warning(self.view, "Select", "Select a user first.")
            return
        if uid == self.user["id"]:
            QMessageBox.warning(self.view, "Error", "You cannot delete your own account.")
            return
        user = UserModel.get_by_id(uid)
        reply = QMessageBox.question(
            self.view, "Delete User",
            f"Delete '{user['full_name']}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            UserModel.delete(uid); self._load_user_mgmt()

    def _reset_password(self):
        uid = self.view.user_mgmt_page.get_selected_id()
        if uid is None:
            QMessageBox.warning(self.view, "Select", "Select a user first.")
            return
        user = UserModel.get_by_id(uid)
        new_pw, ok = QInputDialog.getText(
            self.view, "Reset Password",
            f"New password for {user['full_name']}:",
            QLineEdit.EchoMode.Password,
        )
        if ok and new_pw.strip():
            UserModel.update_password(uid, new_pw.strip())
            QMessageBox.information(self.view, "Done", "Password reset successfully.")
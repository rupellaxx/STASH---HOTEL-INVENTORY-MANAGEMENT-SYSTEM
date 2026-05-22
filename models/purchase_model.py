"""
models/purchase_model.py
"""
from models.database import fetch_all, fetch_one, execute_query

class PurchaseModel:

    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all("""
            SELECT p.id, p.created_at, COALESCE(s.name,'N/A') AS supplier,
                   p.created_by, p.expected_date,
                   (SELECT COUNT(*) FROM purchase_items pi WHERE pi.purchase_id=p.id) AS item_count,
                   p.total_amount, p.status, p.supplier_id
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            ORDER BY p.created_at DESC
        """)

    @staticmethod
    def get_pending_purchases() -> list[dict]:
        """Purchase orders not yet delivered."""
        return fetch_all("""
            SELECT p.id, p.created_at, COALESCE(s.name,'N/A') AS supplier,
                   p.created_by, p.total_amount, p.status
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE p.status='pending' ORDER BY p.created_at DESC
        """)

    @staticmethod
    def get_by_id(purchase_id: int) -> dict | None:
        return fetch_one("""
            SELECT p.*, COALESCE(s.name,'N/A') AS supplier_name,
                   s.contact_name AS supplier_contact, s.email AS supplier_email
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE p.id=%s
        """, (purchase_id,))

    @staticmethod
    def get_approved() -> list[dict]:
        """Returns delivered purchases (formerly 'approved') for damage reporting."""
        return fetch_all("""
            SELECT p.id, p.created_at, COALESCE(s.name,'N/A') AS supplier,
                   p.created_by, p.total_amount, p.status
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE p.status='delivered' ORDER BY p.created_at DESC
        """)

    @staticmethod
    def get_for_owner() -> list[dict]:
        return fetch_all("""
            SELECT p.id, p.created_at, COALESCE(s.name,'N/A') AS supplier,
                   p.created_by, p.expected_date, p.total_amount, p.status
            FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
            ORDER BY p.created_at DESC
        """)

    @staticmethod
    def get_items(purchase_id: int) -> list[dict]:
        return fetch_all("SELECT * FROM purchase_items WHERE purchase_id=%s", (purchase_id,))

    @staticmethod
    def get_pending_items(purchase_id: int) -> list[dict]:
        return fetch_all(
            "SELECT * FROM purchase_items WHERE purchase_id=%s AND in_inventory=0",
            (purchase_id,)
        )

    @staticmethod
    def create(supplier_id: int, expected_date, total_amount: float, created_by: str) -> int:
        return execute_query(
            "INSERT INTO purchases (supplier_id, expected_date, total_amount, status, created_by) "
            "VALUES (%s,%s,%s,'pending',%s)",
            (supplier_id, expected_date, total_amount, created_by),
        )

    @staticmethod
    def deliver(purchase_id: int) -> None:
        execute_query("UPDATE purchases SET status='delivered' WHERE id=%s", (purchase_id,))

    @staticmethod
    def reject(purchase_id: int) -> None:
        execute_query("UPDATE purchases SET status='rejected' WHERE id=%s", (purchase_id,))

    @staticmethod
    def add_item(purchase_id: int, item_name: str, item_id: int,
                 quantity: int, unit_price: float, total: float) -> int:
        return execute_query(
            "INSERT INTO purchase_items (purchase_id,item_name,item_id,quantity,unit_price,total) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (purchase_id, item_name, item_id, quantity, unit_price, total),
        )

    @staticmethod
    def mark_item_in_inventory(pi_id: int, qty: int) -> None:
        execute_query(
            "UPDATE purchase_items SET in_inventory=1, qty_added_to_inventory=%s WHERE id=%s",
            (qty, pi_id),
        )
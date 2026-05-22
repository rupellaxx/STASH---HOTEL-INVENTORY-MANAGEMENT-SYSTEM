"""
models/damage_model.py
"""
from models.database import fetch_all, fetch_one, execute_query

class DamageModel:

    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all("""
            SELECT d.*, i.name AS item_name, COALESCE(s.name,'N/A') AS supplier_name
            FROM damages d
            JOIN items i ON d.item_id=i.id
            LEFT JOIN purchases p ON d.purchase_id=p.id
            LEFT JOIN suppliers s ON p.supplier_id=s.id
            ORDER BY d.created_at DESC
        """)

    @staticmethod
    def get_total_count() -> int:
        row = fetch_one("SELECT COUNT(*) AS cnt FROM damages")
        return int(row["cnt"]) if row else 0

    @staticmethod
    def create(item_id: int, quantity: int, category: str, reason: str,
               created_by: str, purchase_id: int = None) -> int:
        return execute_query(
            "INSERT INTO damages (item_id, purchase_id, quantity, category, reason, status, created_by) "
            "VALUES (%s,%s,%s,%s,%s,'reported',%s)",
            (item_id, purchase_id, quantity, category or "General", reason, created_by),
        )

    @staticmethod
    def resolve(damage_id: int) -> None:
        execute_query("UPDATE damages SET status='resolved' WHERE id=%s", (damage_id,))
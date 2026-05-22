"""
models/item_model.py
"""
from models.database import fetch_all, fetch_one, execute_query

_SKU_PREFIX = {
    "General": "GEN", "Housekeeping": "HK", "Dining": "DI",
    "Maintenance": "MT", "Laundry": "LA", "Front Office": "FO", "Security": "SEC",
}

class ItemModel:

    @staticmethod
    def generate_sku(category: str) -> str:
        prefix = _SKU_PREFIX.get(category, "GEN")
        row = fetch_one("SELECT COUNT(*) AS cnt FROM items WHERE sku LIKE %s", (f"{prefix}-%",))
        count = (int(row["cnt"]) if row else 0) + 1
        return f"{prefix}-{count:03d}"

    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all("SELECT * FROM items ORDER BY name")

    @staticmethod
    def get_by_id(item_id: int) -> dict | None:
        return fetch_one("SELECT * FROM items WHERE id = %s", (item_id,))

    @staticmethod
    def get_by_name(name: str) -> dict | None:
        return fetch_one("SELECT * FROM items WHERE name = %s", (name,))

    @staticmethod
    def get_by_department(department: str) -> list[dict]:
        return fetch_all("SELECT * FROM items WHERE category = %s ORDER BY name", (department,))

    @staticmethod
    def get_low_stock() -> list[dict]:
        return fetch_all(
            "SELECT *, (min_stock - stock_qty) AS deficit "
            "FROM items WHERE stock_qty < min_stock ORDER BY deficit DESC"
        )

    @staticmethod
    def get_total_value() -> float:
        row = fetch_one("SELECT COALESCE(SUM(unit_cost * stock_qty), 0) AS val FROM items")
        return float(row["val"]) if row else 0.0

    @staticmethod
    def get_total_count() -> int:
        row = fetch_one("SELECT COUNT(*) AS cnt FROM items")
        return int(row["cnt"]) if row else 0

    @staticmethod
    def get_categories() -> list[str]:
        rows = fetch_all("SELECT DISTINCT category FROM items ORDER BY category")
        return [r["category"] for r in rows]

    @staticmethod
    def get_stock_health() -> str:
        total = fetch_one("SELECT COUNT(*) cnt FROM items")
        ok    = fetch_one("SELECT COUNT(*) cnt FROM items WHERE stock_qty >= min_stock")
        t = int(total["cnt"]) if total else 0
        o = int(ok["cnt"]) if ok else 0
        pct = int((o / t) * 100) if t else 0
        return f"{pct}%"

    @staticmethod
    def create(name: str, unit: str, unit_cost: float, min_stock: int, category: str) -> int:
        sku = ItemModel.generate_sku(category)
        return execute_query(
            "INSERT INTO items (name, sku, unit, unit_cost, stock_qty, min_stock, category) "
            "VALUES (%s, %s, %s, %s, 0, %s, %s)",
            (name, sku, unit, unit_cost, min_stock, category),
        )

    @staticmethod
    def adjust_stock(item_id: int, delta: int) -> None:
        execute_query("UPDATE items SET stock_qty = stock_qty + %s WHERE id = %s", (delta, item_id))

    @staticmethod
    def delete(item_id: int) -> None:
        execute_query("DELETE FROM items WHERE id = %s", (item_id,))
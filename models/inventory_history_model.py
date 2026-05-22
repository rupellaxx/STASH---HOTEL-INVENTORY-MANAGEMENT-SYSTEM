"""
models/inventory_history_model.py
──────────────────────────────────
Database operations for the `inventory_history` table.
Pure data access – logs every stock movement.
"""

from models.database import fetch_all, fetch_one, execute_query


class InventoryHistoryModel:

    @staticmethod
    def get_all(limit: int = 300) -> list[dict]:
        return fetch_all(
            "SELECT * FROM inventory_history "
            "ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )

    @staticmethod
    def get_by_department(department: str) -> list[dict]:
        return fetch_all(
            "SELECT * FROM inventory_history "
            "WHERE department = %s ORDER BY created_at DESC",
            (department,),
        )

    @staticmethod
    def get_movement_summary() -> list[dict]:
        """Used for the pie-chart in Reports."""
        return fetch_all(
            "SELECT movement_type, SUM(quantity) AS total "
            "FROM inventory_history GROUP BY movement_type"
        )

    @staticmethod
    def get_dept_consumption(department: str) -> list[dict]:
        """Items distributed/used by a specific department."""
        return fetch_all(
            "SELECT item_name, SUM(quantity) AS total_used "
            "FROM inventory_history "
            "WHERE department = %s AND movement_type = 'distributed' "
            "GROUP BY item_name ORDER BY total_used DESC",
            (department,),
        )

    @staticmethod
    def log(item_name: str, movement_type: str, quantity: int,
            user_name: str, notes: str = None,
            department: str = None) -> None:
        """
        Insert one movement record.
        movement_type values: stock_in | distributed | adjustment | damage
        """
        execute_query(
            "INSERT INTO inventory_history "
            "(item_name, movement_type, quantity, user_name, notes, department) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (item_name, movement_type, quantity, user_name, notes, department),
        )
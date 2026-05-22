"""
models/request_model.py
───────────────────────
Database operations for the `requests` table.  Pure data access.
"""

from models.database import fetch_all, fetch_one, execute_query

# ── One-time column check so old databases don't crash ────────────────────────
_HAS_IS_NEW_ITEM = None   # None = not yet checked

def _has_is_new_item_column():
    """Return True if the requests table has the is_new_item column."""
    global _HAS_IS_NEW_ITEM
    if _HAS_IS_NEW_ITEM is None:
        try:
            from models.database import fetch_one as _fo
            row = _fo(
                "SELECT COUNT(*) AS cnt "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "  AND TABLE_NAME  = 'requests' "
                "  AND COLUMN_NAME = 'is_new_item'"
            )
            _HAS_IS_NEW_ITEM = bool(row and int(row["cnt"]) > 0)
        except Exception:
            _HAS_IS_NEW_ITEM = False
    return _HAS_IS_NEW_ITEM


class RequestModel:

    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all("SELECT * FROM requests ORDER BY created_at DESC")

    @staticmethod
    def complete(request_id: int) -> None:
        execute_query(
            "UPDATE requests SET status = 'Completed', notes = %s WHERE id = %s",
            ("Fulfilled via purchase order", request_id),
        )

    @staticmethod
    def get_by_department(department: str) -> list[dict]:
        return fetch_all(
            "SELECT * FROM requests WHERE department = %s ORDER BY created_at DESC",
            (department,),
        )

    @staticmethod
    def get_pending() -> list[dict]:
        return fetch_all(
            "SELECT * FROM requests WHERE status = 'Pending' ORDER BY created_at DESC"
        )

    @staticmethod
    def get_by_id(request_id: int) -> dict | None:
        return fetch_one("SELECT * FROM requests WHERE id = %s", (request_id,))

    @staticmethod
    def create(department: str, requested_by: str, item_name: str,
               quantity: int, unit: str, reason: str,
               is_new_item: bool = False) -> int:
        if _has_is_new_item_column():
            return execute_query(
                "INSERT INTO requests "
                "(department, requested_by, item_name, quantity, unit, "
                " reason, status, is_new_item) "
                "VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s)",
                (department, requested_by, item_name, quantity, unit, reason,
                 1 if is_new_item else 0),
            )
        else:
            # Old database without the column — insert without it
            return execute_query(
                "INSERT INTO requests "
                "(department, requested_by, item_name, quantity, unit, reason, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                (department, requested_by, item_name, quantity, unit, reason),
            )

    @staticmethod
    def update_status(request_id: int, status: str, notes: str = "") -> None:
        execute_query(
            "UPDATE requests SET status = %s, notes = %s WHERE id = %s",
            (status, notes, request_id),
        )

    @staticmethod
    def delete(request_id: int) -> None:
        execute_query("DELETE FROM requests WHERE id = %s", (request_id,))
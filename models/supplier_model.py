"""
models/supplier_model.py
────────────────────────
Database operations for the `suppliers` table.  Pure data access.
"""

from models.database import fetch_all, fetch_one, execute_query


class SupplierModel:

    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all("SELECT * FROM suppliers ORDER BY name")

    @staticmethod
    def get_by_id(supplier_id: int) -> dict | None:
        return fetch_one("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))

    @staticmethod
    def create(name: str, contact_name: str, email: str,
               phone: str, address: str) -> int:
        return execute_query(
            "INSERT INTO suppliers (name, contact_name, email, phone, address) "
            "VALUES (%s, %s, %s, %s, %s)",
            (name, contact_name, email, phone, address),
        )

    @staticmethod
    def update(supplier_id: int, name: str, contact_name: str,
               email: str, phone: str, address: str) -> None:
        execute_query(
            "UPDATE suppliers SET name=%s, contact_name=%s, email=%s, "
            "phone=%s, address=%s WHERE id=%s",
            (name, contact_name, email, phone, address, supplier_id),
        )

    @staticmethod
    def delete(supplier_id: int) -> None:
        execute_query("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
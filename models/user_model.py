"""
models/user_model.py
────────────────────
All database operations that touch the `users` table.
No UI logic whatsoever – pure data access.
"""

from models.database import fetch_all, fetch_one, execute_query, hash_password


class UserModel:

    # ── Read ──────────────────────────────────────────────────────────────────
    @staticmethod
    def get_all() -> list[dict]:
        return fetch_all(
            "SELECT id, full_name, email, role, department, created_at "
            "FROM users ORDER BY full_name"
        )

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        return fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))

    @staticmethod
    def verify_login(email: str, plain_password: str) -> dict | None:
        """
        Hashes *plain_password* with hashlib (SHA-256) then compares
        against the stored hash.  Returns the user row or None.
        """
        hashed = hash_password(plain_password)
        return fetch_one(
            "SELECT * FROM users WHERE email = %s AND password = %s",
            (email, hashed),
        )

    @staticmethod
    def email_exists(email: str, exclude_id: int = None) -> bool:
        if exclude_id:
            row = fetch_one(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (email, exclude_id),
            )
        else:
            row = fetch_one("SELECT id FROM users WHERE email = %s", (email,))
        return row is not None

    # ── Write ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create(full_name: str, email: str, plain_password: str,
               role: str, department: str | None) -> int:
        hashed = hash_password(plain_password)
        return execute_query(
            "INSERT INTO users (full_name, email, password, role, department) "
            "VALUES (%s, %s, %s, %s, %s)",
            (full_name, email, hashed, role, department),
        )

    @staticmethod
    def update(user_id: int, full_name: str, email: str,
               role: str, department: str | None) -> None:
        execute_query(
            "UPDATE users SET full_name=%s, email=%s, role=%s, department=%s "
            "WHERE id = %s",
            (full_name, email, role, department, user_id),
        )

    @staticmethod
    def update_password(user_id: int, plain_password: str) -> None:
        hashed = hash_password(plain_password)
        execute_query(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed, user_id),
        )

    @staticmethod
    def delete(user_id: int) -> None:
        execute_query("DELETE FROM users WHERE id = %s", (user_id,))

    # ── Utility ───────────────────────────────────────────────────────────────
    @staticmethod
    def get_all_for_messaging(exclude_id: int) -> list[dict]:
        """Return id, full_name, role for all users except *exclude_id*."""
        return fetch_all(
            "SELECT id, full_name, role FROM users "
            "WHERE id != %s ORDER BY full_name",
            (exclude_id,),
        )
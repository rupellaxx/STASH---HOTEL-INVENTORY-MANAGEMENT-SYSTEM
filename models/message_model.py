"""
models/message_model.py
"""
from models.database import fetch_all, fetch_one, execute_query

class MessageModel:

    @staticmethod
    def get_for_user(user_id: int) -> list[dict]:
        return fetch_all("""
            SELECT m.id, us.full_name AS sender, ur.full_name AS recipient,
                   m.category, m.title, m.body, m.is_read, m.created_at,
                   m.sender_id, m.recipient_id
            FROM messages m
            JOIN users us ON m.sender_id=us.id
            JOIN users ur ON m.recipient_id=ur.id
            WHERE m.recipient_id=%s OR m.sender_id=%s
            ORDER BY m.created_at DESC
        """, (user_id, user_id))

    @staticmethod
    def get_by_id(message_id: int) -> dict | None:
        return fetch_one("""
            SELECT m.*, us.full_name AS sender_name, ur.full_name AS recipient_name
            FROM messages m
            JOIN users us ON m.sender_id=us.id
            JOIN users ur ON m.recipient_id=ur.id
            WHERE m.id=%s
        """, (message_id,))

    @staticmethod
    def unread_count(user_id: int) -> int:
        row = fetch_one(
            "SELECT COUNT(*) AS cnt FROM messages WHERE recipient_id=%s AND is_read=0",
            (user_id,)
        )
        return int(row["cnt"]) if row else 0

    @staticmethod
    def create(sender_id: int, recipient_id: int, category: str, title: str, body: str) -> int:
        return execute_query(
            "INSERT INTO messages (sender_id, recipient_id, category, title, body) "
            "VALUES (%s,%s,%s,%s,%s)",
            (sender_id, recipient_id, category, title, body),
        )

    @staticmethod
    def mark_read(message_id: int) -> None:
        execute_query("UPDATE messages SET is_read=1 WHERE id=%s", (message_id,))

    @staticmethod
    def delete(message_id: int) -> None:
        execute_query("DELETE FROM messages WHERE id=%s", (message_id,))
import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)


def seed_default_owner(conn: Connection) -> None:
    """Дефолтный владелец (идемпотентно по id).

    Если users.id=1 уже существует — ничего не делаем: логин обновляется
    позже в onboarding_complete / get_current_user под активного пользователя.
    """
    existing = conn.execute(
        text("SELECT username FROM users WHERE id = 1")
    ).fetchone()
    if existing is not None:
        return

    conn.execute(
        text(
            "INSERT INTO users (id, username, password_hash, is_active) "
            "VALUES (1, 'owner', '', 1)"
        )
    )


def _column_exists(conn: Connection, table: str, column: str) -> bool:
    """Проверяет наличие колонки в таблице (для схем-независимого сида)."""
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return any(row[1] == column for row in rows)


def seed_default_folders(conn: Connection) -> None:
    """Системные папки контактов IziBox (идемпотентно по category_key).

    Таксономия: папки принадлежат типам (contact_type), под-папки — parent_id.
    """
    defaults = [
        ("Семья", "#ec4899", 1, "family", "personal"),
        ("Друзья", "#8b5cf6", 2, "friends", "personal"),
        ("Группы", "#6366f1", 3, "groups", "personal"),
        ("Каналы", "#0ea5e9", 1, "channels", "needed"),
        ("Сервисные", "#10b981", 2, "service", "needed"),
    ]
    has_type = _column_exists(conn, "contact_folders", "contact_type")
    for name, color, sort_order, category_key, contact_type in defaults:
        conn.execute(
            text(
                "INSERT OR IGNORE INTO contact_folders "
                "(owner_id, name, color, sort_order, is_default, category_key) "
                "VALUES (1, :name, :color, :sort_order, 1, :category_key)"
            ),
            {
                "name": name,
                "color": color,
                "sort_order": sort_order,
                "category_key": category_key,
            },
        )
        if has_type:
            conn.execute(
                text(
                    "UPDATE contact_folders SET contact_type = :contact_type "
                    "WHERE category_key = :category_key AND owner_id = 1"
                ),
                {"category_key": category_key, "contact_type": contact_type},
            )

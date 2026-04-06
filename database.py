import sqlite3
import os

DB_PATH = "bot_data.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER REFERENCES buttons(id) ON DELETE CASCADE,
            type TEXT NOT NULL CHECK(type IN ('menu', 'text', 'photo', 'file', 'video', 'audio')),
            label TEXT NOT NULL,
            content TEXT,
            file_id TEXT,
            order_num INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def is_admin(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


def add_admin(user_id: int, username: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()
    conn.close()


def remove_admin(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_admins():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins ORDER BY added_at")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_buttons(parent_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if parent_id is None:
        cur.execute(
            "SELECT * FROM buttons WHERE parent_id IS NULL ORDER BY order_num, id"
        )
    else:
        cur.execute(
            "SELECT * FROM buttons WHERE parent_id = ? ORDER BY order_num, id",
            (parent_id,)
        )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_button(button_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_button(parent_id, btn_type, label, content=None, file_id=None, created_by=None):
    conn = get_connection()
    cur = conn.cursor()
    if parent_id is None:
        cur.execute("SELECT COALESCE(MAX(order_num), 0) + 1 FROM buttons WHERE parent_id IS NULL")
    else:
        cur.execute("SELECT COALESCE(MAX(order_num), 0) + 1 FROM buttons WHERE parent_id = ?", (parent_id,))
    order_num = cur.fetchone()[0]

    cur.execute(
        """INSERT INTO buttons (parent_id, type, label, content, file_id, order_num, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (parent_id, btn_type, label, content, file_id, order_num, created_by)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_button(button_id: int, label=None, content=None, file_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if label is not None:
        cur.execute("UPDATE buttons SET label = ? WHERE id = ?", (label, button_id))
    if content is not None:
        cur.execute("UPDATE buttons SET content = ? WHERE id = ?", (content, button_id))
    if file_id is not None:
        cur.execute("UPDATE buttons SET file_id = ? WHERE id = ?", (file_id, button_id))
    conn.commit()
    conn.close()


def delete_button(button_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM buttons WHERE id = ?", (button_id,))
    conn.commit()
    conn.close()


def move_button(button_id: int, direction: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
    btn = cur.fetchone()
    if not btn:
        conn.close()
        return

    if btn["parent_id"] is None:
        cur.execute(
            "SELECT * FROM buttons WHERE parent_id IS NULL ORDER BY order_num, id"
        )
    else:
        cur.execute(
            "SELECT * FROM buttons WHERE parent_id = ? ORDER BY order_num, id",
            (btn["parent_id"],)
        )
    siblings = cur.fetchall()
    ids = [s["id"] for s in siblings]

    try:
        idx = ids.index(button_id)
    except ValueError:
        conn.close()
        return

    if direction == "up" and idx > 0:
        swap_id = ids[idx - 1]
    elif direction == "down" and idx < len(ids) - 1:
        swap_id = ids[idx + 1]
    else:
        conn.close()
        return

    cur.execute("SELECT order_num FROM buttons WHERE id = ?", (button_id,))
    o1 = cur.fetchone()["order_num"]
    cur.execute("SELECT order_num FROM buttons WHERE id = ?", (swap_id,))
    o2 = cur.fetchone()["order_num"]

    cur.execute("UPDATE buttons SET order_num = ? WHERE id = ?", (o2, button_id))
    cur.execute("UPDATE buttons SET order_num = ? WHERE id = ?", (o1, swap_id))
    conn.commit()
    conn.close()

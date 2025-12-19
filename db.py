import sqlite3
from pathlib import Path

DB_PATH = Path("/data/round_robin.db")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS round_robin (
            group_id INTEGER PRIMARY KEY,
            last_user_id INTEGER
        )
        """)
        conn.commit()

def get_last_user(group_id: int):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT last_user_id FROM round_robin WHERE group_id = ?",
            (group_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None

def set_last_user(group_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO round_robin (group_id, last_user_id)
        VALUES (?, ?)
        ON CONFLICT(group_id)
        DO UPDATE SET last_user_id = excluded.last_user_id
        """, (group_id, user_id))
        conn.commit()


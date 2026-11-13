import sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=20)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS chats(
              chat_id INTEGER PRIMARY KEY,
              gcast_enabled INTEGER NOT NULL DEFAULT 1,
              spam_enabled INTEGER NOT NULL DEFAULT 1,
              window_seconds INTEGER NOT NULL DEFAULT 10,
              message_limit INTEGER NOT NULL DEFAULT 6,
              warn_limit INTEGER NOT NULL DEFAULT 3,
              mute_minutes INTEGER NOT NULL DEFAULT 10
            );
            CREATE TABLE IF NOT EXISTS whitelist(
              chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
              PRIMARY KEY(chat_id,user_id)
            );
            CREATE TABLE IF NOT EXISTS warnings(
              chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
              count INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY(chat_id,user_id)
            );
            CREATE TABLE IF NOT EXISTS violations(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
              reason TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """)

    def ensure_chat(self, chat_id, cfg):
        with self.connect() as c:
            c.execute("""INSERT OR IGNORE INTO chats
              (chat_id,window_seconds,message_limit,warn_limit,mute_minutes)
              VALUES(?,?,?,?,?)""",
              (chat_id,cfg.default_window,cfg.default_limit,cfg.warn_limit,cfg.mute_minutes))

    def settings(self, chat_id):
        with self.connect() as c:
            return c.execute("SELECT * FROM chats WHERE chat_id=?", (chat_id,)).fetchone()

    def set_flag(self, chat_id, column, enabled):
        if column not in ("gcast_enabled", "spam_enabled"):
            raise ValueError("Invalid setting")
        with self.connect() as c:
            c.execute(f"UPDATE chats SET {column}=? WHERE chat_id=?", (int(enabled), chat_id))

    def set_limit(self, chat_id, limit):
        with self.connect() as c:
            c.execute("UPDATE chats SET message_limit=? WHERE chat_id=?", (limit, chat_id))

    def is_whitelisted(self, chat_id, user_id):
        with self.connect() as c:
            return c.execute("SELECT 1 FROM whitelist WHERE chat_id=? AND user_id=?",
                             (chat_id,user_id)).fetchone() is not None

    def add_whitelist(self, chat_id, user_id):
        with self.connect() as c:
            c.execute("INSERT OR IGNORE INTO whitelist VALUES(?,?)", (chat_id,user_id))

    def remove_whitelist(self, chat_id, user_id):
        with self.connect() as c:
            cur = c.execute("DELETE FROM whitelist WHERE chat_id=? AND user_id=?", (chat_id,user_id))
            return cur.rowcount

    def add_warning(self, chat_id, user_id, reason):
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as c:
            c.execute("""INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,1)
              ON CONFLICT(chat_id,user_id) DO UPDATE SET count=count+1""", (chat_id,user_id))
            count = c.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
                              (chat_id,user_id)).fetchone()["count"]
            c.execute("INSERT INTO violations(chat_id,user_id,reason,created_at) VALUES(?,?,?,?)",
                      (chat_id,user_id,reason,now))
            return count

    def clear_warnings(self, chat_id, user_id):
        with self.connect() as c:
            c.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat_id,user_id))

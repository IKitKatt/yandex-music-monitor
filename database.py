import sqlite3
import threading
import logging
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_path: str = "data/monitor.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subscriber_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    count INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_count(self, count: int):
        with self.lock:
            with self._get_connection() as conn:
                conn.execute(
                    'INSERT INTO subscriber_counts (count, timestamp) VALUES (?, ?)',
                    (count, datetime.now().isoformat())
                )
                conn.commit()
        self.logger.debug(f"Saved count {count} to database")

    def get_stats(self, days: int):
        """Returns (first_count, last_count) for the given period, or (None, None) if no data."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            first_row = conn.execute(
                'SELECT count FROM subscriber_counts WHERE timestamp >= ? ORDER BY timestamp ASC LIMIT 1',
                (since,)
            ).fetchone()
            last_row = conn.execute(
                'SELECT count FROM subscriber_counts WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 1',
                (since,)
            ).fetchone()
        if first_row and last_row:
            return first_row['count'], last_row['count']
        return None, None

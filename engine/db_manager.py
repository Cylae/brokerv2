import sqlite3
import logging
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="trading_history.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    action TEXT,
                    quantity INTEGER,
                    price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    reason TEXT,
                    order_id INTEGER
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    def log_trade(self, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id):
        """Log a trade to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO trades (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id))

            conn.commit()
            conn.close()
            self.logger.info(f"Trade logged to DB: {action} {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")

    def get_recent_trades(self, limit=10):
        """Fetch recent trades."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trades ORDER BY id DESC LIMIT ?', (limit,))
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            self.logger.error(f"Failed to fetch trades: {e}")
            return []

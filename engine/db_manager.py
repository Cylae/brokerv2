import sqlite3
import logging
from datetime import datetime
import os
import asyncio
import threading

class DatabaseManager:
    def __init__(self, db_path="trading_history.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # Open persistent connection for synchronous operations.
        # check_same_thread=False allows us to pass it between executor threads safely,
        # but we MUST lock access using self._lock to prevent concurrent execution.
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._init_db()
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            self.conn = None

    def _init_db(self):
        """Initialize the database schema."""
        if not self.conn:
            return
        try:
            with self._lock:
                cursor = self.conn.cursor()
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
                self.conn.commit()
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    def _log_trade_sync(self, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id):
        """Log a trade to the database (synchronous)."""
        if not self.conn:
            return
        try:
            timestamp = datetime.now().isoformat()
            with self._lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO trades (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id))

                self.conn.commit()
            self.logger.info(f"Trade logged to DB: {action} {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")

    async def log_trade(self, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id):
        """Log a trade to the database (asynchronous)."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self._log_trade_sync,
            symbol, action, quantity, price, stop_loss, take_profit, reason, order_id
        )

    def _get_recent_trades_sync(self, limit=10):
        """Fetch recent trades (synchronous)."""
        if not self.conn:
            return []
        try:
            with self._lock:
                self.conn.row_factory = sqlite3.Row
                cursor = self.conn.cursor()
                cursor.execute('SELECT * FROM trades ORDER BY id DESC LIMIT ?', (limit,))
                rows = [dict(row) for row in cursor.fetchall()]
            return rows
        except Exception as e:
            self.logger.error(f"Failed to fetch trades: {e}")
            return []

    def close(self):
        if self.conn:
            with self._lock:
                self.conn.close()
                self.conn = None

    async def get_recent_trades(self, limit=10):
        """Fetch recent trades (asynchronous)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_recent_trades_sync, limit)

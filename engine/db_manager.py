import sqlite3
import logging
from datetime import datetime
import os
import asyncio

class DatabaseManager:
    def __init__(self, db_path="trading_history.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    def _log_trade_sync(self, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id):
        """Log a trade to the database (synchronous)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()

                cursor.execute('''
                    INSERT INTO trades (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, symbol, action, quantity, price, stop_loss, take_profit, reason, order_id))

                conn.commit()
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
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM trades ORDER BY id DESC LIMIT ?', (limit,))
                rows = [dict(row) for row in cursor.fetchall()]
                return rows
        except Exception as e:
            self.logger.error(f"Failed to fetch trades: {e}")
            return []

    def close(self):
        """Provides a safe close method to satisfy graceful shutdown expectations."""
        pass # No persistent connection maintained in this refactored version

    async def get_recent_trades(self, limit=10):
        """Fetch recent trades (asynchronous)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_recent_trades_sync, limit)

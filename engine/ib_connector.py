from ib_insync import IB, util
import logging
import asyncio

class IBConnector:
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connects to the IB Gateway or TWS."""
        if not self.ib.isConnected():
            try:
                self.logger.info(f"Connecting to IBKR at {self.host}:{self.port} with client ID {self.client_id}...")
                await self.ib.connectAsync(self.host, self.port, self.client_id)
                self.connected = True
                self.logger.info("Connected to IBKR.")
            except Exception as e:
                self.logger.error(f"Failed to connect to IBKR: {e}")
                self.connected = False
                raise
        else:
            self.logger.info("Already connected to IBKR.")
            self.connected = True

    def disconnect(self):
        """Disconnects from IBKR."""
        if self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from IBKR.")

    def get_ib_instance(self):
        """Returns the IB instance."""
        return self.ib

    async def check_connection(self):
        """Checks if the connection is still active."""
        return self.ib.isConnected()

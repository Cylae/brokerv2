import asyncio
import logging
import argparse
import sys
import os

from engine.trading_engine import TradingEngine
from engine.risk_manager import RiskManager
from engine.db_manager import DatabaseManager
from engine.market_utils import MarketSchedule
from engine.notifier import Notifier
from ai.ai_wrapper import AIWrapper
from config import Config

# Connectors
from engine.ib_connector import IBKRConnector
from engine.binance_connector import BinanceConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def run_trading_cycle(engine, risk_manager, ai, db, notifier, symbols):
    if not MarketSchedule.is_market_open():
        logger.info("Market is CLOSED. Skipping analysis.")
        return

    for symbol in symbols:
        logger.info(f"--- Analyzing {symbol} ---")
        market_data = await engine.get_market_data(symbol)

        if not market_data:
            logger.error(f"Failed to fetch market data for {symbol}")
            continue

        logger.info(f"Market Data: {market_data}")

        decision = ai.analyze_and_decide(market_data)

        if decision:
            logger.info(f"AI Decision: {decision['decision']} with args {decision['args']}")

            cmd = decision['decision']
            args = decision['args']

            try:
                # Basic Normalization for verification logic
                dec_symbol = args['symbol'].upper().replace('/', '')
                target_symbol = symbol.upper().replace('/', '')

                if cmd == 'buy_stock':
                    # Validate symbol matches
                    if dec_symbol not in target_symbol and target_symbol not in dec_symbol:
                        logger.warning(f"AI tried to buy {args['symbol']} but we are analyzing {symbol}. Ignoring mismatch.")
                        continue

                    # Risk Check
                    price = market_data['last']
                    stop_loss = args.get('stop_loss')
                    take_profit = args.get('take_profit')
                    quantity = args['quantity']
                    reason = args.get('reason', 'No reason')

                    valid, validation_msg = await risk_manager.validate_trade(
                        symbol, quantity, price, 'BUY', stop_loss
                    )

                    if not valid:
                        logger.warning(f"Risk Manager Rejected Trade: {validation_msg}")
                        continue

                    trade = await engine.execute_order(
                        symbol, 'BUY', quantity, 'MKT', # Use original symbol
                        stop_loss=stop_loss, take_profit=take_profit
                    )

                    # Get Order ID
                    order_id = 0
                    if hasattr(trade, 'order') and hasattr(trade.order, 'orderId'):
                        order_id = trade.order.orderId
                    elif hasattr(trade, 'id'): # Generic object from Binance
                         order_id = trade.id

                    # Log to DB
                    db.log_trade(symbol, 'BUY', quantity, price, stop_loss, take_profit, reason, order_id)

                    # Notify
                    notifier.send_trade_alert(symbol, 'BUY', quantity, price, stop_loss, reason)

                elif cmd == 'sell_stock':
                    if dec_symbol not in target_symbol and target_symbol not in dec_symbol:
                        logger.warning(f"AI tried to sell {args['symbol']} but we are analyzing {symbol}. Ignoring mismatch.")
                        continue

                    await engine.execute_order(symbol, 'SELL', args['quantity'], 'MKT', stop_loss=args.get('stop_loss'))

                elif cmd == 'hold_position':
                    logger.info("Holding position.")

            except Exception as e:
                logger.error(f"Failed to execute order: {e}")
        else:
            logger.error("AI failed to return a decision.")

async def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading System")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "TSLA"], help="List of symbols to trade")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop")
    parser.add_argument("--mode", choices=['IBKR', 'BINANCE'], default=None, help="Trading Mode")
    args = parser.parse_args()

    # Override Config mode if arg provided
    if args.mode:
        Config.TRADING_MODE = args.mode

    # Validate Config
    try:
        Config.validate()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    logger.info(f"Starting System in {Config.TRADING_MODE} Mode")

    # Initialize Connector based on Mode
    if Config.TRADING_MODE == 'BINANCE':
        connector = BinanceConnector(
            api_key=Config.BINANCE_API_KEY,
            secret_key=Config.BINANCE_SECRET_KEY,
            testnet=Config.BINANCE_TESTNET
        )
    else:
        connector = IBKRConnector(
            host=Config.IB_HOST,
            port=Config.IB_PORT,
            client_id=Config.IB_CLIENT_ID
        )

    ai = AIWrapper(api_key=Config.OPENROUTER_API_KEY, model=Config.OPENROUTER_MODEL)
    db = DatabaseManager()
    notifier = Notifier()

    # Connection Loop
    while True:
        try:
            logger.info("Connecting to Exchange...")
            await connector.connect()
            engine = TradingEngine(connector)

            async def account_provider():
                return await engine.get_account_summary()

            risk_manager = RiskManager(account_provider)

            logger.info("System Initialized. Starting Trading Loop.")

            while True:
                if not await connector.check_connection():
                    logger.error("Connection lost. Reconnecting...")
                    break

                await run_trading_cycle(engine, risk_manager, ai, db, notifier, args.symbols)

                if not args.loop:
                    return

                logger.info("Sleeping for 60 seconds...")
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("Stopping...")
            break
        except Exception as e:
            logger.error(f"Critical Error: {e}")
            logger.info("Restarting in 10 seconds...")
            await asyncio.sleep(10)
        finally:
             await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

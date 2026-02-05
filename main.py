import asyncio
import logging
import argparse
import sys
import os

from engine.ib_connector import IBConnector
from engine.trading_engine import TradingEngine
from engine.risk_manager import RiskManager
from engine.db_manager import DatabaseManager
from engine.market_utils import MarketSchedule
from engine.notifier import Notifier
from ai.ai_wrapper import AIWrapper
from config import Config

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
    # Check Market Hours
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
                if cmd == 'buy_stock':
                    # Validate symbol matches
                    if args['symbol'].upper() != symbol.upper():
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
                        args['symbol'], 'BUY', quantity, 'MKT',
                        stop_loss=stop_loss, take_profit=take_profit
                    )

                    # Get Order ID (Note: Trade object might not have orderId immediately populated in some contexts, but usually yes)
                    order_id = trade.order.orderId

                    # Log to DB
                    db.log_trade(symbol, 'BUY', quantity, price, stop_loss, take_profit, reason, order_id)

                    # Notify
                    notifier.send_trade_alert(symbol, 'BUY', quantity, price, stop_loss, reason)

                elif cmd == 'sell_stock':
                    if args['symbol'].upper() != symbol.upper():
                        logger.warning(f"AI tried to sell {args['symbol']} but we are analyzing {symbol}. Ignoring mismatch.")
                        continue

                    # TODO: Implement full sell logic/short logic
                    await engine.execute_order(args['symbol'], 'SELL', args['quantity'], 'MKT', stop_loss=args.get('stop_loss'))

                elif cmd == 'hold_position':
                    logger.info("Holding position.")

            except Exception as e:
                logger.error(f"Failed to execute order: {e}")
        else:
            logger.error("AI failed to return a decision.")

async def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading System")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "TSLA", "NVDA"], help="List of symbols to trade")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop")
    args = parser.parse_args()

    # Validate Config
    try:
        Config.validate()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    # Initialize Components
    connector = IBConnector(host=Config.IB_HOST, port=Config.IB_PORT, client_id=Config.IB_CLIENT_ID)
    ai = AIWrapper(api_key=Config.OPENROUTER_API_KEY, model=Config.OPENROUTER_MODEL)
    db = DatabaseManager()
    notifier = Notifier()

    # Connection Loop with Backoff
    while True:
        try:
            logger.info("Connecting to IBKR...")
            await connector.connect()
            engine = TradingEngine(connector)

            # Helper to fetch account data for Risk Manager
            async def account_provider():
                return await engine.get_account_summary()

            risk_manager = RiskManager(account_provider)

            logger.info("System Initialized. Starting Trading Loop.")

            while True:
                if not await connector.check_connection():
                    logger.error("Connection lost. Reconnecting...")
                    break # Break inner loop to re-connect

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
             connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

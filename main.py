import asyncio
import logging
import argparse
import sys
import os

from engine.risk_manager import RiskManager
from engine.db_manager import DatabaseManager
from engine.market_utils import MarketSchedule
from engine.notifier import Notifier
from ai.ai_wrapper import AIWrapper
from config import Config
from engine.errors import ConnectionError, OrderError

from engine.ib_connector import IBKRConnector
from engine.ccxt_connector import CCXTConnector

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

async def analyze_symbol(engine, risk_manager, ai, db, notifier, symbol):
    logger.info(f"--- Analyzing {symbol} ---")

    try:
        # 1. Fetch Data
        market_data = await engine.get_market_data(symbol)
        if not market_data:
            logger.error(f"Failed to fetch market data for {symbol}")
            return

        logger.info(f"Market Data ({symbol}): Last {market_data.last}")

        # 2. AI Analysis
        # Adapter: Convert MarketData object to dict for AI Wrapper if needed, or update AI Wrapper.
        # AIWrapper expects dict currently. Let's convert.
        market_data_dict = {
            'symbol': market_data.symbol,
            'last': market_data.last,
            'bid': market_data.bid,
            'ask': market_data.ask,
            'volume': market_data.volume,
            'timestamp': market_data.timestamp,
            **market_data.indicators
        }

        decision = await ai.analyze_and_decide(market_data_dict)

        if not decision:
            logger.error(f"AI failed to return a decision for {symbol}.")
            return

        cmd = decision['decision']
        args = decision['args']
        logger.info(f"AI Decision ({symbol}): {cmd}")

        # 3. Execution Logic
        if cmd in ['buy_stock', 'sell_stock']:
            # Basic Symbol Validation
            dec_symbol = args['symbol'].upper().replace('/', '')
            target_symbol = symbol.upper().replace('/', '')

            if dec_symbol not in target_symbol and target_symbol not in dec_symbol:
                 logger.warning(f"Symbol Mismatch: AI={args['symbol']} vs Target={symbol}. Skipping.")
                 return

            # Risk Check
            price = market_data.last
            quantity = args['quantity']
            stop_loss = args.get('stop_loss')
            take_profit = args.get('take_profit')
            reason = args.get('reason', 'No reason')
            action = 'BUY' if cmd == 'buy_stock' else 'SELL'

            valid, validation_msg = await risk_manager.validate_trade(
                symbol, quantity, price, action, stop_loss
            )

            if not valid:
                logger.warning(f"Risk Rejected ({symbol}): {validation_msg}")
                return

            # Execute
            try:
                trade_result = await engine.execute_order(
                    symbol, action, quantity, 'MKT',
                    stop_loss=stop_loss, take_profit=take_profit
                )

                # Log & Notify
                db.log_trade(
                    symbol, action, quantity, price, stop_loss, take_profit, reason,
                    trade_result.order_id
                )
                notifier.send_trade_alert(symbol, action, quantity, price, stop_loss, reason)

            except OrderError as oe:
                logger.error(f"Order Execution Failed: {oe}")

        elif cmd == 'hold_position':
            logger.info(f"Holding {symbol}.")

    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")

async def run_trading_cycle(engine, risk_manager, ai, db, notifier, symbols):
    if not MarketSchedule.is_market_open():
        logger.info("Market is CLOSED. Skipping cycle.")
        return

    tasks = [analyze_symbol(engine, risk_manager, ai, db, notifier, sym) for sym in symbols]
    await asyncio.gather(*tasks)

async def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading System")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "TSLA"], help="List of symbols")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop")
    parser.add_argument("--mode", choices=['IBKR', 'CRYPTO'], default=None, help="Trading Mode")
    parser.add_argument("--exchange", default="binance", help="Crypto Exchange (if mode=CRYPTO)")
    args = parser.parse_args()

    if args.mode: Config.TRADING_MODE = args.mode

    # New Config for Exchange
    Config.CRYPTO_EXCHANGE = args.exchange

    try:
        Config.validate()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    logger.info(f"Starting System in {Config.TRADING_MODE} Mode")

    if Config.TRADING_MODE == 'CRYPTO':
        connector = CCXTConnector(
            Config.BINANCE_API_KEY,
            Config.BINANCE_SECRET_KEY,
            exchange_id=Config.CRYPTO_EXCHANGE,
            testnet=Config.BINANCE_TESTNET
        )
    else:
        connector = IBKRConnector(Config.IB_HOST, Config.IB_PORT, Config.IB_CLIENT_ID)

    ai = AIWrapper(Config.OPENROUTER_API_KEY, Config.OPENROUTER_MODEL)
    db = DatabaseManager()
    notifier = Notifier()

    while True:
        try:
            logger.info("Connecting...")
            await connector.connect()

            async def account_provider():
                summary = await connector.get_account_summary()
                return {'NetLiquidation': summary.net_liquidation}

            risk_manager = RiskManager(account_provider)

            logger.info("System Initialized. Starting Loop.")

            while True:
                if not await connector.check_connection():
                    logger.error("Connection lost.")
                    break

                await run_trading_cycle(connector, risk_manager, ai, db, notifier, args.symbols)

                if not args.loop:
                    return

                logger.info("Sleeping for 60 seconds...")
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("Stopping...")
            break
        except Exception as e:
            logger.error(f"Critical Error: {e}")
            await asyncio.sleep(10)
        finally:
             await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

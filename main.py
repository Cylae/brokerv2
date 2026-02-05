import asyncio
import logging
import argparse
import sys
import os

from engine.ib_connector import IBConnector
from engine.trading_engine import TradingEngine
from engine.risk_manager import RiskManager
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

async def run_trading_cycle(engine, risk_manager, ai, symbols):
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

                    valid, reason = await risk_manager.validate_trade(
                        symbol, args['quantity'], price, 'BUY', stop_loss
                    )

                    if not valid:
                        logger.warning(f"Risk Manager Rejected Trade: {reason}")
                        continue

                    await engine.execute_order(
                        args['symbol'], 'BUY', args['quantity'], 'MKT',
                        stop_loss=stop_loss, take_profit=take_profit
                    )

                elif cmd == 'sell_stock':
                    if args['symbol'].upper() != symbol.upper():
                        logger.warning(f"AI tried to sell {args['symbol']} but we are analyzing {symbol}. Ignoring mismatch.")
                        continue

                    # Risk Check (Assuming Short Selling logic similar to buy for position size)
                    # For MVP, focusing on long trades primarily, but keeping structure.
                    await engine.execute_order(args['symbol'], 'SELL', args['quantity'], 'MKT')

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

    try:
        await connector.connect()
        engine = TradingEngine(connector)

        # Helper to fetch account data for Risk Manager
        async def account_provider():
            return await engine.get_account_summary()

        risk_manager = RiskManager(account_provider)

        if args.loop:
            logger.info("Starting continuous trading loop...")
            while True:
                await run_trading_cycle(engine, risk_manager, ai, args.symbols)
                logger.info("Sleeping for 60 seconds...")
                await asyncio.sleep(60)
        else:
            await run_trading_cycle(engine, risk_manager, ai, args.symbols)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        connector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

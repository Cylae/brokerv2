from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from .base_connector import BaseConnector
from .indicators import Indicators
from .models import MarketData, TradeResult, Position, AccountSummary

class IBKRConnector(BaseConnector):
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self._historical_cache = {}
        self._historical_cache_ttl = 300

    async def connect(self):
        if not self.ib.isConnected():
            try:
                self.logger.info(f"Connecting to IBKR at {self.host}:{self.port}...")
                await self.ib.connectAsync(self.host, self.port, self.client_id)
                self.connected = True
                self.logger.info("Connected to IBKR.")
            except Exception as e:
                self.logger.error(f"Failed to connect to IBKR: {e}")
                self.connected = False
                raise
        else:
            self.connected = True

    async def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from IBKR.")

    async def check_connection(self) -> bool:
        return self.ib.isConnected()

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        contract = Stock(symbol, 'SMART', 'USD')
        try:
            await self.ib.qualifyContractsAsync(contract)
        except Exception as e:
            self.logger.error(f"Could not qualify contract for {symbol}: {e}")
            return None

        # Task 1: Snapshot
        async def get_snapshot():
            ticker = self.ib.reqMktData(contract, '', False, False)
            if not (ticker.last or ticker.bid or ticker.ask):
                future = asyncio.Future()

                def on_update(tickers):
                    if ticker in tickers:
                        if ticker.last or ticker.bid or ticker.ask:
                            if not future.done():
                                future.set_result(True)

                self.ib.pendingTickersEvent += on_update
                try:
                    await asyncio.wait_for(future, timeout=1.0)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self.ib.pendingTickersEvent -= on_update
            return ticker

        current_time = asyncio.get_event_loop().time()
        cached_data = self._historical_cache.get(symbol)

        technicals = {}
        if cached_data and (current_time - cached_data['time'] < self._historical_cache_ttl):
            bars = None
            technicals = cached_data['technicals']
            get_history_coro = None
        else:
            # Task 2: History
            async def get_history():
                return await self.ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime='',
                    durationStr='10 D',
                    barSizeSetting='1 hour',
                    whatToShow='TRADES',
                    useRTH=True
                )
            get_history_coro = get_history()

        if get_history_coro:
            ticker, bars = await asyncio.gather(get_snapshot(), get_history_coro)
        else:
            ticker = await get_snapshot()

        last_price = ticker.last if ticker.last else ticker.close

        if not last_price:
             self.logger.warning(f"No market data received for {symbol}")
             return None

        if bars:
            df = util.df(bars)
            technicals = Indicators.get_technical_summary(df)
            self._historical_cache[symbol] = {
                'time': current_time,
                'technicals': technicals
            }

        return MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            last=last_price,
            bid=ticker.bid,
            ask=ticker.ask,
            volume=ticker.volume,
            indicators=technicals
        )

    async def execute_order(self, symbol: str, action: str, quantity: float, order_type: str = 'MKT', price: float = None, stop_loss: float = None, take_profit: float = None) -> TradeResult:
        contract = Stock(symbol, 'SMART', 'USD')
        await self.ib.qualifyContractsAsync(contract)

        if order_type.upper() == 'MKT':
            parent = MarketOrder(action, quantity)
        elif order_type.upper() == 'LMT':
            if price is None:
                 raise ValueError("Price needed for LMT")
            parent = LimitOrder(action, quantity, price)
        else:
            raise ValueError(f"Unknown Order Type: {order_type}")

        orders_to_place = [parent]

        if (stop_loss or take_profit) and action == 'BUY':
            parent.transmit = False
            if stop_loss:
                stop = self.ib.bracketStopOrder(parent, stop_loss)
                stop.transmit = True
                if take_profit:
                    stop.transmit = False
                orders_to_place.append(stop)
            if take_profit:
                limit = self.ib.bracketLimitOrder(parent, take_profit)
                limit.transmit = True
                orders_to_place.append(limit)

        trades = []
        for o in orders_to_place:
            t = self.ib.placeOrder(contract, o)
            trades.append(t)

        parent_trade = trades[0]
        # Note: orderId might not be populated instantly without a wait loop, but usually valid in async flow if connected.

        return TradeResult(
            order_id=str(parent_trade.order.orderId),
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            status=parent_trade.orderStatus.status
        )

    async def get_account_summary(self) -> AccountSummary:
        tags = 'NetLiquidation,TotalCashValue'
        summary = await self.ib.accountSummaryAsync()
        vals = {}
        for item in summary:
             if item.tag in tags.split(','):
                 vals[item.tag] = float(item.value)

        return AccountSummary(
            net_liquidation=vals.get('NetLiquidation', 0.0),
            total_cash=vals.get('TotalCashValue', 0.0),
            currency='USD'
        )

    async def get_positions(self) -> List[Position]:
        positions = self.ib.positions()
        pos_list = []
        for p in positions:
            pos_list.append(Position(
                symbol=p.contract.symbol,
                quantity=p.position,
                avg_cost=p.avgCost,
                current_price=0.0 # IBKR positions object doesn't have live price usually, separate lookup needed if strictly required
            ))
        return pos_list

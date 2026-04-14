import time
from typing import Optional
from .client import BinanceClient
from .logging_config import logger
from .validators import OrderSide, OrderType
from binance.exceptions import BinanceAPIException, BinanceOrderException

class OrderManager:
    def __init__(self, client: BinanceClient):
        self.client = client.get_futures_client()

    def place_market_order(self, symbol: str, side: OrderSide, quantity: float, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        try:
            logger.info(f"[REQUEST] ACTION: PLACE_ORDER | TYPE: MARKET | SIDE: {side} | QTY: {quantity} | SYMBOL: {symbol}")
            response = self.client.futures_create_order(
                symbol=symbol,
                side=str(side),
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"[RESPONSE] ID: {response.get('orderId')} | STATUS: {response.get('status')} | FILL_QTY: {response.get('executedQty')}")
            
            # Place protective orders if requested
            if stop_loss:
                self.place_stop_loss(symbol, side, quantity, stop_loss)
            if take_profit:
                self.place_take_profit(symbol, side, quantity, take_profit)
                
            return response
        except Exception as e:
            logger.error(f"[FAILURE] MARKET_ORDER | ERROR: {e}")
            raise

    def place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: Optional[float] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        try:
            logger.info(f"[REQUEST] ACTION: PLACE_ORDER | TYPE: LIMIT | SIDE: {side} | PRICE: {price} | QTY: {quantity} | SYMBOL: {symbol}")
            response = self.client.futures_create_order(
                symbol=symbol,
                side=str(side),
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            logger.info(f"[RESPONSE] ID: {response.get('orderId')} | STATUS: {response.get('status')} | LIMIT_PRICE: {response.get('price')}")
            
            # Place protective orders if requested
            if stop_loss:
                self.place_stop_loss(symbol, side, quantity, stop_loss)
            if take_profit:
                self.place_take_profit(symbol, side, quantity, take_profit)
                
            return response
        except Exception as e:
            logger.error(f"[FAILURE] LIMIT_ORDER | ERROR: {e}")
            raise

    def place_stop_loss(self, symbol: str, side: OrderSide, quantity: float, stop_price: float):
        """Places a STOP_MARKET order to close the position."""
        exit_side = "SELL" if str(side).upper() == "BUY" else "BUY"
        logger.info(f"[PROTECT] ACTION: SET_SL | SYMBOL: {symbol} | TRIGGER: {stop_price} | SIDE: {exit_side}")
        return self.client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type='STOP_MARKET',
            stopPrice=stop_price,
            closePosition=True
        )

    def place_take_profit(self, symbol: str, side: OrderSide, quantity: float, tp_price: float):
        """Places a TAKE_PROFIT_MARKET order to close the position."""
        exit_side = "SELL" if str(side).upper() == "BUY" else "BUY"
        logger.info(f"[PROTECT] ACTION: SET_TP | SYMBOL: {symbol} | TRIGGER: {tp_price} | SIDE: {exit_side}")
        return self.client.futures_create_order(
            symbol=symbol,
            side=exit_side,
            type='TAKE_PROFIT_MARKET',
            stopPrice=tp_price,
            closePosition=True
        )

    def place_twap_order(self, symbol: str, side: OrderSide, quantity: float, chunks: int = 5, interval_seconds: int = 10):
        """
        Simple TWAP implementation: splits quantity into chunks and places MARKET orders.
        """
        logger.info(f"[STRATEGY_START] TWAP | SIDE: {side} | TOTAL_QTY: {quantity} | SYMBOL: {symbol} | CHUNKS: {chunks}")
        responses = []
        chunk_qty = round(quantity / chunks, 6)
        
        for i in range(chunks):
            try:
                logger.info(f"[TWAP_CHUNK] {i+1}/{chunks} | PLACING MARKET ORDER...")
                resp = self.place_market_order(symbol, side, chunk_qty)
                responses.append(resp)
                if i < chunks - 1:
                    time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"[STRATEGY_ERROR] TWAP | CHUNK: {i+1} | MSG: {e}")
                break
        
        logger.info(f"[STRATEGY_END] TWAP | COMPLETED {len(responses)}/{chunks} CHUNKS")
        return responses

    def place_grid_order(self, symbol: str, quantity: float, lower_price: float, upper_price: float):
        """
        Simple Grid implementation: places one Buy Limit at lower_price and one Sell Limit at upper_price.
        """
        logger.info(f"[STRATEGY_START] GRID | SYMBOL: {symbol} | QTY: {quantity} | LOWER: {lower_price} | UPPER: {upper_price}")
        responses = []
        
        try:
            # Place Buy order
            logger.info("[GRID_ACTION] PLACING LOWER BUY LIMIT...")
            buy_resp = self.place_limit_order(symbol, OrderSide.BUY, quantity, lower_price)
            responses.append(buy_resp)
            
            # Place Sell order
            logger.info("[GRID_ACTION] PLACING UPPER SELL LIMIT...")
            sell_resp = self.place_limit_order(symbol, OrderSide.SELL, quantity, upper_price)
            responses.append(sell_resp)
            
        except Exception as e:
            logger.error(f"[STRATEGY_ERROR] GRID | MSG: {e}")
            raise
            
        logger.info("[STRATEGY_END] GRID | BOTH ORDERS PLACED")
        return responses

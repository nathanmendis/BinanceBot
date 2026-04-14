from pydantic import BaseModel, field_validator, ConfigDict
from enum import Enum
from typing import Optional

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    TWAP = "TWAP"
    GRID = "GRID" # Added

class OrderInput(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    symbol: str
    side: Optional[OrderSide] = None # Optional for GRID
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    lower_price: Optional[float] = None
    upper_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return v.upper()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v, info):
        if info.data.get('order_type') == OrderType.LIMIT and (v is None or v <= 0):
            raise ValueError("Price is required and must be greater than 0 for LIMIT orders")
        return v

    @field_validator('upper_price', 'lower_price')
    @classmethod
    def validate_grid_prices(cls, v, info):
        if info.data.get('order_type') == OrderType.GRID and (v is None or v <= 0):
            raise ValueError("Both upper and lower prices are required for GRID orders")
        return v

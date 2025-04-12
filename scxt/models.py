import time
from datetime import datetime, UTC
from typing import Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from web3.types import TxParams


# Common base models
class BaseTimestampedModel(BaseModel):
    """Base model with timestamp and datetime fields."""

    timestamp: int = Field(
        default_factory=lambda: int(time.time() * 1000),
        description="Timestamp in milliseconds",
    )
    datetime: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 datetime string",
    )


class BaseExchangeModel(BaseTimestampedModel):
    """Base model for exchange-related data with common fields."""

    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original information from the exchange",
    )


class MarketPrecision(BaseModel):
    """Precision settings for a market."""

    price: int = Field(default=18, description="Decimal places for price values")
    amount: int = Field(default=18, description="Decimal places for amount values")


class Market(BaseModel):
    """
    Market (trading pair) information.
    """

    id: str = Field(..., description="Unique identifier for the market on the exchange")
    symbol: str = Field(
        ...,
        description="Market symbol in SCXT unified format (e.g., 'BTC/USDT', 'ETH-PERP')",
    )
    base: str = Field(..., description="Base currency code")
    quote: str = Field(..., description="Quote currency code")
    active: bool = Field(
        default=True, description="Whether the market is active and tradeable"
    )
    type: str = Field(default="spot", description="Market type (spot, perp, etc.)")
    precision: MarketPrecision = Field(
        default_factory=MarketPrecision, description="Precision settings"
    )
    maker_fee: Optional[float] = Field(default=None, description="Maker fee rate")
    taker_fee: Optional[float] = Field(default=None, description="Taker fee rate")
    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original market information from the exchange",
    )
    # TODO: Add limits


class Currency(BaseModel):
    """
    Currency information.
    """

    id: str = Field(
        ..., description="Unique identifier for the currency on the exchange"
    )
    code: str = Field(
        ..., description="Currency code in SCXT unified format (e.g., 'BTC', 'ETH')"
    )
    name: Optional[str] = Field(default=None, description="Full name of the currency")
    active: bool = Field(
        default=True, description="Whether the currency is active and available"
    )
    precision: int = Field(
        default=18, description="Number of decimal places for currency amounts"
    )
    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original currency information from the exchange",
    )
    # TODO: Add limits


class Balance(BaseModel):
    """
    Account balance for a specific currency.
    """

    free: float = Field(default=0.0, description="Available balance")
    used: float = Field(
        default=0.0, description="Balance in use (e.g., in open orders)"
    )
    total: float = Field(default=0.0, description="Total balance (free + used)")

    @field_validator("total", mode="before")
    @classmethod
    def calculate_total(cls, v, info):
        """Calculate total from free and used if not provided."""
        # Only calculate if the value is explicitly None or 0.0
        if v == 0.0 and "free" in info.data and "used" in info.data:
            return info.data["free"] + info.data["used"]
        return v

    # Add model_post_init to ensure total is always calculated
    def model_post_init(self, __context):
        if self.total == 0.0:
            self.total = self.free + self.used


class AccountBalance(BaseExchangeModel):
    """Complete account balance information."""

    balances: Dict[str, Balance] = Field(
        default_factory=dict, description="Balances by currency code"
    )


class OrderType(str, Enum):
    """
    Order type enum.
    """

    MARKET = "market"
    LIMIT = "limit"


class OrderSide(str, Enum):
    """
    Order side enum.
    """

    BUY = "buy"
    SELL = "sell"


class Order(BaseModel):
    """
    Order information.
    """

    model_config = {
        "arbitrary_types_allowed": True,
    }

    tx_hash: Optional[str] = Field(..., description="Transaction hash")
    tx_params: Optional[TxParams] = Field(
        default_factory=TxParams, description="Transaction parameters"
    )
    market: str = Field(..., description="Market symbol")
    order_type: OrderType = Field(..., description="Order type")
    side: OrderSide = Field(..., description="Order side")
    price: Optional[float] = Field(default=None, description="Order price")
    amount: float = Field(..., description="Order amount in base currency")
    info: Dict[str, Any] = Field(
        default_factory=dict, description="Original order information from the exchange"
    )


class Position(BaseExchangeModel):
    """
    Position information for a specific market.
    """

    id: str = Field(..., description="Position ID")
    market: str = Field(..., description="Market symbol")
    size: float = Field(
        ..., description="Position size (positive for long, negative for short)"
    )
    margin: Optional[float] = Field(default=None, description="Position margin")
    liquidation_price: Optional[float] = Field(
        default=None, description="Position liquidation price"
    )

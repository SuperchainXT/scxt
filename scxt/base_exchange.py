from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Union, Tuple, List
import logging
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from scxt import ChainClient, ChainManager
from scxt.models import (
    Market,
    Currency,
    AccountBalance,
    Order,
    Position,
    # Ticker,
    # Trade,
)
from scxt.utils import iso8601, parse_timeframe, format_precision


class ExchangeConfig(BaseModel):
    """
    Configuration for an exchange.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    chain: Optional[ChainClient] = Field(
        default=None, description="Client for blockchain operations"
    )
    chain_manager: Optional[ChainManager] = Field(
        default=None, description="Chain manager for blockchain operations"
    )
    chain_id: Optional[int] = Field(
        default=None, description="Chain ID for blockchain operations"
    )
    private_key: Optional[str] = Field(
        default=None, description="Private key for blockchain operations"
    )
    contracts: Dict[str, str] = Field(
        default_factory=dict, description="Contract addresses for blockchain operations"
    )


class BaseExchange(ABC):
    """
    Base class for all exchange implementations.

    Defines the standard interface that all exchange implementations should follow.
    Each subclass should implement the abstract methods appropriate for their API.
    """

    def __init__(self, config: Union[Dict[str, Any], ExchangeConfig]):
        """
        Initialize the exchange with configuration parameters.

        Args:
            config: Exchange configuration (API keys, URLs, etc.)
        """
        self.config = ExchangeConfig.model_validate(config)
        self.logger = logging.getLogger(f"scxt.{self.__class__.__name__}")

        # set up the chain client if the proper configuration is provided
        self.chain = self._setup_chain()
        if self.chain:
            self.contracts = self._merge_configs(
                self.config.contracts, self.chain.contracts
            )
        else:
            self.contracts = self.config.contracts

        # exchange data caches
        self.markets: Dict[str, Market] = {}
        self.currencies: Dict[str, Currency] = {}

        # rate limiting state
        self._last_request_timestamp = 0
        self._rate_limit = 1000

    def _setup_chain(self) -> Optional[ChainClient]:
        """
        Set up the chain client for blockchain operations.
        """
        if self.config.chain:
            # if a chain is provided, use it
            return self.config.chain
        elif self.config.chain_id:
            # if a chain ID is provided, create a new client
            self.chain_manager = self.config.chain_manager or ChainManager()
            self.chain_manager.add_chain(self.config.chain_id)
            return self.chain_manager.get_client(self.config.chain_id)
        else:
            # no chain provided
            return None

    def _merge_configs(self, d1, d2):
        """Recursively merge two configuration dictionaries"""
        result = d1.copy()
        for k, v in d2.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    @abstractmethod
    def load_markets(self, reload: bool = False) -> Dict[str, Market]:
        """Load market definitions from the exchange"""
        pass

    @abstractmethod
    def fetch_markets(self) -> List[Market]:
        """Fetch all available markets from the exchange"""
        pass

    @abstractmethod
    def fetch_currencies(self) -> Dict[str, Currency]:
        """Fetch supported currencies and their properties"""
        pass

    @abstractmethod
    def fetch_balance(self) -> AccountBalance:
        """Fetch current account balance"""
        pass

    @abstractmethod
    def deposit(
        self,
        amount: float,
        currency: str,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> None:
        """
        Deposit funds into the exchange account
        Args:
            amount: Amount to deposit
            currency: Currency code (e.g., 'BTC', 'ETH')
            send: Whether to send the transaction immediately
            params: Additional parameters for the deposit
        """
        pass

    @abstractmethod
    def withdraw(
        self,
        amount: float,
        currency: str,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> None:
        """
        Withdraw funds from the exchange account

        Args:
            amount: Amount to withdraw
            currency: Currency code (e.g., 'BTC', 'ETH')
            send: Whether to send the transaction immediately
            params: Additional parameters for the withdrawal
        """
        pass

    @abstractmethod
    def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> Order:
        """
        Create a new order

        Args:
            symbol: Trading pair symbol
            type: Order type ('market', 'limit', etc.)
            side: Order side ('buy' or 'sell')
            amount: Order amount in base currency
            price: Order price (required for limit orders)
            send: Whether to send the order immediately
            params: Additional exchange-specific parameters
        """
        pass

    @abstractmethod
    def cancel_order(
        self,
        id: str,
        symbol: Optional[str] = None,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> Order:
        """
        Cancel an existing order

        Args:
            id: Order ID
            symbol: Trading pair symbol (required by some exchanges)
            send: Whether to send the cancellation immediately
            params: Additional exchange-specific parameters
        """
        pass

    @abstractmethod
    def fetch_open_order(
        self,
        id: str,
        params: Dict[str, Any] = {},
    ) -> Order:
        """
        Fetch order details

        Args:
            id: Order ID
            params: Additional exchange-specific parameters
        """
        pass

    @abstractmethod
    def fetch_position(self, symbol: str, params: Dict[str, Any] = {}) -> Position:
        """
        Fetch position for the account

        Args:
            symbol: Market symbol to fetch positions for a specific market
            params: Additional parameters for the request

        Returns:
            Position object containing position details
        """
        pass

    # Common utility methods

    def market(self, symbol: str) -> Market:
        """Get market information for a symbol"""
        if not self.markets or symbol not in self.markets:
            self.load_markets()

        if symbol not in self.markets:
            raise ValueError(f"Market '{symbol}' not found")

        return self.markets[symbol]

    def market_id(self, symbol: str) -> str:
        """Convert unified symbol to exchange-specific market ID"""
        return self.market(symbol).id

    def currency(self, code: str) -> Currency:
        """Get currency information"""
        if not self.currencies or code not in self.currencies:
            self.fetch_currencies()

        if code not in self.currencies:
            raise ValueError(f"Currency '{code}' not found")

        return self.currencies[code]

    def price_to_precision(self, symbol: str, price: float) -> float:
        """Format price according to exchange's precision rules"""
        market = self.market(symbol)
        return format_precision(price, market.precision.price)

    def amount_to_precision(self, symbol: str, amount: float) -> float:
        """Format amount according to exchange's precision rules"""
        market = self.market(symbol)
        return format_precision(amount, market.precision.amount)

    def get_fees(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get trading fees for a symbol or all symbols"""
        # Default implementation - exchanges should override
        return {"maker": 0.001, "taker": 0.001}

    def parse_symbol(self, symbol: str) -> Tuple[str, str]:
        """Convert 'BTC/USDT' to base/quote pair ('BTC', 'USDT')"""
        parts = symbol.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid symbol format: {symbol}")
        return parts[0], parts[1]

    def handle_rate_limits(self):
        """
        Basic rate limit handling. Exchanges should override with specific implementations.
        """
        now = datetime.now().timestamp() * 1000
        elapsed = now - self._last_request_timestamp
        if elapsed < self._rate_limit:
            # Simple delay to respect rate limits
            import time

            time.sleep((self._rate_limit - elapsed) / 1000)
        self._last_request_timestamp = now

    def iso8601(self, timestamp: Optional[int] = None) -> str:
        """Convert timestamp to ISO 8601 format"""
        return iso8601(timestamp)

    def parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string (e.g. '1m', '1h') to seconds"""
        return parse_timeframe(timeframe)

    def __str__(self) -> str:
        """Exchange name"""
        return self.__class__.__name__

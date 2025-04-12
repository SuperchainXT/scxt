from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from web3.types import HexBytes, TxParams
from scxt.models import (
    Market,
    Currency,
    MarketPrecision,
    AccountBalance,
    Balance,
    Order,
    Position,
)
from scxt.base_exchange import BaseExchange


class SynthetixV2(BaseExchange):
    """
    Synthetix V2 exchange implementation for interacting with the Synthetix protocol.
    """

    def __init__(self, config={}):
        # Default configuration options
        self.name = "Synthetix V2"

        # Default config values
        default_config = {
            "chain_id": 10,
            "contracts": {
                "PerpsV2MarketData": "0x340B5d664834113735730Ad4aFb3760219Ad9112",
                "sUSD": "0x8c6f28f2F1A3C87F0f938b96d27520d9751ec8d9",
            },
        }

        # Merge with provided config
        merged_config = self._merge_configs(default_config, config)

        # Initialize base class
        super().__init__(merged_config)

        # Load ABIs
        self._load_abis()

        # Basic initialization
        self.logger.info(
            f"Initialized {self.name} exchange on chain id {self.chain.chain_id}"
        )

    def _load_abis(self):
        """Load ABIs for the exchange"""
        ABIS_TO_LOAD = [
            "PerpsV2MarketData",
            "PerpsV2Market",
        ]
        for contract_name in ABIS_TO_LOAD:
            self.chain.load_abi(contract_name)

    def _get_market_contract(self, market: Market):
        """Get the contract for a specific market"""
        market_address = market.id
        market_contract = self.chain.get_contract(
            name="PerpsV2Market", address=market_address
        )
        return market_contract

    def load_markets(self, reload: bool = False) -> Dict[str, Market]:
        """Load markets for the exchange"""
        # Return cached markets if available and reload is not requested
        if self.markets and not reload:
            return self.markets

        data_contract = self.chain.get_contract(
            "PerpsV2MarketData", self.contracts["PerpsV2MarketData"]
        )
        self.logger.info("Calling allProxiedMarketSummaries()")
        raw_summaries = data_contract.functions.allProxiedMarketSummaries().call()
        self.logger.info("Received allProxiedMarketSummaries() response")

        # Process the raw summaries to create market objects
        markets = {}

        for summary in raw_summaries:
            # Extract and clean the asset name (remove null bytes)
            asset_bytes = summary.asset
            asset_name = asset_bytes.decode("utf-8").strip("\x00")
            # Handle the special case where sETH and sBTC are used
            if asset_name in ["sETH", "sBTC"]:
                asset_name = asset_name[1:]

            # Extract market key
            market_key = summary.key.decode("utf-8").strip("\x00")

            # Extract the market address
            market_address = summary.market

            # Extract fee rates
            maker_fee = summary.feeRates.makerFeeOffchainDelayedOrder / 1e18
            taker_fee = summary.feeRates.takerFeeOffchainDelayedOrder / 1e18

            # Format the market symbol
            symbol = f"{asset_name}-PERP"

            # Create market object
            market = Market(
                id=market_address,
                symbol=symbol,
                base=asset_name,
                quote="USD",
                active=True,
                type="perp",
                precision=MarketPrecision(price=18, amount=18),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                info={
                    "market_key": market_key,
                    "max_leverage": summary.maxLeverage / 1e18,
                    "market_size": summary.marketSize / 1e18,
                    "market_skew": summary.marketSkew / 1e18,
                    "market_debt": summary.marketDebt / 1e18,
                    "current_funding_rate": summary.currentFundingRate / 1e18,
                    "current_funding_velocity": summary.currentFundingVelocity / 1e18,
                },
            )

            # Add to markets dictionary
            markets[symbol] = market

        self.markets = markets
        self.logger.info(f"Loaded {len(markets)} markets from Synthetix V2")
        return markets

    def fetch_markets(self) -> List[Market]:
        """Fetch all available markets from the exchange"""
        # Reload markets and return as a list
        self.load_markets(reload=True)
        return list(self.markets.values())

    def fetch_currencies(self) -> Dict[str, Currency]:
        """Fetch supported currencies and their properties"""
        # If we already have currencies and not asked to reload, return them
        if self.currencies:
            return self.currencies

        # Load the sUSD contract
        susd_contract = self.chain.get_contract(
            name="ERC20", address=self.contracts["sUSD"]
        )
        currencies = {}

        # Add sUSD as the primary currency
        currencies["sUSD"] = Currency(
            id="sUSD",
            code="sUSD",
            name="Synthetix USD",
            active=True,
            precision=18,
            info={
                "contract": susd_contract,
            },
        )
        self.currencies = currencies
        self.logger.info(f"Loaded {len(currencies)} currencies from Synthetix V2")
        return currencies

    def fetch_balance(self, symbol) -> AccountBalance:
        """Fetch current account balance for a specific market.

        Args:
            symbol (str): The market symbol to fetch the balance for.

        Returns:
            AccountBalance: An object containing the available and used margin balances.
        """
        market = self.market(symbol)
        market_contract = self._get_market_contract(market)

        # Fetch balance from the market contract
        accessible_margin = market_contract.functions.accessibleMargin(
            self.chain.address
        ).call()
        remaining_margin = market_contract.functions.remainingMargin(
            self.chain.address
        ).call()

        # Convert to AccountBalance object
        free_margin = accessible_margin.marginAccessible
        used_margin = remaining_margin.marginRemaining - free_margin
        balance = Balance(
            free=self.chain.provider.from_wei(free_margin, "ether"),
            used=self.chain.provider.from_wei(used_margin, "ether"),
        )
        balances = {
            "sUSD": balance,
        }
        return AccountBalance(balances=balances)

    def deposit(
        self,
        amount: float,
        currency: str,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> Union[HexBytes, TxParams]:
        """Deposit a specific amount of currency into the exchange account for a specific market.

        Args:
            amount (float): The amount of currency to deposit.
            currency (str): The currency code to deposit (only 'sUSD' is supported).
            send (bool): Whether to send the transaction immediately or return the transaction parameters.
            params: Additional parameters for the deposit.

        Returns:
            HexBytes or TxParams: The transaction hash of the deposit transaction or the transaction parameters.

        Raises:
            ValueError: If a currency other than 'sUSD' is specified.
            ValueError: If the deposit amount is less than or equal to 0.
            ValueError: If the market is not specified.
        """
        if currency != "sUSD":
            raise ValueError("Only sUSD deposits are supported.")
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than 0")

        market = params.get("market", None)
        if not market:
            raise ValueError("Market must be specified for deposit")

        # Get the relevant contracts
        market = self.market(market)
        market_contract = self._get_market_contract(market)

        # Build the deposit transaction
        deposit_tx = self.chain.get_tx(to=market_contract.address)
        deposit_tx["data"] = market_contract.encode_abi(
            "transferMargin",
            [
                self.chain.provider.to_wei(amount, "ether"),
            ],
        )

        if send:
            tx_hash = self.chain.send_transaction(deposit_tx)
            self.logger.info(f"Deposit transaction sent: 0x{tx_hash.hex()}")
            return tx_hash
        else:
            return deposit_tx

    def withdraw(
        self,
        amount: float,
        currency: str,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> Union[HexBytes, TxParams]:
        """Withdraw a specific amount of currency from the exchange account for a specific market.

        Args:
            amount (float): The amount of currency to withdraw.
            currency (str): The currency code to withdraw (only 'sUSD' is supported).
            params (Dict[str, Any]): Additional parameters for the withdrawal.

        Returns:
            Union[HexBytes, TxParams]: The transaction hash of the withdrawal transaction or the transaction parameters.

        Raises:
            ValueError: If a currency other than 'sUSD' is specified.
        """
        if currency != "sUSD":
            raise ValueError("Only sUSD withdrawals are supported.")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than 0")
        market = params.get("market", None)
        if not market:
            raise ValueError("Market must be specified for withdrawal")

        # Get the relevant contracts
        market = self.market(market)
        market_contract = self._get_market_contract(market)

        # Build the withdrawal transaction
        withdraw_tx = self.chain.get_tx(to=market_contract.address)
        withdraw_tx["data"] = market_contract.encode_abi(
            "transferMargin",
            [
                -self.chain.provider.to_wei(amount, "ether"),
            ],
        )

        if send:
            # Send the transaction
            tx_hash = self.chain.send_transaction(withdraw_tx)
            self.logger.info(f"Withdraw transaction sent: 0x{tx_hash.hex()}")
            return tx_hash
        else:
            return withdraw_tx

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> Order:
        """
        Create a new order

        Args:
            symbol: Market symbol (e.g., 'BTC-PERP')
            order_type: Order type ('market', 'limit', etc.)
            side: Order side ('buy' or 'sell')
            amount: Order amount in base currency
            price: Order price (required for limit orders)
            send: Whether to send the transaction immediately
            params: Additional exchange-specific parameters

        Returns:
            Order: The created order object
        """
        if order_type != "market":
            raise ValueError("Only market orders are supported")
        if amount <= 0:
            raise ValueError("Order amount must be greater than 0")
        if side.lower() not in ["buy", "sell"]:
            raise ValueError("Order side must be 'buy' or 'sell'")

        # Get the market object
        market = self.market(symbol)
        market_contract = self._get_market_contract(market)

        # Default params
        params = params or {}
        params["tracking_code"] = params.get(
            "tracking_code",
            "0x5343585400000000000000000000000000000000000000000000000000000000",
        )
        params["slippage_tolerance"] = params.get("slippage_tolerance", 0.005)

        # Convert amount to size delta (positive for buy/long, negative for sell/short)
        size_delta = self.chain.provider.to_wei(amount, "ether")
        if side == "sell":
            size_delta = -size_delta

        # Set desired fill price
        if not price:
            asset_price = market_contract.functions.assetPrice().call()
            slippage_side = 1 if side == "buy" else -1
            price = int(
                self.chain.provider.from_wei(asset_price.price, "ether")
                * Decimal(1 + slippage_side * params["slippage_tolerance"])
                * Decimal(1e18)
            )

        tx = self.chain.get_tx(to=market_contract.address)
        tx["data"] = market_contract.encode_abi(
            "submitOffchainDelayedOrderWithTracking",
            [size_delta, price, params["tracking_code"]],
        )

        if send:
            # Build and send transaction
            tx_hash = self.chain.send_transaction(tx)
            self.logger.info(f"Order {order_type} transaction sent: 0x{tx_hash.hex()}")
        else:
            tx_hash = None

        # Create order object
        order = Order(
            tx_hash=tx_hash.hex() if tx_hash else None,
            tx_params=tx,
            market=market.symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            info={
                "tracking_code": params["tracking_code"],
                "slippage_tolerance": params["slippage_tolerance"],
                "market_address": market.id,
            },
        )
        return order

    def cancel_order(
        self,
        symbol: str,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> HexBytes:
        """
        Cancel an existing order

        Args:
            market: Market symbol (e.g., 'BTC-PERP')

        Returns:
            HexBytes: The transaction hash of the cancellation transaction
        """
        # Get the market object
        market = self.market(symbol)
        market_contract = self._get_market_contract(market)

        # Build the cancel transaction
        cancel_tx = self.chain.get_tx(to=market_contract.address)
        cancel_tx["data"] = market_contract.encode_abi(
            "cancelOffchainDelayedOrder",
            [self.chain.address],
        )

        # Build and send transaction
        if send:
            tx_hash = self.chain.send_transaction(cancel_tx)
            self.logger.info(f"Cancel order transaction sent: 0x{tx_hash.hex()}")
            return tx_hash
        else:
            return cancel_tx

    def fetch_open_order(self, id: str) -> Order:
        """
        Fetch an order for the account

        Args:
            id: Market symbol to fetch orders for a specific market

        Returns:
            An order object containing order details
        """
        market = self.market(id)
        market_contract = self._get_market_contract(market)

        # Get order data from the contract
        order_data = market_contract.functions.delayedOrders(self.chain.address).call()

        # Create Order object
        order = Order(
            tx_hash=None,
            tx_params=None,
            market=market.symbol,
            order_type="market",
            side="buy" if order_data.sizeDelta > 0 else "sell",
            amount=self.chain.provider.from_wei(order_data.sizeDelta, "ether"),
            price=self.chain.provider.from_wei(order_data.desiredFillPrice, "ether"),
            info={
                "market_address": market.id,
                "tracking_code": order_data.trackingCode,
                "executable_at": order_data.executableAtTime,
            },
        )
        return order

    def fetch_position(self, symbol: str) -> Position:
        """
        Fetch a position for the account

        Args:
            symbol: Market symbol to fetch positions for a specific market

        Returns:
            A position object containing position details
        """
        market = self.market(symbol)
        market_contract = self._get_market_contract(market)

        # Get position data from the contract
        position_data = market_contract.functions.positions(self.chain.address).call()

        # Check if the position exists and has a non-zero size
        if position_data and position_data.size != 0:
            size = self.chain.provider.from_wei(position_data.size, "ether")
            # Get liquidation price
            liq_price_data = market_contract.functions.liquidationPrice(
                self.chain.address
            ).call()
            liquidation_price = self.chain.provider.from_wei(
                liq_price_data.price, "ether"
            )

            # Create Position object
            position = Position(
                id=f"{market.symbol}-{position_data.id}",
                market=market.symbol,
                size=size,
                margin=self.chain.provider.from_wei(position_data.margin, "ether"),
                liquidation_price=liquidation_price,
                info={
                    "position_id": position_data.id,
                    "last_funding_index": position_data.lastFundingIndex,
                    "market_address": market.id,
                },
            )
        else:
            # Create empty position object
            position = Position(
                id=f"{market.symbol}-0",
                market=market.symbol,
                size=0,
                margin=0,
                liquidation_price=None,
                info={
                    "position_id": None,
                    "last_funding_index": None,
                    "market_address": market.id,
                },
            )
        return position

    # Exchange-specific functions
    def approve_market(
        self, symbol: str, amount: int = 2**256 - 1, send: bool = False
    ) -> Union[HexBytes, TxParams]:
        """
        Approve the market contract to spend a specific amount of sUSD.

        Args:
            symbol (str): The market symbol (e.g., 'BTC-PERP').
            amount (int): The amount of sUSD to approve (default is max uint256).
            send (bool): Whether to send the transaction immediately (default is False).

        Returns:
            HexBytes: The transaction hash of the approval transaction.
        """
        market = self.market(symbol)
        market_contract = self._get_market_contract(market)
        susd_contract = self.chain.get_contract(
            name="ERC20", address=self.contracts["sUSD"]
        )

        approve_return = self.chain.approve_token(
            token_address=susd_contract.address,
            spender_address=market_contract.address,
            amount=self.chain.provider.to_wei(amount, "ether"),
            send=send,
        )
        return approve_return

    # TODO: Add execute order function

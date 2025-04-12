from decimal import Decimal
from typing import Dict, List, Optional, Any, Union, Tuple

import requests
from web3.types import TxParams, Wei, HexBytes

from scxt.models import (
    Market,
    Currency,
    AccountBalance,
    Balance,
    Order,
    Position,
    OrderSide,
    OrderType,
)
from scxt.base_exchange import BaseExchange, ExchangeConfig
from scxt.http_client import HTTPClient, HTTPConfig

# Define the Odos API Base URL
ODOS_BASE_URL = "https://api.odos.xyz/"
ODOS_API_VERSION = "v2"


class Odos(BaseExchange):
    """
    Odos exchange implementation for interacting with the DEX aggregator.
    """

    def __init__(self, config: Union[Dict[str, Any], ExchangeConfig] = {}):
        self.name = "Odos"

        # Default config values
        default_config = {
            "chain_id": 10,  # Default to Optimism
            # "slippage_tolerance": 0.005,  # Default 0.5% slippage (used as decimal)
            # "referral_code": 0,  # TODO: Implement referral code
            # "odos_api_url": ODOS_BASE_URL,
            # "odos_api_version": ODOS_API_VERSION,
        }

        # Merge with provided config
        merged_config = self._merge_configs(default_config, config)

        # Initialize base class
        super().__init__(merged_config)

        # Initialize HTTP client directly
        try:
            base_url = ODOS_BASE_URL
            http_config = HTTPConfig(base_url=base_url)
            self.client = HTTPClient(http_config)
            self.client.logger = self.logger
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Odos HTTP client: {e}") from e

        self._load_contracts()

        self.logger.info(
            f"Initialized {self.name} exchange on chain id {self.chain.chain_id}"
        )

    def _load_contracts(self):
        """Load contracts from the Odos API."""
        endpoint = f"/info/contract-info/{ODOS_API_VERSION}/{self.chain.chain_id}"
        try:
            self.logger.info("Fetching router information from Odos API")
            response = self.client.get(endpoint)

            self.chain.contracts["OdosRouter"] = response.get("routerAddress")
            self.chain.abis["OdosRouter"] = response.get("routerAbi").get("abi")
            self.logger.info("Loaded contracts and ABIs for OdosRouter.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Odos API connection error fetching currencies: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to parse Odos currencies response: {e}")

    def _parse_symbol(self, symbol: str) -> Tuple[str, str]:
        """Parse a symbol like 'BASE/QUOTE' into base and quote currency codes."""
        if "/" not in symbol:
            raise ValueError(
                f"Invalid symbol format for Odos: '{symbol}'. Expected 'BASE/QUOTE'."
            )
        base, quote = symbol.split("/")
        if not base or not quote:
            raise ValueError(
                f"Invalid symbol format for Odos: '{symbol}'. Base or Quote missing."
            )
        return base.upper(), quote.upper()

    def load_markets(self, reload: bool = False) -> Dict[str, Market]:
        """Not applicable for Odos."""
        raise NotImplementedError("load_markets is not applicable for Odos aggregator.")

    def fetch_markets(self) -> List[Market]:
        """Not applicable for Odos."""
        raise NotImplementedError(
            "fetch_markets is not applicable for Odos aggregator."
        )

    def fetch_currencies(self, reload: bool = False) -> Dict[str, Currency]:
        """Fetch supported currencies from the Odos API for the configured chain."""
        if self.currencies and not reload:
            return self.currencies
        if not self.chain:
            raise RuntimeError("ChainClient not configured. Cannot fetch currencies.")

        endpoint = f"/info/tokens/{self.chain.chain_id}"
        try:
            self.logger.info("Fetching currencies from Odos API")
            response = self.client.get(endpoint)
            token_map = response.get("tokenMap", {})
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Odos API connection error fetching currencies: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to parse Odos currencies response: {e}")

        currencies = {}
        for address, token_data in token_map.items():
            code = token_data.get("symbol", "").upper()
            decimals = token_data.get("decimals")
            if not code or decimals is None:
                continue  # Skip tokens without symbol or decimals

            try:
                checksum_address = self.chain.provider.to_checksum_address(address)
            except Exception:
                self.logger.warning(
                    f"Invalid address format for token {code}: {address}. Skipping."
                )
                continue

            currencies[code] = Currency(
                id=checksum_address,
                code=code,
                name=token_data.get("name"),
                active=True,
                precision=decimals,
                info={"address": checksum_address},
            )

        self.currencies = currencies
        self.logger.info(
            f"Loaded {len(self.currencies)} currencies from Odos for chain {self.chain.chain_id}"
        )
        return self.currencies

    def fetch_balance(self, code: Optional[str] = None) -> AccountBalance:
        """Fetch the wallet balance for a specific currency code."""
        if code is None:
            raise NotImplementedError(
                "Fetching all balances is not implemented yet. Provide a currency code."
            )

        code_upper = code.upper()
        if not self.currencies or code_upper not in self.currencies:
            raise ValueError(
                f"Currency '{code_upper}' not loaded. Call fetch_currencies() first."
            )

        currency = self.currencies[code_upper]
        token_address = currency.info.get("address")
        decimals = currency.precision

        if not token_address or decimals is None:
            raise ValueError(
                f"Address or decimals missing for currency '{code_upper}'."
            )

        try:
            if code_upper == "ETH":
                # Fetch ETH balance
                balance_wei = self.chain.get_balance(self.chain.address)
            else:
                # Fetch all other ERC20 tokens
                balance_wei = self.chain.get_token_balance(token_address)
            balance_float = float(Decimal(balance_wei) / (Decimal(10) ** decimals))
            balance_obj = Balance(free=balance_float, used=0.0, total=balance_float)
            return AccountBalance(balances={code_upper: balance_obj})
        except Exception as e:
            self.logger.error(f"Failed to fetch balance for {code_upper}: {e}")
            raise RuntimeError(f"Failed to fetch balance for {code_upper}: {e}") from e

    def deposit(
        self, amount: float, currency: str, params: Dict[str, Any] = {}
    ) -> None:
        """Not applicable for Odos."""
        raise NotImplementedError(f"{self.name} does not support deposits.")

    def withdraw(
        self, amount: float, currency: str, params: Dict[str, Any] = {}
    ) -> None:
        """Not applicable for Odos."""
        raise NotImplementedError(f"{self.name} does not support withdrawals.")

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
        Prepare a swap order using the Odos aggregator. Returns prepared TxParams.

        Args:
            symbol (str): Trading pair symbol in 'BASE/QUOTE' format (e.g., 'WETH/USDC').
            order_type (str): Must be 'market'.
            side (str): 'buy' (buy BASE with QUOTE) or 'sell' (sell BASE for QUOTE).
            amount (float): Amount of the *input* token to spend.
            price (Optional[float]): Not used.
            send (bool): This parameter is ignored. The method always returns prepared TxParams.
            params (Dict[str, Any]): Additional parameters for Odos API (slippageLimitPercent, etc.).

        Returns:
            Order: An object containing the prepared transaction parameters in `order.tx_params`.

        Raises:
            ValueError: For invalid inputs (symbol, side, type, amount, missing currency).
            ConnectionError: If API requests fail due to network issues.
            RuntimeError: For unexpected API errors or parsing issues.
        """
        if order_type.lower() != "market":
            raise ValueError(f"{self.name} only supports 'market' order type.")
        if side.lower() not in ["buy", "sell"]:
            raise ValueError(f"Invalid order side: '{side}'. Must be 'buy' or 'sell'.")
        if amount <= 0:
            raise ValueError("Order amount must be positive.")

        # Parse the symbol
        base_code, quote_code = self._parse_symbol(symbol)
        input_code = quote_code if side.lower() == "buy" else base_code
        output_code = base_code if side.lower() == "buy" else quote_code
        self.logger.info(f"Preparing Odos swap: {amount} {input_code} -> {output_code}")

        # Get Token Details and Format Amount
        if input_code not in self.currencies or output_code not in self.currencies:
            raise ValueError(
                f"Input '{input_code}' or output '{output_code}' currency not found."
            )

        input_currency = self.currencies[input_code]
        output_currency = self.currencies[output_code]
        input_address = input_currency.info.get("address")
        output_address = output_currency.info.get("address")
        input_decimals = input_currency.precision

        if not input_address or not output_address or input_decimals is None:
            raise ValueError("Address or decimals missing for input/output tokens.")

        try:
            factor = Decimal(10) ** input_decimals
            input_amount_wei = str(int(Decimal(str(amount)) * factor))
        except Exception as e:
            raise ValueError(f"Could not format amount for {input_code}: {e}") from e

        # Prepare and Send Quote Request
        params["slippage_tolerance"] = params.get("slippage_tolerance", 0.005)
        quote_request_body = {
            "chainId": self.chain.chain_id,
            "inputTokens": [
                {"tokenAddress": input_address, "amount": input_amount_wei}
            ],
            "outputTokens": [{"tokenAddress": output_address, "proportion": 1}],
            "userAddr": self.chain.address,
            "slippageLimitPercent": params["slippage_tolerance"] * 100,
            "disableRFQs": params.get("disable_rfqs", True),
            "compact": params.get("compact", True),
            "sourceBlacklist": params.get("source_blacklist", []),
            "sourceWhitelist": params.get("source_whitelist", []),
        }

        self.logger.debug(f"Odos Quote Request Body: {quote_request_body}")
        try:
            quote_response = self.client.post(
                f"/sor/quote/{ODOS_API_VERSION}", data=quote_request_body
            )
            self.logger.debug(f"Odos Quote Response: {quote_response}")
            path_id = quote_response.get("pathId")
            if not path_id:
                raise RuntimeError(
                    f"Odos quote failed: {quote_response.get('message', 'No pathId found')}"
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Odos API connection error during quote: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Odos quote request failed: {e}") from e

        # Assemble the transaction
        assemble_request_body = {
            "userAddr": self.chain.address,
            "pathId": path_id,
            "simulate": params.get("simulate", False),
        }
        self.logger.debug(f"Odos Assemble Request Body: {assemble_request_body}")
        try:
            assemble_response = self.client.post(
                "/sor/assemble", data=assemble_request_body
            )
            self.logger.debug(f"Odos Assemble Response: {assemble_response}")
            tx_details = assemble_response.get("transaction")
            if not tx_details:
                raise RuntimeError(
                    f"Odos assemble failed: {assemble_response.get('message', 'No transaction data found')}"
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Odos API connection error during assemble: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Odos assemble request failed: {e}") from e

        # Prepare the transaction
        tx_params: TxParams = {
            "to": tx_details["to"],
            "data": tx_details["data"],
            "value": Wei(int(tx_details["value"])),
            "chainId": self.chain.chain_id,
        }
        if send:
            # Build and send transaction
            tx_hash = self.chain.send_transaction(tx_params)
            self.logger.info(f"Order {order_type} transaction sent: 0x{tx_hash.hex()}")
        else:
            tx_hash = None

        # Create the order object
        order = Order(
            tx_hash=tx_hash,
            tx_params=tx_params,
            market=symbol,
            order_type=OrderType.MARKET,
            side=OrderSide(side.lower()),
            amount=amount,
            price=None,  # TODO: Add price from quote
            info={
                "pathId": path_id,
                "input_token": input_code,
                "output_token": output_code,
                "input_amount_wei": input_amount_wei,
                "router_address": tx_params["to"],
                "quote_response": quote_response,
                "assemble_response": assemble_response,
            },
        )
        self.logger.info(f"Prepared Odos swap transaction for {symbol}.")
        return order

    def cancel_order(
        self,
        id: str,
        symbol: Optional[str] = None,
        send: bool = False,
        params: Dict[str, Any] = {},
    ) -> None:
        """Not applicable for Odos."""
        raise NotImplementedError(f"{self.name} does not support order cancellation.")

    def fetch_open_order(self, id: str, params: Dict[str, Any] = {}) -> Order:
        """Not applicable for Odos."""
        raise NotImplementedError(f"{self.name} does not have persistent open orders.")

    def fetch_position(self, symbol: str, params: Dict[str, Any] = {}) -> Position:
        """Not applicable for Odos."""
        raise NotImplementedError(f"{self.name} does not support positions.")

    # Exchange-specific functions
    def approve_router(
        self, token_address: str, amount: int = 2**256 - 1, send: bool = False
    ) -> Union[HexBytes, TxParams]:
        """
        Approve the router contract to spend a specific amount of a specified ERC20.

        Args:
            token_address (str): The address of the ERC20 token to approve.
            amount (int): The amount of the token to approve (default is max uint256).
            send (bool): Whether to send the transaction immediately (default is False).

        Returns:
            HexBytes: The transaction hash of the approval transaction.
        """
        router_contract = self.chain.get_contract(
            name="OdosRouter", address=self.chain.contracts["OdosRouter"]
        )

        approve_return = self.chain.approve_token(
            token_address=token_address,
            spender_address=router_contract.address,
            amount=self.chain.provider.to_wei(amount, "ether"),
            send=send,
        )
        return approve_return

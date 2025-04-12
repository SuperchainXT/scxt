import os
import json
from typing import Dict, Optional, Any, Union, List
import logging
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams, Wei, HexBytes, TxReceipt, Nonce
from eth_account import Account
from pydantic import BaseModel, Field

from scxt.constants import PUBLIC_RPCS


class ChainConfig(BaseModel):
    """Configuration for a blockchain connection."""

    rpc_url: Optional[str] = Field(
        default=None, description="RPC URL for the blockchain"
    )
    address: Optional[str] = Field(
        default=None,
        description="Address for an account. If a private key is provided, it must match.",
    )
    private_key: Optional[str] = Field(
        default=None, description="Private key for signing transactions"
    )
    chain_id: Optional[int] = Field(
        default=None, description="Expected chain ID (for validation)"
    )
    chain_name: Optional[str] = Field(
        default=None, description="Chain name (e.g., 'optimism', 'base')"
    )
    verify_chain: bool = Field(
        default=True,
        description="Whether to verify the chain ID matches the expected one",
    )
    gas_price_multiplier: float = Field(
        default=1.0, description="Multiplier for either `gasPrice` or `maxFeePerGas`"
    )
    gas_limit_multiplier: float = Field(
        default=1.1, description="Multiplier for `gas` from `estimateGas` calls"
    )
    gas_limit_buffer: int = Field(
        default=50000, description="Buffer to add to gas limit estimation"
    )
    contracts: Dict[str, str] = Field(
        default_factory=dict, description="Contract addresses for this chain"
    )


class ChainClient:
    """A general-purpose client for interacting with EVM-compatible blockchains."""

    def __init__(self, config: Union[Dict[str, Any], ChainConfig]):
        """Initialize the Web3 client."""
        # validate config
        self.config = ChainConfig.model_validate(config)

        # set up logger and initialize components
        self.logger = logging.getLogger("scxt.ChainClient")
        self.provider = self._setup_provider()
        self.chain_id = self._validate_chain()
        self.contracts = self.config.contracts

        # Set up account
        self.account = None
        self.address = None
        if self.config.private_key:
            self._setup_account()

        # load common ABIs
        self.abis = {}

    def _get_default_rpc_url(self, chain_id: int) -> str:
        """
        Get a default RPC URL for the given chain ID.
        In production, this would use environment variables or a config file.

        Args:
            chain_id: Chain ID

        Returns:
            RPC URL
        """
        env_var_name = f"CHAIN_{chain_id}_RPC"
        if env_var_name in os.environ:
            return os.environ[env_var_name]

        # Fallback to public RPCs - NOT recommended for production
        if chain_id in PUBLIC_RPCS:
            return PUBLIC_RPCS[chain_id]

        raise ValueError(f"No default RPC URL for chain {chain_id}")

    def _setup_provider(self) -> Web3:
        """Set up the Web3 provider from the RPC URL."""
        if not self.config.rpc_url and self.config.chain_id:
            self.logger.info("No RPC URL provided, using default for chain")
            self.config.rpc_url = self._get_default_rpc_url(self.config.chain_id)

        # TODO: Support other provider types (WS, IPC)
        provider = Web3(Web3.HTTPProvider(self.config.rpc_url))

        # Check connection
        if not self.config.rpc_url:
            raise ValueError("No RPC URL provided")
        elif not provider.is_connected():
            raise ConnectionError("Failed to connect to RPC.")

        return provider

    def _validate_chain(self) -> int:
        """Validate the chain ID if verification is enabled."""
        # get chain ID from provider
        provider_chain_id = self.provider.eth.chain_id

        # if chain ID is specified, verify it matches
        if self.config.verify_chain and self.config.chain_id is not None:
            self.logger.info(
                f"Connected to chain ID: {provider_chain_id}, "
                f"expected: {self.config.chain_id}"
            )
            if provider_chain_id != self.config.chain_id:
                raise ValueError(
                    f"Chain ID mismatch: connected to {provider_chain_id}, "
                    f"but expected {self.config.chain_id}"
                )

        return self.config.chain_id or provider_chain_id

    def _setup_account(self):
        """Set up an account from the private key if provided."""
        if self.config.private_key:
            try:
                self.account = Account.from_key(self.config.private_key)
                if self.config.address and self.account.address != self.config.address:
                    raise ValueError("Private key does not match provided address")
                self.address = self.provider.to_checksum_address(self.account.address)
                self.logger.info(f"Account signer set up with address: {self.address}")
            except Exception as e:
                self.logger.error(f"Failed to set up account: {e}")
                raise
        elif self.config.address:
            self.address = self.provider.to_checksum_address(self.config.address)
            self.logger.info(f"Account address set up: {self.address}")

    def load_abi(self, name: str) -> List:
        """Load an ABI from the contract directory or return from cache."""
        # Return cached ABI if available
        if name in self.abis:
            return self.abis[name]

        # Determine possible file paths
        module_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = []

        # First check chain-specific directory if chain_id is available
        if self.chain_id is not None:
            chain_specific_path = os.path.join(
                module_dir, "contracts", str(self.chain_id), f"{name}.json"
            )
            possible_paths.append(chain_specific_path)

        # Then check common directory
        common_path = os.path.join(module_dir, "contracts", "common", f"{name}.json")
        possible_paths.append(common_path)

        # Try each path
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        abi = json.load(f)

                    # Cache the loaded ABI
                    self.abis[name] = abi
                    self.logger.debug(f"Loaded ABI for {name} from {path}")
                    return abi
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse ABI file: {path}")
                except Exception as e:
                    self.logger.warning(f"Error loading ABI file {path}: {e}")

        raise FileNotFoundError(f"Could not find ABI for contract: {name}")

    def get_contract(self, name: str, address: Optional[str] = None) -> Contract:
        """
        Get a contract instance.

        Args:
            name: Name of the contract (used to look up ABI)
            address: Contract address (if None, uses address from config contracts)

        Returns:
            Web3 contract instance
        """
        # get ABI
        abi = self.load_abi(name)

        # get address
        if address is None:
            if name not in self.config.contracts:
                raise ValueError(
                    f"Contract address for {name} not found in configuration"
                )
            address = self.config.contracts[name]

        # create contract
        check_address = self.provider.to_checksum_address(address)
        return self.provider.eth.contract(
            address=check_address, abi=abi, decode_tuples=True
        )

    # Transaction methods
    def sign_transaction(self, tx: TxParams) -> HexBytes:
        """
        Sign a transaction with the account's private key.

        Args:
            tx: Transaction parameters

        Returns:
            Signed transaction
        """
        if not self.account:
            raise ValueError("Cannot sign transaction: no account set up")

        signed_tx = self.account.sign_transaction(tx)
        return signed_tx.raw_transaction

    def send_transaction(self, tx: TxParams, build: bool = True) -> HexBytes:
        """
        Sign and send a transaction.

        Args:
            tx: Transaction parameters

        Returns:
            Transaction hash
        """
        if build:
            tx = self.build_transaction(tx)
        raw_tx = self.sign_transaction(tx)
        tx_hash = self.provider.eth.send_raw_transaction(raw_tx)
        return tx_hash

    def wait_for_transaction_receipt(
        self, tx_hash: HexBytes, timeout: int = 120
    ) -> TxReceipt:
        """
        Wait for a transaction receipt.

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Transaction receipt
        """
        return self.provider.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

    def get_tx(
        self,
        tx: Optional[TxParams] = None,
        to: Optional[str] = None,
        value: int = 0,
        data: Optional[bytes] = None,
    ) -> TxParams:
        """
        Build a basic transaction with minimal parameters.

        Args:
            tx: Existing transaction parameters to build upon (optional)
            to: Recipient address
            value: Amount of ETH to send in wei
            data: Transaction data

        Returns:
            Basic transaction parameters
        """
        if not self.address:
            raise ValueError("cannot build transaction: no account connected")

        # initialize transaction parameters
        result_tx = {} if tx is None else tx.copy()

        # add sender if not already present
        if "from" not in result_tx:
            result_tx["from"] = self.address

        # add chain ID if not already present
        if "chainId" not in result_tx:
            result_tx["chainId"] = self.chain_id

        # add recipient if provided
        if to is not None:
            result_tx["to"] = to

        # add value if not already present
        if "value" not in result_tx:
            result_tx["value"] = Wei(value)

        # add data if provided
        if data is not None:
            result_tx["data"] = data

        return result_tx

    def update_nonce(self, tx: TxParams, nonce: Optional[int] = None) -> TxParams:
        """
        Add nonce to a transaction.

        Args:
            tx: Transaction parameters
            nonce: Specific nonce to use, or None to fetch from chain

        Returns:
            Transaction with nonce added
        """
        result_tx = tx.copy()
        if nonce is not None:
            result_tx["nonce"] = Nonce(nonce)
        elif self.address and "nonce" not in result_tx:
            result_tx["nonce"] = Nonce(
                self.provider.eth.get_transaction_count(self.address)
            )
        return result_tx

    def update_gas_price(
        self,
        tx: TxParams,
        max_fee_per_gas: Optional[Union[int, Wei, str]] = None,
        max_priority_fee_per_gas: Optional[Union[int, Wei, str]] = None,
        gas_price: Optional[Union[int, Wei, str]] = None,
    ) -> TxParams:
        """
        Add gas price information to a transaction.

        If no gas parameters are provided, EIP-1559 gas parameters will be
        automatically calculated based on current network conditions.

        Args:
            tx: Transaction parameters
            max_fee_per_gas: Max fee per gas in wei (for EIP-1559 transactions)
            max_priority_fee_per_gas: Max priority fee per gas (for EIP-1559)
            gas_price: Gas price in wei (for legacy transactions)

        Returns:
            Transaction with gas price information added
        """
        result_tx = tx.copy()

        # validate the inputs
        if gas_price is not None and (
            max_fee_per_gas is not None or max_priority_fee_per_gas is not None
        ):
            raise ValueError("cannot specify both legacy and eip-1559 gas prices")

        if gas_price is not None:
            # legacy transaction
            result_tx["gasPrice"] = Wei(int(gas_price))
        else:
            # eip-1559 transaction with automatic defaults if needed
            try:
                # get current base fee
                latest_block = self.provider.eth.get_block("latest")
                base_fee = latest_block["baseFeePerGas"]

                # set max fee per gas
                if max_fee_per_gas is not None:
                    result_tx["maxFeePerGas"] = Wei(int(max_fee_per_gas))
                else:
                    # default to base fee * multiplier
                    result_tx["maxFeePerGas"] = Wei(
                        int(base_fee * self.config.gas_price_multiplier)
                    )

                # set max priority fee
                if max_priority_fee_per_gas is not None:
                    result_tx["maxPriorityFeePerGas"] = Wei(
                        min(int(max_priority_fee_per_gas), result_tx["maxFeePerGas"])
                    )
                else:
                    try:
                        # try to get the suggested priority fee from the node
                        result_tx["maxPriorityFeePerGas"] = min(
                            self.provider.eth.max_priority_fee,
                            result_tx["maxFeePerGas"],
                        )
                    except Exception:
                        # fallback to a reasonable priority fee (0.1 gwei)
                        self.logger.debug(
                            "could not get max priority fee, using fallback"
                        )
                        result_tx["maxPriorityFeePerGas"] = min(
                            Wei(100000000), result_tx["maxFeePerGas"]
                        )

            except Exception as e:
                # if we can't get the base fee, fall back to legacy gas pricing
                self.logger.warning(f"failed to apply eip-1559 gas pricing: {e}")
                if "gasPrice" not in result_tx:
                    gas_price = self.provider.eth.gas_price
                    result_tx["gasPrice"] = Wei(
                        int(gas_price * self.config.gas_price_multiplier)
                    )
                    self.logger.debug(
                        f"using legacy gas price: {result_tx['gasPrice'] / 1e9:.2f} gwei"
                    )

        return result_tx

    def update_gas_limit(
        self,
        tx: TxParams,
        gas: Optional[int] = None,
    ) -> TxParams:
        """
        Add gas limit to a transaction.

        Args:
            tx: Transaction parameters
            gas: Specific gas limit to use, or None to estimate

        Returns:
            Transaction with gas limit added
        """
        result_tx = tx.copy()

        # add gas limit if provided, otherwise estimate it
        if gas is not None:
            result_tx["gas"] = gas
        elif "gas" not in result_tx:
            # estimate gas and add buffer
            try:
                estimated_gas = self.provider.eth.estimate_gas(result_tx)
                result_tx["gas"] = (
                    int(estimated_gas * self.config.gas_limit_multiplier)
                    + self.config.gas_limit_buffer
                )
                self.logger.debug(
                    f"estimated gas: {estimated_gas}, with buffer: {result_tx['gas']}"
                )
            except Exception as e:
                self.logger.error(f"failed to estimate gas: {e}")
                raise

        return result_tx

    def build_transaction(
        self,
        tx: Optional[TxParams] = None,
    ) -> TxParams:
        """
        Build a complete transaction with all necessary fields.

        This function takes a partial transaction and fills in any missing fields:
        - Basic transaction fields (from, to, value, data)
        - Nonce determination
        - Gas pricing (with EIP-1559 support)
        - Gas limit estimation

        Args:
            tx: Transaction parameters to build upon

        Returns:
            Complete transaction parameters
        """
        # initialize with empty dict if None
        result_tx = {} if tx is None else tx.copy()

        # add basic transaction parameters if not present
        if "from" not in result_tx and self.address:
            result_tx["from"] = self.address

        if "chainId" not in result_tx:
            result_tx["chainId"] = self.chain_id

        if "value" not in result_tx:
            result_tx["value"] = Wei(0)

        # extract parameters we need for helper methods
        nonce = result_tx.get("nonce")
        gas = result_tx.get("gas")
        gas_price = result_tx.get("gasPrice")
        max_fee_per_gas = result_tx.get("maxFeePerGas")
        max_priority_fee_per_gas = result_tx.get("maxPriorityFeePerGas")

        # add nonce
        result_tx = self.update_nonce(result_tx, nonce)

        # add gas price information
        result_tx = self.update_gas_price(
            result_tx, max_fee_per_gas, max_priority_fee_per_gas, gas_price
        )

        # add gas limit
        result_tx = self.update_gas_limit(result_tx, gas)
        return result_tx

    # Common blockchain operations
    def get_balance(self, address: Optional[str] = None) -> Wei:
        """
        Get the ETH balance of an address.

        Args:
            address: Address to check (if None, uses account address)

        Returns:
            Balance in wei
        """
        if address:
            address = self.provider.to_checksum_address(address)
        elif self.address:
            address = self.address
        else:
            raise ValueError("No address provided and no account set up")
        return self.provider.eth.get_balance(address)

    def get_token_balance(
        self, token_address: str, address: Optional[str] = None
    ) -> int:
        """
        Get the token balance of an address.

        Args:
            token_address: Address of the ERC20 token contract
            address: Address to check (if None, uses account address)

        Returns:
            Token balance
        """
        address = address or self.address
        if not address:
            raise ValueError("No address provided and no account set up")

        # Create token contract and call balanceOf
        token = self.get_contract("ERC20", token_address)
        return token.functions.balanceOf(address).call()

    def get_token_decimals(self, token_address: str) -> int:
        """
        Get the decimals of an ERC20 token.

        Args:
            token_address: Address of the ERC20 token contract

        Returns:
            Token decimals
        """
        token = self.get_contract("ERC20", token_address)
        return token.functions.decimals().call()

    def approve_token(
        self,
        token_address: str,
        spender_address: str,
        amount: int = 2**256 - 1,
        send: bool = False,
    ) -> Union[HexBytes, TxParams]:
        """
        Approve a spender to use tokens.

        Args:
            token_address: Address of the ERC20 token contract
            spender_address: Address of the spender
            amount: Amount to approve
            send: Whether to send the transaction immediately

        Returns:
            Transaction hash or transaction parameters
        """
        if not self.address:
            raise ValueError("Cannot approve tokens: no account set up")

        # build the transaction
        token = self.get_contract("ERC20", token_address)
        tx_params = self.get_tx(to=token.address)
        tx_params["data"] = token.encode_abi("approve", [spender_address, amount])

        # early return if not sending the transaction
        if not send:
            return tx_params

        # Send the transaction
        tx_hash = self.send_transaction(tx_params)
        return tx_hash

    def get_chain_info(self) -> Dict[str, Any]:
        """
        Get information about the current chain.

        Returns:
            Dict with chain details (id, block number, etc.)
        """
        return {
            "chain_id": self.chain_id,
            "block_number": self.provider.eth.block_number,
        }

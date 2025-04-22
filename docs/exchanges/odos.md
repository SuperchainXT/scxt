# Odos Guide

This guide explains how to use `scxt` to interact with Odos, a DEX aggregator.

## Overview

Odos is a DEX aggregator that optimizes token swaps across multiple exchanges to find the best rates and lowest slippage. The `scxt` implementation provides a simplified interface for interacting with Odos across supported blockchains.

Learn more about Odos at [Odos](https://www.odos.xyz/).

## Setup

To use the Odos exchange in your project, you'll need:

- A wallet with a private key for transaction signing
- ETH (or the native token of your target chain) for gas fees
- Tokens to swap (ERC-20 tokens)

### Initialization

First, initialize the Odos exchange with your configuration:

```python
import os
from scxt.exchanges import Odos
from scxt import ChainClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the chain connection
chain_config = {
    "chain_id": 10,  # Optimism (default)
    "private_key": os.getenv("PRIVATE_KEY"),
    "rpc_url": os.getenv("CHAIN_10_RPC"), # Replace with your RPC URL
}

# Create chain client
chain = ChainClient(chain_config)

# Initialize Odos exchange
odos = Odos({"chain": chain})
```

By default, Odos is configured to work with Optimism (chain ID 10), but you can also use it with other EVM-compatible chains by changing the `chain_id`.

## Fetching Currencies

Before performing swaps, you'll need to fetch the available currencies:

```python
# Load all available tokens for the selected chain
currencies = odos.fetch_currencies()

# Print available tokens
print(f"Loaded {len(currencies)} tokens")
for symbol, currency in list(currencies.items())[:5]:  # Show first 5 tokens
    print(f"Token: {symbol}, Address: {currency.info['address']}")
```

This method will call the Odos API to retrieve the list of supported tokens and their addresses. You can use the token symbols to reference them when creating orders.

## Checking Balances

Check your token balances using the `fetch_balance` method:

```python
# Check ETH/native token balance
eth_balance = odos.fetch_balance("ETH")
print(f"ETH Balance: {eth_balance.balances['ETH'].free}")

# Check an ERC-20 token balance (e.g., WETH)
weth_balance = odos.fetch_balance("WETH")
print(f"WETH Balance: {weth_balance.balances['WETH'].free}")

# Check USDC balance
usdc_balance = odos.fetch_balance("USDC")
print(f"USDC Balance: {usdc_balance.balances['USDC'].free}")
```

## Token Approval

Before swapping ERC-20 tokens, you need to approve the Odos router to spend your tokens:

```python
# Get token information
token = odos.currencies["WETH"]
token_address = token.info["address"]

# Approve the Odos router to spend your tokens
# The default amount is max uint256, which means unlimited approval
approval_tx = odos.approve_router(
    token_address=token_address,
    amount=1000,  # Specific amount to approve
    send=True,    # Set to True to send the transaction immediately
)

# Wait for the approval transaction to be confirmed
tx_receipt = odos.chain.wait_for_transaction_receipt(approval_tx)
print(f"Approval transaction confirmed: {tx_receipt['transactionHash'].hex()}")
```

## Creating Swap Orders

To swap tokens using Odos, use the `create_order` method:

```python
# Prepare a swap order (buy WETH with USDC)
order = odos.create_order(
    symbol="WETH/USDC",  # Trading pair in BASE/QUOTE format
    side="buy",          # 'buy' to buy base with quote, 'sell' to sell base for quote
    amount=100,          # Amount of input token to spend
    order_type="market", # Only 'market' is supported
    params={
        "slippage_tolerance": 0.005,  # 0.5% slippage tolerance (default)
    }
)

# The order object contains the prepared transaction parameters
print(f"Swap prepared: {order.info['input_token']} → {order.info['output_token']}")

# Send the transaction
tx_hash = odos.chain.send_transaction(order.tx_params)
print(f"Swap transaction sent: 0x{tx_hash.hex()}")

# Wait for the transaction to be confirmed
receipt = odos.chain.wait_for_transaction_receipt(tx_hash)
print(f"Swap confirmed in block {receipt['blockNumber']}")
```

You can also create and send the transaction in one step by setting `send=True`:

```python
# Create and send a swap order in one step
order = odos.create_order(
    symbol="USDC/WETH",  # Sell WETH for USDC
    side="buy",          # Buy USDC with WETH
    amount=0.1,          # Amount of WETH to spend
    order_type="market",
    send=True,           # Send the transaction immediately
)

# Wait for confirmation
receipt = odos.chain.wait_for_transaction_receipt(order.tx_hash)
print(f"Swap confirmed: 0x{order.tx_hash.hex()}")
```

### Understanding Swap Sides

- **Buy**: When side is "buy", you're buying the base currency with the quote currency. For example, with symbol "WETH/USDC" and side "buy", you're spending USDC to buy WETH.
- **Sell**: When side is "sell", you're selling the base currency for the quote currency. For example, with symbol "WETH/USDC" and side "sell", you're spending WETH to buy USDC.

## Advanced Configuration

Odos supports additional configuration options when creating orders:

```python
# Advanced order parameters
order = odos.create_order(
    symbol="WETH/USDC",
    side="buy",
    amount=100,
    order_type="market",
    params={
        "slippage_tolerance": 0.01,  # 1% slippage tolerance
        "referral_code": 0,          # Referral code if you have one
        "disable_rfqs": True,        # Disable RFQ sources
        "source_blacklist": ["Curve"],  # DEXs to exclude
        "source_whitelist": [],      # Only use these DEXs (empty = use all)
        "simulate": True,            # Simulate the transaction before sending
    }
)
```

For a full list of parameters, refer to the [Odos API documentation](https://docs.odos.xyz/build/api-docs).

## Complete Example

Here's a complete example that demonstrates fetching currencies, checking balances, approving tokens, and executing a swap:

```python
import os
from scxt.exchanges import Odos
from scxt import ChainClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure and initialize
chain_config = {
    "chain_id": 10,  # Optimism
    "private_key": os.getenv("PRIVATE_KEY"),
    "rpc_url": os.getenv("OPTIMISM_RPC_URL"),
}
chain = ChainClient(chain_config)
odos = Odos({"chain": chain})

# Fetch available currencies
currencies = odos.fetch_currencies()
print(f"Loaded {len(currencies)} tokens")

# Check balances
eth_balance = odos.fetch_balance("ETH")
print(f"ETH Balance: {eth_balance.balances['ETH'].free}")
usdc_balance = odos.fetch_balance("USDC")
print(f"USDC Balance: {usdc_balance.balances['USDC'].free}")

# Approve USDC for swapping
usdc = odos.currencies["USDC"]
approval_tx = odos.approve_router(
    token_address=usdc.info["address"],
    send=True
)
odos.chain.wait_for_transaction_receipt(approval_tx)
print("USDC approved for trading")

# Execute a swap (USDC to WETH)
swap_amount = 10  # Amount of USDC to swap
order = odos.create_order(
    symbol="WETH/USDC",
    side="buy",
    amount=swap_amount,
    order_type="market",
    send=True
)

# Wait for the swap to complete
receipt = odos.chain.wait_for_transaction_receipt(order.tx_hash)
print(f"Swap completed in block {receipt['blockNumber']}")

# Check updated balances
weth_balance = odos.fetch_balance("WETH")
print(f"New WETH Balance: {weth_balance.balances['WETH'].free}")
```

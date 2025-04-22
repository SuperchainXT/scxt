# Synthetix V2 Perps Guide

This guide explains how to use `scxt` to interact with Synthetix V2 perpetual futures markets on Optimism.

**Note:** Synthetix V2 requires direct blockchain interactions. You will need:

- A wallet with a private key, or a method to sign transactions.
- A supported RPC endpoint for the target chain (e.g., Optimism, Base).
- Sufficient funds in your wallet:
  - ETH (or the native token of the chain) for gas fees.
  - `sUSD` for margin deposits.

## Setup

First, make sure you have initialized the `SynthetixV2` exchange instance as shown in the [Quickstart Guide](../quickstart.md).

```python
import os
from scxt.exchanges import SynthetixV2
from dotenv import load_dotenv

load_dotenv()

config = {
    "chain_id": 10,  # Or your target chain ID (e.g., 8453 for Base)
    "private_key": os.getenv("PRIVATE_KEY"),
    "rpc_url": os.getenv("CHAIN_10_RPC") # Or your target chain RPC
}

try:
    exchange = SynthetixV2(config)
    exchange.logger.info(f"Connected to Synthetix V2 with address {exchange.chain.address}")
except Exception as e:
    exchange.logger.info(f"Error: {e}")

# Example: Load markets (needed for subsequent operations)
try:
    exchange.load_markets()
    exchange.logger.info("Markets loaded.")
except Exception as e:
    exchange.logger.info(f"Error loading markets: {e}")
```

## Fetching Margin Balance

You can check your available margin for a specific perpetual market.

```python
symbol = "ETH-PERP" # Example market symbol

try:
    balance_info = exchange.fetch_balance(symbol=symbol)
    susd_balance = balance_info.balances.get("sUSD")

    if susd_balance:
        exchange.logger.info(f"Margin for {symbol}:")
        exchange.logger.info(f"  Free: {susd_balance.free:.4f} sUSD")
        exchange.logger.info(f"  Used: {susd_balance.used:.4f} sUSD")
        exchange.logger.info(f"  Total: {susd_balance.total:.4f} sUSD")
    else:
        exchange.logger.info(f"Could not fetch sUSD balance for {symbol}")

except Exception as e:
    exchange.logger.error(f"Error fetching balance for {symbol}: {e}")
```

## Managing Margin

### Depositing Margin

You need to deposit `sUSD` into a specific market contract to trade.

```python
# Assuming 'exchange' is initialized and markets are loaded
symbol = "ETH-PERP"
amount_to_deposit = 100.0  # Amount of sUSD to deposit

try:
    approve_tx = exchange.approve_market(
        amount=amount_to_deposit,
        market=symbol,
        send=True
    )
    exchange.chain.wait_for_transaction_receipt(approve_tx)

    tx_hash = exchange.deposit(
        amount=amount_to_deposit,
        currency="sUSD",
        market=symbol,
        send=True
    )
    exchange.logger.info(f"Deposit transaction sent: 0x{tx_hash.hex()}")
    exchange.chain.wait_for_transaction_receipt(tx_hash)
    exchange.logger.info("Deposit confirmed!")

except Exception as e:
    print(f"Error depositing margin: {e}")
```

### Withdrawing Margin

You can withdraw your free margin from a market.

```python
# Assuming 'exchange' is initialized and markets are loaded
symbol = "ETH-PERP"
amount_to_withdraw = 50.0 # Amount of sUSD to withdraw

try:
    exchange.logger.info(f"Withdrawing {amount_to_withdraw} sUSD from {symbol} market...")
    tx_hash = exchange.withdraw(
        amount=amount_to_withdraw,
        currency="sUSD",
        market=symbol,
        send=True
    )
    exchange.logger.info(f"Withdrawal transaction sent: 0x{tx_hash.hex()}")
    exchange.chain.wait_for_transaction_receipt(tx_hash)
    exchange.logger.info("Withdrawal confirmed!")

except Exception as e:
    print(f"Error withdrawing margin: {e}")
```

## Fetching Positions

Check your current open position in a market.

```python
# Assuming 'exchange' is initialized and markets are loaded
symbol = "ETH-PERP"

try:
    position = exchange.fetch_position(symbol=symbol)

    print(f"Position for {symbol}:")
    print(f"  Size: {position.size}") # Positive for long, negative for short
    # Add other relevant fields if needed, e.g., margin, entry price (might require parsing 'info')
    # print(f"  Margin: {position.margin}")
    # print(f"  Liquidation Price: {position.liquidation_price}")
    print(f"  Raw Info: {position.info}") # Contains detailed data from the contract

except Exception as e:
    print(f"Error fetching position for {symbol}: {e}")
```

## Placing Orders (Simplified)

Synthetix V2 uses an asynchronous, keeper-driven system for order execution (off-chain delayed orders). The `create_order` function in `scxt` currently submits the _intent_ to create such an order (the "commit" step).

**Important:** The function returns the transaction hash of this initial submission. Actual execution depends on keepers and network conditions. This is a simplified interface; monitoring the order status until execution requires further steps beyond the basic `create_order` call.

```python
# Assuming 'exchange' is initialized and markets are loaded
symbol = "ETH-PERP"
order_size = 0.1 # Amount of the base asset (e.g., ETH)

# Example: Market Buy Order
try:
    print(f"Submitting Market Buy order for {order_size} {symbol.split('-')[0]}...")
    order_result_tx = exchange.create_order(
        symbol=symbol,
        order_type="market",
        side="buy",
        amount=order_size
    )
    print(f"Market Buy order submission tx: 0x{order_result_tx.hex()}")
except Exception as e:
    print(f"Error creating market buy order: {e}")

# Example: Limit Sell Order
limit_price = 3500.0
try:
    print(f"Submitting Limit Sell order for {order_size} {symbol.split('-')[0]} at {limit_price}...")
    order_result_tx = exchange.create_order(
        symbol=symbol,
        order_type="limit",
        side="sell",
        amount=order_size,
        price=limit_price
    )
    print(f"Limit Sell order submission tx: 0x{order_result_tx.hex()}")
except Exception as e:
    print(f"Error creating limit sell order: {e}")

```

## Fetching and Cancelling Delayed Orders

Synthetix V2 has the concept of "delayed orders" (which the `create_order` function submits). You can fetch the details or cancel _pending_ delayed orders.

```python
# Assuming 'exchange' is initialized and markets are loaded
symbol = "ETH-PERP"

# Fetch pending delayed order
try:
    order = exchange.fetch_order(symbol=symbol)
    if order.info.get('size', 0) != 0: # Check if a delayed order exists
      print(f"Pending delayed order for {symbol}:")
      print(f"  Side: {'Buy' if order.info['size'] > 0 else 'Sell'}")
      print(f"  Size: {abs(order.info['size'])}")
      print(f"  Target Price: {order.info['target_price']}") # Price for limit orders
      print(f"  Commit Deposit: {order.info['commit_deposit']}")
      print(f"  Keeper Deposit: {order.info['keeper_deposit']}")
      print(f"  Is Offchain: {order.info['is_offchain']}")
    else:
      print(f"No pending delayed order found for {symbol}.")
except Exception as e:
    print(f"Error fetching delayed order for {symbol}: {e}")

# Cancel pending delayed order
try:
    print(f"Attempting to cancel delayed order for {symbol}...")
    cancel_tx = exchange.cancel_order(symbol=symbol)
    print(f"Cancel order transaction sent: 0x{cancel_tx.hex()}")
    # Wait for confirmation if needed
except Exception as e:
    # This will likely fail if there is no cancellable delayed order
    print(f"Error cancelling delayed order for {symbol}: {e}")
```

## Important Considerations

- **Keeper Delays:** Synthetix V2 order execution relies on keepers and has inherent delays. `create_order` only starts the process.
- **sUSD:** Ensure your wallet has sufficient `sUSD` for margin and ETH for gas.

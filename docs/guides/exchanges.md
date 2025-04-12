# Exchanges

Exchanges are the backbone of the `scxt` library. The unified interface provides a consistent way to interact with each exchange, regardless of the underlying smart contracts or APIs.

## Understanding the Exchange Interface

Each exchange in `scxt` inherits from the `BaseExchange` class, which defines a standard interface that makes it easy to switch between different protocols without changing your code.

### Core Exchange Methods

Here are the key methods available in the exchange interface:

| Method                                                        | Description                                   |
| ------------------------------------------------------------- | --------------------------------------------- |
| `load_markets()`                                              | Load market definitions from the exchange     |
| `fetch_markets()`                                             | Get a list of all available markets           |
| `fetch_currencies()`                                          | Get supported currencies and their properties |
| `fetch_balance()`                                             | Get your current account balance              |
| `deposit(amount, currency, send=False)`                       | Deposit funds into the exchange               |
| `withdraw(amount, currency, send=False)`                      | Withdraw funds from the exchange              |
| `create_order(symbol, type, side, amount, price, send=False)` | Create a new trading order                    |
| `cancel_order(id, symbol, send=False)`                        | Cancel an existing order                      |
| `fetch_order(id, symbol)`                                     | Get details of a specific order               |
| `fetch_position(symbol)`                                      | Get your current position for a market        |

### Utility Methods

Each exchange also provides utility methods to help with common operations:

| Method                                | Description                                |
| ------------------------------------- | ------------------------------------------ |
| `market(symbol)`                      | Get market information for a symbol        |
| `currency(code)`                      | Get currency information                   |
| `price_to_precision(symbol, price)`   | Format price according to exchange rules   |
| `amount_to_precision(symbol, amount)` | Format amount according to exchange rules  |
| `get_fees(symbol)`                    | Get trading fees for a symbol              |
| `parse_symbol(symbol)`                | Convert 'BTC/USDT' to ('BTC', 'USDT') pair |

## Working with Transactions

The `send` parameter is present in several methods (`deposit`, `withdraw`, `create_order`, `cancel_order`) and controls whether transactions are:

- **Prepared only (`send=False`)**: Returns transaction parameters that you can modify before sending
- **Executed immediately (`send=True`)**: Signs and sends the transaction to the blockchain

When `send=False` (default), you get a transaction object that you can later send using the chain client:

```python
# Prepare a transaction
tx_params = exchange.create_order(
    symbol='BTC-PERP',
    type='market',
    side='buy',
    amount=0.1,
    send=False
)

# Modify parameters if needed
tx_params['gas_limit'] = 300000

# Send the modified transaction
tx_hash = exchange.chain.send_transaction(tx_params)
```

See the [transactions guide](transactions.md) for more details on how to work with transactions in `scxt`.

## Using the `params` Parameter

Many methods include a `params` dictionary parameter for exchange-specific options. This allows you to access unique features of each exchange while maintaining a consistent API.

Common use cases for the `params` parameter include:

### Market-Specific Parameters

```python
# Set specific parameters for Synthetix
order = exchange.create_order(
    symbol='ETH-PERP',
    type='market',
    side='buy',
    amount=0.1,
    send=True,
    params={
        'tracking_code': '0x123456...',  # Synthetix-specific tracking code
        'slippage_tolerance': 0.01       # Allow 1% slippage
    }
)
```

### Network and Chain Selection

```python
# Specify deposit network
exchange.deposit(
    amount=100,
    currency='USDC',
    params={
        'market': 'ETH-PERP'  # Required by some exchanges
    }
)
```

## Exchange Configuration

When instantiating an exchange, you can provide various configuration parameters:

```python
import scxt

exchange = scxt.exchange({
    # Blockchain connection
    'chain_id': 10,                           # Optimism Mainnet
    'rpc_url': 'https://mainnet.optimism.io', # RPC endpoint
    'private_key': '0x123...',                # Optional, for signing transactions

    # Contract addresses (exchange-specific)
    'contracts': {
        'PerpsV2MarketData': '0x340B5d664834113735730Ad4aFb3760219Ad9112',
        'sUSD': '0x8c6f28f2F1A3C87F0f938b96d27520d9751ec8d9',
    },
})
```

## Chain Client Integration

Each exchange is connected to a `ChainClient`, which handles blockchain interactions. When you call methods with `send=True`, transactions are routed through the provided RPC.

You can access the chain client directly for common operations like ERC20 balances and approvals, as well as utilities for preparing and signing transactions:

```python
# Approve a token for trading
tx_hash = exchange.chain.approve_token(
    token_address='0x1234...',
    spender_address='0xabcd...',
    amount=1000000,
    send=True
)

# Wait for transaction confirmation
receipt = exchange.chain.wait_for_transaction_receipt(tx_hash)
```

## Exchange-Specific Features

While the unified API covers common functionality, some exchanges have unique features. You can access these through exchange-specific methods:

```python
# Synthetix-specific method
if isinstance(exchange, scxt.exchanges.SynthetixV2):
    tx_hash = exchange.approve_market('ETH-PERP', send=True)
```

Each exchange implementation may have specific requirements for initialization and usage, so refer to the exchange-specific documentation for more details.

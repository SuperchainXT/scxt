# SCXT

SCXT is a Python library providing a unified interface for interacting with exchanges across the Optimism Superchain

## Overview

SCXT abstracts away the complexities of interacting with protocols by providing a consistent API across all supported exchanges. This makes it easier for developers to build trading tools, bots, and analytics platforms that work across multiple protocols and chains.

## Installation

```bash
# uv
uv add scxt

# pip
pip install scxt
```

## Quick Start

```python
import scxt

# Initialize the exchange
exchange = scxt.exchange({
    'rpc_url': 'https://mainnet.optimism.io',
    'private_key': 'your_private_key',  # Optional, for trading
})

# Fetch available markets
markets = exchange.fetch_markets()
print(markets)

# Fetch account balances (requires private key)
balances = exchange.fetch_balance()
print(balances)

# Create a market order (requires private key)
order = exchange.create_order(
    symbol='ETH',
    type='market',
    side='buy',
    amount=0.1,
)
print(order)
```

## Features

- Unified API between protocols and exchanges
- Market data retrieval (available markets, prices, order books)
- Account information and balances
- Consistent error handling and data formats

## Supported Exchanges

(coming soon)

## Documentation

For detailed documentation, examples, and API references, visit [the documentation site](#) (coming soon).

## Acknowledgments

- This project is supported by an Optimism Builders Grant
- Inspired by the [CCXT](https://github.com/ccxt/ccxt) library for centralized exchanges

## Status

SCXT is currently in early development. The API is subject to change as the project evolves.

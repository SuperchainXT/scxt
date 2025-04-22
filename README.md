# SCXT

SCXT is a Python library providing a unified interface for interacting with exchanges across the Optimism Superchain

## Overview

SCXT abstracts away the complexities of interacting with protocols by providing a consistent API across all supported exchanges. This makes it easier for developers to build trading tools, bots, and analytics platforms that work across multiple protocols and chains.

## Quickstart

The core idea is to create an instance of the exchange you want to use. Let's use Synthetix V2 on the Optimism network (chain ID 10) as an example.

```python
import os
from scxt.exchanges import SynthetixV2
from dotenv import load_dotenv

# Load environment variables (optional, for API keys etc.)
load_dotenv()

# Configuration for Synthetix V2
config = {
    "chain_id": 10,  # Optimism Mainnet
    "private_key": os.getenv("PRIVATE_KEY"), # Your wallet's private key
    "rpc_url": os.getenv("CHAIN_10_RPC") # An Optimism RPC endpoint
}

# Create the exchange instance
exchange = SynthetixV2(config)

# Fetch markets
markets = exchange.fetch_markets()
print("Markets:", markets)
```

## Features

- Unified API between protocols and exchanges
- Market data retrieval (available markets, prices, order books)
- Account information and balances
- Consistent error handling and data formats

## Supported Exchanges

- Synthetix V2
- Odos

## Documentation

For detailed documentation, examples, and API references, visit [the documentation site](#) (coming soon).

## Acknowledgments

- This project is supported by an Optimism Builders Grant
- Inspired by the [CCXT](https://github.com/ccxt/ccxt) library for centralized exchanges

## Status

SCXT is currently in early development. The API is subject to change as the project evolves.

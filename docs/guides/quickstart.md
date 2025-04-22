# Quickstart Guide

This guide will help you get started with `scxt` quickly.

## Installation

You can install `scxt` using uv or pip:

```bash
# uv
uv add scxt

# pip
pip install scxt
```

## Basic Usage: Connecting to an Exchange

The core idea is to create an instance of the exchange you want to use. Let's use Synthetix V2 on the Optimism network (chain ID 10) as an example.

```python
import os
from scxt.exchanges.synthetix import SynthetixV2
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
```

**Important Notes:**

- **Private Key:** Private key security is extremely important. Storing private keys in environment variables is a common practice, but ensure you use secure methods to manage them. Never hardcode your private key in your source code. For production applications, consider using a secrets management system and simply using `scxt` to prepare transaction data and signing them using a more secure method.
- **RPC URL:** If an RPC is not provided, the library will default to a public RPC endpoint. These often have restricted features, low rate limits, and do not guarantee uptime. For production applications it is recommended to use a hosted solution like [Alchemy](https://www.alchemy.com/), [Infura](https://www.infura.io/), or any other reliable provider.

## Fetching Market Data

Once connected, you can fetch information like available markets:

```python
markets = exchange.fetch_markets()
for market in markets[:5]:
    print(f"- {market.symbol} (ID: {market.id})")
```

## Next Steps

Now that you have the basics, check out the specific guides for more advanced actions:

- **[Best Practices](./best_practices.md):** Understand important considerations for building reliable applications.
- **[Synthetix V2 Guide](../exchanges/synthetix_v2.md):** Learn how to place orders, check balances, and manage positions on Synthetix V2.
- **[Odos Guide](../exchanges/odos.md):** Learn how to use Odos for token swaps.

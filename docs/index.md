# Welcome to scxt!

`scxt` is a Python library designed to make it easier to interact with cryptocurrency exchanges, with a special focus on decentralized exchanges (DEX) that require direct blockchain interactions.

## Installation

```bash
# uv
uv add scxt

# pip
pip install scxt
```

## What does it do?

- **Unified Interface:** Provides a standard way to connect to and trade on different exchanges, so you don't have to learn a new system for each one.
- **Chain Integration:** Seamlessly handles blockchain operations like preparing transactions, interacting with ERC20 tokens, and interacting with smart contracts.
- **Standard Data Models:** Uses consistent structures (like `Market`, `Order`, `Position`) and methods (like `create_order`, `fetch_markets`, etc.) across all supported exchanges, making your trading logic more portable.

## Who is it for?

`scxt` is built for developers and traders who want programmatic access to crypto exchanges, especially those building applications or bots that interact with DeFi protocols on the Superchain.

This library draws inspiration from the popular [`ccxt`](https://github.com/ccxt/ccxt) library, but focuses on the unique needs of decentralized exchanges and direct blockchain interactions.

## Explore the Docs

- **[Quickstart Guide](quickstart.md):** Get started with installation and basic usage.
- **[Best Practices](guides/best_practices.md):** Tips for using `scxt` effectively and safely.

**Exchange Guides:**

- **[Synthetix V2 Guide](exchanges/synthetix_v2.md):** Learn how to trade on Synthetix V2 Perps.
- **[Odos Guide](exchanges/odos.md):** Learn how to trade on Odos.

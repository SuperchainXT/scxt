# Best Practices Guide

Here are some recommendations for using `scxt` effectively and safely, especially when dealing with DeFi protocols.

## Security

- **Private Key Management:** NEVER hardcode your private key directly in your source code. Use secure methods like:
  - Dedicated secrets management systems (like HashiCorp Vault, AWS Secrets Manager, etc.) for production applications.
  - Hardware wallets or secure enclaves for high-security scenarios (though direct integration might require more advanced setup).
  - Environment variables (e.g., using `.env` files and `python-dotenv`) are suitable for development and testing, however they are not recommended for production. These can be accidentally exposed if the code is shared or pushed to a public repository, packaged in a Docker image, or if the machine is compromised.

## Configuration

- **RPC Endpoints:** Use reliable and private RPC endpoints for production systems. Public RPCs often have rate limits, may be less reliable, and could potentially expose your transaction data.
- **Chain ID Verification:** Keep `verify_chain=True` (the default) in `ChainConfig` to prevent accidental transactions on the wrong network.
- **Contract Addresses:** Double-check that the contract addresses in your configuration (either default or provided) are correct for the specific exchange and network you are targeting.

## Blockchain Interactions (DeFi)

- **Gas Estimation:** Gas costs can fluctuate. While `scxt` applies multipliers (`gas_limit_multiplier`, `gas_price_multiplier`), monitor actual gas usage and adjust these multipliers in the `ChainConfig` if needed for reliability or cost optimization.
- **Transaction Confirmation:** Blockchain transactions are asynchronous. Don't assume an action is complete immediately after sending a transaction.
  - Use `chain.wait_for_transaction_receipt(tx_hash)` to wait for a transaction to be mined.
  - Check the `status` field in the returned receipt (`receipt.status == 1` for success, `0` for failure).
- **Nonce Management:** `scxt`'s `ChainClient` handles nonce management automatically by default. However, if you are managing multiple transactions or accounts, be aware of nonce conflicts. You can always set `send=False` in a transaction in order to override the default nonce management and send the transaction manually later.
- **Approvals:** When interacting with tokens, remember that you often need to _approve_ the exchange contract to spend your tokens first.

# Transaction Management with `scxt`

This guide explains how to work with transactions using the `scxt` library. Understanding transaction preparation, signing, and submission is essential for interacting with exchanges and blockchain protocols.

## Transaction Preparation Basics

The `ChainClient` class in `scxt` provides several methods for preparing and submitting transactions to EVM-compatible blockchains. There are two main approaches to working with transactions:

1. **Automatic mode** - Using `send=True` to automatically prepare and submit transactions
2. **Manual mode** - Using `send=False` to get transaction data for custom handling

Any method which prepares a transaction will contain a `send` parameter.

## Building Transactions

Transactions are prepared in a few steps. The `ChainClient` contains some methods to help with this process, but provides a flexible interface for you to customize transactions as needed:

### 1. Basic Transaction Fields

First, we use the `get_tx` method to create a basic transaction object:

- `to`: Sets the recipient address
- `from`: Sets the sender address to your connected account
- `chainId`: Sets the blockchain network ID
- `value`: Sets the native token amount to send (defaults to 0)

### 2. Transaction Data

Next, we use the smart contract ABI to encode the transaction data. Each smart contract will have it's own logic, but exchanges in `scxt` typically abstract away this complexity. Since contract interfaces are included, we can map the smart contract function to the unified interface.

```python
# Get the contract instance
token_contract = client.chain.get_contract("ERC20", token_address="0x1234...")

# Use encode_abi from the contract instance
tx_data = token_contract.encode_abi("approve", [spender_address, amount])

# Create transaction with data
tx_params = client.chain.get_tx(
    to=token_contract.address
)
tx_params['data'] = tx_data
```

### 3. Build Transaction

To complete a transaction, you need to add these important components:

1. **Gas pricing** - Determines how much you'll pay for the transaction

   - Uses provider estimates and applies your configured multiplier
   - Supports both EIP-1559 and legacy transactions
   - Can be adjusted with `gas_price_multiplier` in your configuration

2. **Nonce** - Transaction sequence number

   - Automatically fetched from the RPC for your account
   - Ensures transactions are processed in the correct order

3. **Gas limit** - Maximum computational resources allowed
   - Calculated with `estimateGas` based on your transaction
   - Applies a buffer and multiplier for safety
   - Can be configured with `gas_limit_multiplier` and `gas_limit_buffer`

All three components can be applied at once using the `build_transaction()` method or set `build=True` when calling `send_transaction`.

## Transaction Submission

### Automatic Mode (send=True)

The simplest way to send a transaction is to use automatic mode:

```python
# Initialize your exchange client
client = scxt.exchange({
    'rpc_url': 'https://mainnet.optimism.io',
    'private_key': 'your_private_key',
})

# Create and send a transaction in one step
tx_hash = client.chain.approve_token(
    token_address='0x1234...',
    spender_address='0xabcd...',
    amount=1000000,
    send=True  # This will sign and send the transaction
)

# Wait for the transaction to be mined
receipt = client.wait_for_transaction_receipt(tx_hash)
```

In this mode, the library:

1. Creates the transaction
2. Fills in missing parameters using default logic (nonce, gas price, gas limit)
3. Signs the transaction with your private key
4. Submits it to the RPC
5. Returns the transaction hash

### Manual Mode (send=False)

For more control, use manual mode to get the transaction data:

```python
# Get transaction data without sending
tx_params = client.approve_token(
    token_address='0x1234...',
    spender_address='0xabcd...',
    amount=1000000,
    send=False  # Returns transaction data instead of sending
)

print(tx_params)
# Example output:
# {
#     'to': '0x1234...',
#     'from': '0xabcd...',
#     'data': '0x...',
#     'value': 0,
#     'chainId': 1
# }

# You can now modify the transaction with any parameters you want:
tx_params['gas'] = 100000
tx_params['nonce'] = 0

# Option 1: Send the transaction
# This option will add any missing parameters and send the transaction
# Finally, it will sign and submit the transaction and return the transaction hash
tx_hash = client.chain.send_transaction(tx_params, build=True)

# Option 2: Build the transaction, but sign and send it yourself
# This option will return the transaction parameters
# You can use any signing method you want, but this requires a more advanced setup
tx_hash = client.chain.build_transaction(tx_params)
# YOUR SIGNING LOGIC HERE
```

Manual mode is useful for:

- Implementing advanced gas strategies
- Complex nonce management in multi-threaded or asynchronous applications
- Using external signing solutions (hardware wallets, multisigs, etc.)
- Building transaction batching systems
- Implementing simulation before submission

## Transaction Receipts

After sending a transaction, you can retrieve the transaction receipt to check its status:

```python
# Wait for transaction confirmation with timeout
receipt = client.wait_for_transaction_receipt(tx_hash)

# Check transaction status
if receipt['status'] == 1:
    print("Transaction succeeded!")
else:
    print("Transaction failed!")
```

## Advanced Transaction Configuration

You can configure default transaction behavior in the `ChainConfig`:

```python
client = scxt.exchange({
    'rpc_url': 'https://mainnet.optimism.io',
    'private_key': 'your_private_key',

    # Transaction defaults
    'gas_price_multiplier': 1.1,   # 10% higher than base price
    'gas_limit_multiplier': 1.2,   # 20% buffer on gas estimates
    'gas_limit_buffer': 50000,     # Additional 50K gas units
})
```

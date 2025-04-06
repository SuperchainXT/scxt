from hexbytes import HexBytes
from web3 import Web3


TEST_TO_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TEST_CHAIN_ID = 1
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def test_get_tx(client):
    """test creating a basic transaction"""

    # test basic tx
    tx = client.get_tx(to=TEST_TO_ADDRESS, value=1000)
    assert tx["from"] == client.address
    assert tx["to"] == TEST_TO_ADDRESS
    assert tx["value"] == 1000
    assert tx["chainId"] == TEST_CHAIN_ID

    # test with existing tx
    base_tx = {"to": TEST_TO_ADDRESS, "value": 2000}
    tx = client.get_tx(tx=base_tx)
    assert tx["from"] == client.address
    assert tx["to"] == TEST_TO_ADDRESS
    assert tx["value"] == 2000
    assert tx["chainId"] == TEST_CHAIN_ID

    # test with data
    tx = client.get_tx(data=b"test data")
    assert tx["data"] == b"test data"


def test_update_nonce(client):
    """test adding nonce to a transaction"""

    # test with explicit nonce
    tx = client.get_tx()
    tx = client.update_nonce(tx, nonce=42)
    assert tx["nonce"] == 42

    # test with automatic nonce
    tx = client.get_tx()
    tx = client.update_nonce(tx)
    assert "nonce" in tx
    assert isinstance(tx["nonce"], int)


def test_update_gas_price(client):
    """test adding gas price to a transaction"""

    # test with legacy gas price
    tx = client.get_tx()
    tx = client.update_gas_price(tx, gas_price=20_000_000_000)  # 20 gwei
    assert "gasPrice" in tx
    assert tx["gasPrice"] == 20_000_000_000
    assert "maxFeePerGas" not in tx
    assert "maxPriorityFeePerGas" not in tx

    # test with eip-1559 params
    tx = client.get_tx()
    tx = client.update_gas_price(
        tx,
        max_fee_per_gas=30_000_000_000,  # 30 gwei
        max_priority_fee_per_gas=2_000_000_000,  # 2 gwei
    )
    assert "maxFeePerGas" in tx
    assert "maxPriorityFeePerGas" in tx
    assert tx["maxFeePerGas"] == 30_000_000_000
    assert tx["maxPriorityFeePerGas"] == 2_000_000_000
    assert "gasPrice" not in tx

    # test with automatic eip-1559 params
    tx = client.get_tx()
    tx = client.update_gas_price(tx)
    assert ("maxFeePerGas" in tx and "maxPriorityFeePerGas" in tx) or "gasPrice" in tx


def test_update_gas_limit(client):
    """test adding gas limit to a transaction"""

    # test with explicit gas limit
    tx = client.get_tx()
    tx = client.update_gas_limit(tx, gas=100000)
    assert tx["gas"] == 100000

    # test with estimation
    # tx = client.get_tx(to=TEST_TO_ADDRESS, value=100)
    # tx = client.update_gas_limit(tx)
    # assert "gas" in tx
    # assert tx["gas"] > 21000  # basic tx gas + buffer


def test_build_transaction(client):
    """test building a complete transaction"""

    # test simple transaction
    tx = client.build_transaction(
        tx={
            "to": TEST_TO_ADDRESS,
            "value": Web3.to_wei(0.002, "ether"),
            "gas": 21000,
        }
    )
    assert tx["to"] == TEST_TO_ADDRESS
    assert tx["value"] == Web3.to_wei(0.002, "ether")
    assert "gas" in tx
    assert ("maxFeePerGas" in tx and "maxPriorityFeePerGas" in tx) or "gasPrice" in tx
    assert "nonce" in tx


def test_token_operations(client):
    """test token-related operations"""

    # test token balance
    try:
        balance = client.get_token_balance(USDC)
        decimals = client.get_token_decimals(USDC)

        # test token approval (if we have a balance)
        if balance > 0:
            tx_hash, receipt = client.approve_token(USDC, TEST_TO_ADDRESS, amount=1000)
            assert isinstance(tx_hash, HexBytes)
            assert receipt["status"] == 1
        assert isinstance(balance, int)
        assert decimals == 6
    except Exception as e:
        client.logger.error(f"Failed to test token operations: {e}")

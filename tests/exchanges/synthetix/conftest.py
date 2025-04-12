import pytest
from dotenv import load_dotenv
from eth_account import Account
from scxt import ChainClient
from scxt.exchanges import SynthetixV2

load_dotenv()

TEST_MNEMONIC = "test test test test test test test test test test test junk"


@pytest.fixture
def account():
    """Get a test account"""
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(TEST_MNEMONIC)


def steal_susd(exchange):
    """Steal sUSD from a whale"""
    WHALE_ADDRESS = "0x2145304C34a9837349C3250D9311fC742336b2Fe"
    exchange.chain.provider.provider.make_request(
        "anvil_impersonateAccount", [WHALE_ADDRESS]
    )

    # Get the sUSD contract
    susd_contract = exchange.currencies["sUSD"].info["contract"]

    # Create a tx
    tx = exchange.chain.get_tx(tx={"from": WHALE_ADDRESS}, to=susd_contract.address)
    tx["data"] = susd_contract.encode_abi(
        "transfer",
        [
            # WHALE_ADDRESS,
            exchange.chain.address,
            exchange.chain.provider.to_wei(1000, "ether"),
        ],
    )
    tx["nonce"] = exchange.chain.provider.eth.get_transaction_count(WHALE_ADDRESS)
    tx = exchange.chain.build_transaction(tx)
    tx_hash = exchange.chain.provider.eth.send_transaction(tx)

    # tx_hash = exchange.chain.send_transaction(tx)
    exchange.chain.provider.eth.wait_for_transaction_receipt(tx_hash)
    exchange.chain.provider.provider.make_request(
        "anvil_stopImpersonatingAccount", [WHALE_ADDRESS]
    )
    return tx_hash


@pytest.fixture
def snx(account):
    """Get a test Synthetix exchange with a funded account"""
    chain_config = {
        "chain_id": 10,
        "private_key": f"0x{account.key.hex()}",
    }
    chain = ChainClient(chain_config)

    config = {
        "chain": chain,
    }
    exchange = SynthetixV2(config)
    exchange.load_markets()
    exchange.fetch_currencies()

    # Fund the account with sUSD
    steal_susd(exchange)

    # Check if an order exists, and if so cancel it
    order = exchange.fetch_open_order("ETH-PERP")
    if order.amount > 0:
        cancel_tx = exchange.cancel_order(order.id, send=True)
        exchange.chain.wait_for_transaction_receipt(cancel_tx)
    return exchange

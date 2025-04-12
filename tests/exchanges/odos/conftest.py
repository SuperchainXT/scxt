import pytest
from dotenv import load_dotenv
from eth_account import Account
from scxt import ChainClient
from scxt.exchanges import Odos

load_dotenv()

TEST_MNEMONIC = "test test test test test test test test test test test junk"


@pytest.fixture
def account():
    """Get a test account"""
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(TEST_MNEMONIC)


@pytest.fixture
def odos_op(account):
    """Get a test Odos exchange on OP mainnet with a funded account"""
    chain_config = {
        "chain_id": 10,
        "private_key": f"0x{account.key.hex()}",
    }
    chain = ChainClient(chain_config)

    config = {
        "chain": chain,
    }
    exchange = Odos(config)
    exchange.fetch_currencies()
    return exchange

import pytest
from dotenv import load_dotenv
from eth_account import Account
from scxt import ChainClient

load_dotenv()

TEST_MNEMONIC = "test test test test test test test test test test test junk"


@pytest.fixture
def account():
    """Get a test account"""
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(TEST_MNEMONIC)


@pytest.fixture
def client(account):
    """Get a test client"""
    config = {
        "chain_id": 1,
        "private_key": account.key.hex(),
    }
    return ChainClient(config)

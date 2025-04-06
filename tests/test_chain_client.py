import pytest
from eth_account import Account
from scxt import ChainConfig, ChainClient
from scxt.constants import PUBLIC_RPCS


@pytest.mark.parametrize("chain_id", [1, 10, 8453])
def test_default_client(chain_id):
    client = ChainClient({"chain_id": chain_id})
    assert client

    # run some RPC calls and ensure the client works
    block = client.provider.eth.get_block("latest")
    assert block
    assert block["number"] > 0

    chain_id = client.provider.eth.chain_id
    assert chain_id == chain_id


def test_bad_chain_config():
    # bad chain id
    with pytest.raises(ValueError):
        ChainClient({"chain_id": 9999})

    # missing chain id
    with pytest.raises(ValueError):
        ChainClient({})

    # chain id mismatch with validation
    with pytest.raises(ValueError):
        ChainClient(
            {
                "chain_id": 1,
                "rpc_url": PUBLIC_RPCS[10],
                "verify_chain": True,
            }
        )

    # bad chain id without verification
    test_client = ChainClient(
        {
            "chain_id": 1,
            "rpc_url": PUBLIC_RPCS[10],
            "verify_chain": False,
        }
    )
    assert test_client
    assert test_client.chain_id == 1
    assert test_client.provider.eth.chain_id == 10


def test_chain_client_init_with_dict():
    """Test initializing ChainClient with a config dictionary"""
    client = ChainClient({"chain_id": 1})
    assert client.chain_id == 1
    assert client.provider.is_connected()


def test_chain_client_init_with_config():
    """Test initializing ChainClient with a ChainConfig object"""
    config = ChainConfig(chain_id=1)
    client = ChainClient(config)
    assert client.chain_id == 1
    assert client.provider.is_connected()


def test_load_abi():
    """Test loading an ABI from the built-in cache"""
    client = ChainClient({"chain_id": 1})
    abi = client.load_abi("ERC20")
    assert isinstance(abi, list)
    assert len(abi) > 0
    assert any(item["name"] == "balanceOf" for item in abi)


def test_load_abi_not_found():
    """Test error when loading non-existent ABI"""
    client = ChainClient({"chain_id": 1})
    with pytest.raises(FileNotFoundError):
        client.load_abi("NonExistentContract")


def test_load_abi_cache_storage():
    """Test that loaded ABIs are properly stored in the cache"""
    client = ChainClient({"chain_id": 1})

    # Clear the existing cache for ERC20 to test fresh loading
    if "ERC20" in client.abis:
        del client.abis["ERC20"]

    # Load the ABI
    abi = client.load_abi("ERC20")

    # Verify it was added to the cache
    assert "ERC20" in client.abis
    assert client.abis["ERC20"] is abi  # Same object reference

    # Load again and verify it returns the cached version
    cached_abi = client.load_abi("ERC20")
    assert cached_abi is abi  # Should be the same object reference


def test_load_different_abis():
    """Test loading multiple different ABIs"""
    client = ChainClient({"chain_id": 1})

    # Load ERC20 ABI
    erc20_abi = client.load_abi("ERC20")
    assert isinstance(erc20_abi, list)
    assert any(item.get("name") == "balanceOf" for item in erc20_abi)

    usdc_abi = client.load_abi("USDC")
    assert isinstance(usdc_abi, list)
    assert "USDC" in client.abis


def test_get_chain_info():
    """Test getting chain information"""
    client = ChainClient({"chain_id": 1})
    info = client.get_chain_info()

    assert isinstance(info, dict)
    assert "chain_id" in info
    assert info["chain_id"] == 1
    assert "block_number" in info
    assert isinstance(info["block_number"], int)
    assert info["block_number"] > 0


def test_account_setup_with_private_key():
    """Test setting up an account with a private key"""
    # Generate a random private key for testing
    acct = Account.create()

    client = ChainClient(
        {
            "chain_id": 1,
            "private_key": acct.key.hex(),
        }
    )

    assert client.account is not None
    assert client.address == acct.address


# TODO: Test get_balance
# TODO: Test get_token_balance

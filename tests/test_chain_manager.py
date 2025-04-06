import pytest
from scxt import ChainManager, ChainClient, ChainConfig


def test_chain_manager_init():
    """Test ChainManager initialization"""
    manager = ChainManager()
    assert manager.clients == {}


def test_add_chain():
    """Test adding a chain to the manager"""
    manager = ChainManager()
    client = manager.add_chain(1)  # Ethereum mainnet

    assert 1 in manager.clients
    assert isinstance(client, ChainClient)
    assert client.chain_id == 1


def test_add_chain_with_config_dict():
    """Test adding a chain with config dictionary"""
    manager = ChainManager()
    config = {"rpc_url": "https://eth.llamarpc.com"}
    client = manager.add_chain(1, config)

    assert 1 in manager.clients
    assert client.config.rpc_url == "https://eth.llamarpc.com"


def test_add_chain_with_config_object():
    """Test adding a chain with ChainConfig object"""
    manager = ChainManager()
    config = ChainConfig(chain_id=1, rpc_url="https://eth.llamarpc.com")
    client = manager.add_chain(1, config)

    assert 1 in manager.clients
    assert client.config.rpc_url == "https://eth.llamarpc.com"


def test_get_client():
    """Test getting a client by chain id"""
    manager = ChainManager()
    manager.add_chain(1)
    manager.add_chain(10)

    client = manager.get_client(1)
    assert client.chain_id == 1

    client = manager.get_client(10)
    assert client.chain_id == 10


def test_get_client_invalid_chain():
    """Test getting a client for non-existent chain"""
    manager = ChainManager()

    with pytest.raises(ValueError, match="No client for chain 999"):
        manager.get_client(999)


def test_remove_chain():
    """Test removing a chain from the manager"""
    manager = ChainManager()
    manager.add_chain(1)
    manager.add_chain(10)

    assert len(manager.clients) == 2

    manager.remove_chain(1)
    assert 1 not in manager.clients
    assert 10 in manager.clients
    assert len(manager.clients) == 1


def test_remove_nonexistent_chain():
    """Test removing a chain that doesn't exist"""
    manager = ChainManager()
    manager.add_chain(1)

    with pytest.raises(ValueError, match="No client for chain 999"):
        manager.remove_chain(999)


def test_get_all_chains():
    """Test getting information for all chains"""
    manager = ChainManager()
    manager.add_chain(1)
    manager.add_chain(10)

    chains_info = manager.get_all_chains()

    assert isinstance(chains_info, list)
    assert len(chains_info) == 2

    # Check that each item is a dictionary with the expected information
    for chain_info in chains_info:
        assert isinstance(chain_info, dict)
        assert "chain_id" in chain_info


def test_multiple_chains_operations():
    """Test operating with multiple chains"""
    manager = ChainManager()

    eth_client = manager.add_chain(1)
    op_client = manager.add_chain(10)
    base_client = manager.add_chain(8453)

    assert len(manager.clients) == 3

    # Verify clients are stored correctly
    assert manager.get_client(1) == eth_client
    assert manager.get_client(10) == op_client
    assert manager.get_client(8453) == base_client

    # Remove one chain
    manager.remove_chain(10)
    assert len(manager.clients) == 2
    assert 10 not in manager.clients

    with pytest.raises(ValueError):
        manager.get_client(10)

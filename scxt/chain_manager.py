from typing import Dict, List, Optional, Any, Union
import logging

from scxt.chain_client import ChainClient, ChainConfig


class ChainManager:
    """
    Manager for multiple blockchain connections.

    Allows working with multiple chains simultaneously for cross-chain operations
    like arbitrage, bridging, and monitoring.
    """

    def __init__(self) -> None:
        """Initialize the chain manager."""
        self.clients: Dict[int, ChainClient] = {}
        self.logger = logging.getLogger("scxt.ChainManager")

    def add_chain(
        self,
        chain_id: int,
        config: Optional[Union[Dict[str, Any], ChainConfig]] = None,
    ) -> ChainClient:
        """
        Add a new chain connection.

        Args:
            chain_id: Chain ID (e.g., 1 for Ethereum)
            config: Chain configuration

        Returns:
            ChainClient instance
        """
        # create a config
        if config is None:
            config = ChainConfig(chain_id=chain_id)
        elif isinstance(config, dict):
            config["chain_id"] = chain_id
            config = ChainConfig.model_validate(config)

        # create the client
        client = ChainClient(config)
        self.clients[client.chain_id] = client

        self.logger.info(f"Added chain {client.chain_id}")
        return client

    def get_client(self, chain_id: int) -> ChainClient:
        """
        Get a client for the specified chain.

        Args:
            chain_id_or_name: Chain ID or name

        Returns:
            ChainClient instance
        """
        # Get the client
        if chain_id not in self.clients:
            raise ValueError(f"No client for chain {chain_id}")
        return self.clients[chain_id]

    def remove_chain(self, chain_id: int) -> None:
        """
        Remove a chain connection.

        Args:
            chain_id_or_name: Chain ID or name
        """
        client = self.get_client(chain_id)
        del self.clients[client.chain_id]
        self.logger.info(f"Removed chain {client.chain_id}")

    def get_all_chains(self) -> List[Dict[str, Any]]:
        """
        Get information about all connected chains.

        Returns:
            List of chain information dictionaries
        """
        return [client.get_chain_info() for client in self.clients.values()]

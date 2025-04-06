"""Constants module for SCXT.

This module contains global constants used throughout the SCXT package,
including blockchain addresses, RPC endpoints, and ABIs.
"""

# Multicall3 contract address deployed on most EVM chains
MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"

# Dictionary of public RPC endpoints mapped by chain ID
PUBLIC_RPCS = {
    1: "https://eth.llamarpc.com",           # Ethereum Mainnet
    10: "https://mainnet.optimism.io/",      # Optimism
    8453: "https://mainnet.base.org",        # Base
}

# Minimal ABI for interacting with ERC20 tokens
MINIMAL_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

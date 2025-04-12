from eth_account import Account
from scxt import ChainClient
from scxt.models import Currency, AccountBalance, Balance
from scxt.exchanges import Odos


def test_init_odos():
    exchange = Odos()
    assert exchange.name == "Odos"
    assert exchange.chain.chain_id == 10
    assert isinstance(exchange.chain, ChainClient)


def test_odos_fetch_currencies():
    exchange = Odos()
    currencies = exchange.fetch_currencies()

    # Check that currencies dictionary is not empty
    assert len(currencies) > 0
    assert isinstance(currencies, dict)

    # Check that all values are Currency instances
    assert all(isinstance(currency, Currency) for currency in currencies.values())

    # Check that sUSD exists
    assert "ETH" in currencies
    assert "OP" in currencies
    assert "WETH" in currencies
    assert "USDC" in currencies

    # Check some properties
    weth = currencies["WETH"]
    assert weth.id == "0x4200000000000000000000000000000000000006"
    assert weth.code == "WETH"
    assert weth.name == "Wrapped Ether"
    assert weth.active is True
    assert weth.precision == 18


def test_odos_balance():
    # Create a new account for testing
    account = Account.create()
    address = account.address
    private_key = account.key.hex()

    exchange = Odos()

    # Set the account address and private key
    exchange.chain.address = address
    exchange.chain.private_key = private_key

    exchange.fetch_currencies()

    # Check that the balance is fetched correctly
    balance = exchange.fetch_balance("WETH")
    assert isinstance(balance, AccountBalance)
    assert isinstance(balance.balances, dict)
    assert "WETH" in balance.balances
    assert isinstance(balance.balances["WETH"], Balance)

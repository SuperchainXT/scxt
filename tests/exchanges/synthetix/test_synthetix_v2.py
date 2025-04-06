from eth_account import Account
from scxt import ChainClient
from scxt.models import Market, Currency, AccountBalance, Balance
from scxt.exchanges import SynthetixV2


def test_init_synthetix():
    exchange = SynthetixV2()
    assert exchange.name == "Synthetix V2"
    assert exchange.chain.chain_id == 10
    assert isinstance(exchange.chain, ChainClient)
    assert "PerpsV2MarketData" in exchange.chain.abis


def test_synthetix_v2_load_markets():
    exchange = SynthetixV2()
    exchange.load_markets()

    # check markets
    assert len(exchange.markets) > 0
    assert isinstance(exchange.markets, dict)
    assert all(isinstance(market, Market) for market in exchange.markets.values())


def test_synthetix_v2_fetch_currencies():
    exchange = SynthetixV2()
    currencies = exchange.fetch_currencies()

    # Check that currencies dictionary is not empty
    assert len(currencies) > 0
    assert isinstance(currencies, dict)

    # Check that all values are Currency instances
    assert all(isinstance(currency, Currency) for currency in currencies.values())

    # Check that sUSD exists
    assert "sUSD" in currencies

    # Check sUSD properties
    susd = currencies["sUSD"]
    assert susd.id == "sUSD"
    assert susd.code == "sUSD"
    assert susd.name == "Synthetix USD"
    assert susd.active is True
    assert susd.precision == 18
    assert "contract" in susd.info
    assert susd.info["contract"].address == exchange.contracts["sUSD"]


def test_synthetix_v2_balance():
    # Create a new account for testing
    account = Account.create()
    address = account.address
    private_key = account.key.hex()

    exchange = SynthetixV2()

    # Set the account address and private key
    exchange.chain.address = address
    exchange.chain.private_key = private_key

    exchange.load_markets()
    exchange.fetch_currencies()

    # Check that the balance is fetched correctly
    balance = exchange.fetch_balance("ETH-PERP")
    assert isinstance(balance, AccountBalance)
    assert isinstance(balance.balances, dict)
    assert "sUSD" in balance.balances
    assert isinstance(balance.balances["sUSD"], Balance)

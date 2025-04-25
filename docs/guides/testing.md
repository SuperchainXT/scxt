## Testing

The tests are located in the `tests` directory. The tests in the root `tests` directory are meant to verify the functionality of the various clients. The `exchanges` directory contains tests for each exchange. These tests may require some configuration to run, for example running local anvil node and updating the chain RPC.

### Running Tests

To run the tests, you can use the following command:

```bash
# run tests
uv run pytest tests

# increased logging verbosity
uv run pytest --log-cli-level=INFO tests
```

### Running Exchange Tests

To run the exchange tests, you will need to install [foundry](https://book.getfoundry.sh/getting-started/installation.html) and run the following command:

```bash
anvil --fork-url <RPC_URL>
```

This will start a local anvil node that the tests can connect to. It is important to use a local fork in order to fund the test account with ETH, or impersonate other accounts. Before running the tests, make sure to update the `CHAIN_{id}_RPC` environment variable in the `.env` file to point to your local anvil node.

Note that some tests will run slowly due to the overhead of fetching data on the forked chain. It is likely that public RPCs or slower nodes will run into issues with rate limits.

```bash
# run exchange tests
uv run pytest tests/exchanges/odos
```

### Test Fixtures

Check test fixtures in `tests/exchange/{exchange_name}/conftest.py` for the exchange you are testing. These fixtures are used to set up the test environment, for example funding the account with some ERC20 token. You extend these fixtures to create test cases that simulate different scenarios and verify the functionality of your code.

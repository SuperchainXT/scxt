import time


def test_odos_approval(odos_op):
    """Test the approve_token function ."""
    token = odos_op.currencies["USDC"]
    token_address = token.info["address"]
    tx_params = odos_op.approve_router(
        token_address=token_address,
        amount=1000000,
        send=False,
    )
    assert tx_params["to"] == token_address
    assert tx_params["from"] == odos_op.chain.address


def test_odos_quote(odos_op):
    """Test the get_quote function ."""
    quote = odos_op.create_order(
        symbol="ETH/USDC",
        side="buy",
        amount=100,
        order_type="market",
        send=False,
    )
    odos_op.logger.info(
        f"Quote from {quote.info['input_token']}: {quote.info['quote_response']['inAmounts']} to {quote.info['output_token']}: {quote.info['quote_response']['outAmounts']}"
    )
    assert quote.info["input_token"] == "USDC"
    assert quote.info["output_token"] == "ETH"


def test_odos_quote_timing(odos_base):
    """Test the get_quote function ."""
    times = []
    for _ in range(10):
        try:
            start_time = time.time()
            odos_base.create_order(
                symbol="ETH/USDC",
                side="buy",
                amount=100,
                order_type="market",
                params={
                    # "simple": True,
                    "source_whitelist": [
                        "Aerodrome Slipstream",
                        "Aerodrome Volatile",
                        "Uniswap V3",
                        "Uniswap V4",
                        "Wrapped Ether",
                    ],
                },
                send=False,
            )
            end_time = time.time()
            times.append(end_time - start_time)
            odos_base.logger.info(
                f"Time taken for quote: {end_time - start_time} seconds"
            )
        except Exception as e:
            odos_base.logger.error(f"Error during quote: {e}")
            continue

    average_time = sum(times) / len(times)
    odos_base.logger.info(
        f"Average time taken for {len(times)} quotes: {average_time} seconds"
    )


def test_odos_order(odos_op):
    """Test the create_order function ."""
    order = odos_op.create_order(
        symbol="ETH/USDC",
        side="sell",
        amount=1,
        order_type="market",
        send=True,
    )
    odos_op.logger.info(f"Order created: {order}")
    assert order.tx_hash is not None
    assert order.tx_params is not None

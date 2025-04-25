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
    odos_op.logger.info(f"Quote from {quote.info['input_token'] }: {quote.info['quote_response']['inAmounts']} to {quote.info['output_token']}: {quote.info['quote_response']['outAmounts']}")
    assert quote.info["input_token"] == "USDC"
    assert quote.info["output_token"] == "ETH"
    



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
    
    

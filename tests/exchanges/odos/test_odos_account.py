def test_odos_approval(odos_op):
    """Test the approve_token function ."""
    token = odos_op.currencies["WETH"]
    token_address = token.info["address"]
    tx_params = odos_op.approve_router(
        token_address=token_address,
        amount=1,
        send=False,
    )
    assert tx_params["to"] == token_address
    assert tx_params["from"] == odos_op.chain.address


def test_odos_order(odos_op):
    """Test the create_order function ."""
    order = odos_op.create_order(
        symbol="WETH/USDC",
        side="buy",
        amount=1,
        order_type="market",
        # send=True,
    )
    odos_op.logger.info(f"Order created: {order}")

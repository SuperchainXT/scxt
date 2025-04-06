def test_synthetix_v2_transfers(snx):
    """Test the deposit and withdraw function of the SynthetixV2 class."""
    snx.logger.info(f"Initial balance: {snx.fetch_balance('ETH-PERP')}")
    deposit_tx = snx.deposit(
        amount=2000,
        currency="sUSD",
        market="ETH-PERP",
        approve=True,
    )
    snx.chain.wait_for_transaction_receipt(deposit_tx)
    snx.logger.info(f"Balance after deposit: {snx.fetch_balance('ETH-PERP')}")

    withdraw_tx = snx.withdraw(
        amount=1000,
        currency="sUSD",
        market="ETH-PERP",
    )
    snx.chain.wait_for_transaction_receipt(withdraw_tx)
    snx.logger.info(f"Balance after withdraw: {snx.fetch_balance('ETH-PERP')}")


def test_synthetix_v2_order(snx):
    """Test the create_order function ."""
    position = snx.fetch_position(
        symbol="ETH-PERP",
    )
    snx.logger.info(f"Position: {position}")

    order = snx.fetch_order(
        symbol="ETH-PERP",
    )
    snx.logger.info(f"Order: {order}")

    cancel_tx = snx.cancel_order(
        symbol="ETH-PERP",
    )
    snx.chain.wait_for_transaction_receipt(cancel_tx)

    snx.create_order(
        symbol="ETH-PERP",
        side="buy",
        amount=1,
        order_type="market",
    )

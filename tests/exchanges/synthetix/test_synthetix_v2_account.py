def test_synthetix_v2_transfers(snx):
    """Test the deposit and withdraw function of the SynthetixV2 class."""
    snx.logger.info(f"Initial balance: {snx.fetch_balance('ETH-PERP')}")
    approve_tx = snx.approve_market(
        amount=2000,
        symbol="ETH-PERP",
        send=True,
    )
    snx.logger.info(f"Approval transaction: {approve_tx.hex()}")

    deposit_tx = snx.deposit(
        amount=2000,
        currency="sUSD",
        send=True,
        params={
            "market": "ETH-PERP",
        },
    )
    snx.chain.wait_for_transaction_receipt(deposit_tx)
    snx.logger.info(f"Balance after deposit: {snx.fetch_balance('ETH-PERP')}")

    withdraw_tx = snx.withdraw(
        amount=1000,
        currency="sUSD",
        send=True,
        params={
            "market": "ETH-PERP",
        },
    )
    snx.chain.wait_for_transaction_receipt(withdraw_tx)
    snx.logger.info(f"Balance after withdraw: {snx.fetch_balance('ETH-PERP')}")


def test_synthetix_v2_order(snx):
    """Test the create_order function ."""
    position = snx.fetch_position(
        symbol="ETH-PERP",
    )
    snx.logger.info(f"Position: {position}")

    snx.create_order(
        symbol="ETH-PERP",
        side="buy",
        amount=1,
        order_type="market",
        # send=True,
    )

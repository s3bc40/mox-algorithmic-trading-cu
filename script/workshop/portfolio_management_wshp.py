import boa

from boa.contracts.abi.abi_contract import ABIContract
from moccasin.config import get_active_network, Network
from script.workshop._setup_script_wshp import setup_script
from script.workshop.constants import TRADING_ARB_BALANCE
from script.workshop.deposit_wshp import run_deposit_script, deposit
from script.workshop.rebalance_wshp import (
    run_rebalance_script,
    print_token_balances,
    get_balance_status,
    get_tokens_balance_normalized,
    get_prices,
)


def moccasin_main() -> None:
    usdc, arb, _, _ = setup_script()
    active_network: Network = get_active_network()
    pool_contract: ABIContract = run_deposit_script(usdc, arb, active_network)
    a_usdc, a_arb, amount_arb_to_sell = run_rebalance_script(
        usdc, arb, active_network, pool_contract
    )

    amount = usdc.balanceOf(boa.env.eoa)
    deposit(pool_contract, usdc, amount)

    amount = TRADING_ARB_BALANCE - amount_arb_to_sell
    deposit(pool_contract, arb, amount)

    print_token_balances(usdc, arb, a_usdc, a_arb)
    usdc_price, arb_price = get_prices()
    a_usdc_balance_normalized, a_arb_balance_normalized = get_tokens_balance_normalized(
        a_arb, a_usdc
    )
    needs_rebalance, usdc_percent_allocation, arb_percent_allocation = (
        get_balance_status(
            a_usdc_balance_normalized, a_arb_balance_normalized, usdc_price, arb_price
        )
    )

    print(f"Needs rebalance: {needs_rebalance}")
    print(f"Current percent allocation USDC: {usdc_percent_allocation}")
    print(f"Current percent allocation ARB: {arb_percent_allocation}")

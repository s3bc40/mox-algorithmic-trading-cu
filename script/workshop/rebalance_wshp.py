import boa

from boa.contracts.abi.abi_contract import ABIContract
from moccasin.config import get_active_network, Network
from script.workshop._setup_script_wshp import setup_script
from script.workshop.constants import (
    BUFFER,
    TARGET_TOKEN_ALLOCATION,
    TRADING_ARB_BALANCE,
)
from typing import Tuple


def get_a_tokens_contracts(active_network: Network):
    aave_protocol_data_provider = active_network.manifest_named(
        "aave_protocol_data_provider"
    )
    print("Getting ATokens contracts from Aave...")
    a_tokens = aave_protocol_data_provider.getAllATokens()

    a_arb = None
    a_usdc = None
    for a_token in a_tokens:
        if "ARB" in a_token[0]:
            a_arb = active_network.manifest_named("arb", address=a_token[1])
        if "USDC" in a_token[0]:
            a_usdc = active_network.manifest_named("usdc", address=a_token[1])

    return (a_arb, a_usdc)


def get_price(feed_name: str) -> float:
    active_network = get_active_network()
    price_feed = active_network.manifest_named(feed_name)
    price = price_feed.latestAnswer()
    decimals = price_feed.decimals()
    decimals_normalized = 10**decimals
    return price / decimals_normalized


def get_tokens_balance_normalized(
    a_arb: ABIContract, a_usdc: ABIContract
) -> Tuple[float, float]:
    a_usdc_balance = a_usdc.balanceOf(boa.env.eoa)  # 6 decimals
    a_arb_balance = a_arb.balanceOf(boa.env.eoa)  # 18 decimals

    a_usdc_balance_normalized = a_usdc_balance / 1e6
    a_arb_balance_normalized = a_arb_balance / 1e18
    return (a_usdc_balance_normalized, a_arb_balance_normalized)


def get_prices() -> Tuple[float, float]:
    usdc_price = get_price("usdc_usd")
    arb_price = get_price("arb_usd")
    return (usdc_price, arb_price)


def get_balance_status(
    a_usdc_balance_normalized: float,
    a_arb_balance_normalized: float,
    usdc_price: float,
    arb_price: float,
) -> Tuple[bool, float, float]:
    usdc_value = a_usdc_balance_normalized * usdc_price
    arb_value = a_arb_balance_normalized * arb_price
    total_value = usdc_value + arb_value
    if total_value == 0:
        return (False, 0, 0)

    usdc_percent_allocation = usdc_value / total_value
    arb_percent_allocation = arb_value / total_value

    needs_rebalancing = (
        abs(usdc_percent_allocation - TARGET_TOKEN_ALLOCATION) > BUFFER
        or abs(arb_percent_allocation - TARGET_TOKEN_ALLOCATION) > BUFFER
    )

    return (needs_rebalancing, usdc_percent_allocation, arb_percent_allocation)


def print_token_balances(usdc, arb, a_usdc, a_arb):
    print(f"USDC balance: {usdc.balanceOf(boa.env.eoa)}")
    print(f"ARB balance: {arb.balanceOf(boa.env.eoa)}")
    print(f"aUSDC balance: {a_usdc.balanceOf(boa.env.eoa)}")
    print(f"aARB balance: {a_arb.balanceOf(boa.env.eoa)}")


def calculate_rebalancing_trades(
    usdc_data: dict,  # {"balance": float, "price": float, "contract": Contract}
    arb_data: dict,  # {"balance": float, "price": float, "contract": Contract}
    target_allocations: dict[str, float],  # {"usdc": 0.3, "arb": 0.7}
) -> dict[str, dict]:
    """
    Calculate the trades needed to rebalance a portfolio of USDC and ARB.

    Args:
        usdc_data: Dict containing USDC balance, price and contract
        arb_data: Dict containing ARB balance, price and contract
        target_allocations: Dict of token symbol to target allocation (must sum to 1)

    Returns:
        Dict of token symbol to dict containing contract and trade amount:
            {"usdc": {"contract": Contract, "trade": int},
             "arb": {"contract": Contract, "trade": int}}
    """
    # Calculate current values
    usdc_value = usdc_data["balance"] * usdc_data["price"]
    arb_value = arb_data["balance"] * arb_data["price"]
    total_value = usdc_value + arb_value

    # Calculate target values
    target_usdc_value = total_value * target_allocations["usdc"]
    target_arb_value = total_value * target_allocations["arb"]

    # Calculate trades needed in USD
    usdc_trade_usd = target_usdc_value - usdc_value
    arb_trade_usd = target_arb_value - arb_value

    # Convert to token amounts
    return {
        "usdc": {
            "contract": usdc_data["contract"],
            "trade": usdc_trade_usd / usdc_data["price"],
        },
        "arb": {
            "contract": arb_data["contract"],
            "trade": arb_trade_usd / arb_data["price"],
        },
    }


def uniswap_exactInputSingle(
    trades: dict[str, dict],
    arb: ABIContract,
    usdc: ABIContract,
    active_network: Network,
) -> int:
    uniswap_swap_router = active_network.manifest_named("uniswap-swap-router")

    arb_to_sell = trades["arb"]["trade"]
    amount_arb = abs(int(arb_to_sell * 10**18))

    arb.approve(uniswap_swap_router.address, amount_arb)

    print(amount_arb)

    min_out = int((trades["usdc"]["trade"] * (10**6)) * 0.90)

    print("Let's swap!")
    uniswap_swap_router.exactInputSingle(
        (arb.address, usdc.address, 3000, boa.env.eoa, amount_arb, min_out, 0)
    )

    print_token_balances(usdc, arb, usdc, arb)

    return amount_arb


def rebalance(
    active_network: Network,
    usdc: ABIContract,
    arb: ABIContract,
    usdc_price: float,
    arb_price: float,
    usdc_percent_allocation: float,
    arb_percent_allocation: float,
    a_usdc_balance_normalized: float,
    a_arb_balance_normalized: float,
) -> int:
    print(f"Target percent allocation USDC: {TARGET_TOKEN_ALLOCATION}")
    print(f"Target percent allocation ARB: {TARGET_TOKEN_ALLOCATION}")
    print(f"Current percent allocation USDC: {usdc_percent_allocation}")
    print(f"Current percent allocation ARB: {arb_percent_allocation}")

    usdc_data = {
        "balance": a_usdc_balance_normalized,
        "price": usdc_price,
        "contract": usdc,
    }
    arb_data = {
        "balance": a_arb_balance_normalized,
        "price": arb_price,
        "contract": arb,
    }
    target_allocations = {
        "usdc": TARGET_TOKEN_ALLOCATION,
        "arb": TARGET_TOKEN_ALLOCATION,
    }

    print("Computing trades...")
    trades = calculate_rebalancing_trades(usdc_data, arb_data, target_allocations)
    return uniswap_exactInputSingle(trades, arb, usdc, active_network)


def run_rebalance_script(
    usdc: ABIContract,
    arb: ABIContract,
    active_network: Network,
    pool_contract: ABIContract,
) -> Tuple[ABIContract, ABIContract, int]:
    a_arb, a_usdc = get_a_tokens_contracts(active_network)
    usdc_price, arb_price = get_prices()
    a_usdc_balance_normalized, a_arb_balance_normalized = get_tokens_balance_normalized(
        a_arb, a_usdc
    )

    print_token_balances(usdc, arb, a_usdc, a_arb)

    needs_rebalancing, usdc_percent_allocation, arb_percent_allocation = (
        get_balance_status(
            a_usdc_balance_normalized, a_arb_balance_normalized, usdc_price, arb_price
        )
    )

    amount_arb_to_sell = 0
    if needs_rebalancing:
        print("Rebalancing needed")
        a_arb.approve(pool_contract.address, a_arb.balanceOf(boa.env.eoa))
        pool_contract.withdraw(arb.address, TRADING_ARB_BALANCE, boa.env.eoa)

        amount_arb_to_sell = rebalance(
            active_network,
            usdc,
            arb,
            usdc_price,
            arb_price,
            usdc_percent_allocation,
            arb_percent_allocation,
            a_usdc_balance_normalized,
            a_arb_balance_normalized,
        )
        print(f"Amount ARB to sell: {amount_arb_to_sell}")
    else:
        print("Rebalancing not needed")

    return (a_usdc, a_arb, amount_arb_to_sell)


def moccasin_main():
    usdc, arb, _, _ = setup_script()
    active_network: Network = get_active_network()

    aavev3_pool_address_provider = active_network.manifest_named(
        "aavev3_pool_address_provider"
    )
    pool_address = aavev3_pool_address_provider.getPool()
    pool_contract = active_network.manifest_named("pool", address=pool_address)
    run_rebalance_script(usdc, arb, active_network, pool_contract)

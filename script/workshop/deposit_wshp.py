import boa

from boa.contracts.abi.abi_contract import ABIContract
from moccasin.config import get_active_network, Network
from script.workshop.constants import REFERAL_CODE, TRADING_ARB_BALANCE
from script.workshop._setup_script_wshp import setup_script


def deposit(pool_contract, token, amount) -> None:
    """
    Deposit `amount` of `token` into the Aave contract pool at `pool_contract`.

    :param pool_contract: The Aave contract pool to deposit into.
    :param token: The token to deposit.
    :param amount: The amount of `token` to deposit.
    :return: None
    """
    allowed_amount = token.allowance(boa.env.eoa, pool_contract.address)
    if allowed_amount < amount:
        token.approve(pool_contract.address, amount)
    print(
        f"Depositing {amount} {token.name()} into Aave contract pool {pool_contract.address}"
    )
    pool_contract.supply(token.address, amount, boa.env.eoa, REFERAL_CODE)


def run_deposit_script(
    usdc: ABIContract, arb: ABIContract, active_network: Network
) -> ABIContract:
    """
    Deposit all USDC and ARB (the forked Arbitrum token) into the Aave contract pool.

    This script is meant to be run from a fork of the Arbitrum network. It deposits all USDC and ARB
    from the current account into the Aave protocol pool on the forked network.
    """
    usdc_balance = usdc.balanceOf(boa.env.eoa)
    arb_balance = arb.balanceOf(boa.env.eoa)

    aavev3_pool_address_provider = active_network.manifest_named(
        "aavev3_pool_address_provider"
    )
    pool_address = aavev3_pool_address_provider.getPool()
    pool_contract = active_network.manifest_named("pool", address=pool_address)

    if usdc_balance > 0:
        deposit(pool_contract, usdc, usdc_balance)

    if arb_balance > 0:
        deposit(pool_contract, arb, TRADING_ARB_BALANCE)

    (
        totalCollateralBase,
        totalDebtBase,
        availableBorrowsBase,
        currentLiquidationThreshold,
        ltv,
        healthFactor,
    ) = pool_contract.getUserAccountData(boa.env.eoa)
    print(f"""User account data:
            totalCollateralBase: {totalCollateralBase}
            totalDebtBase: {totalDebtBase}
            availableBorrowsBase: {availableBorrowsBase}
            currentLiquidationThreshold: {currentLiquidationThreshold}
            ltv: {ltv}
            healthFactor: {healthFactor}
            """)
    return pool_contract


def moccasin_main() -> None:
    """
    Deposit all USDC and ARB (the forked Arbitrum token) into the Aave contract pool.

    This script is meant to be run from a fork of the Arbitrum network. It deposits all USDC and ARB
    from the current account into the Aave protocol pool on the forked network.
    """
    usdc, arb, _, _ = setup_script()
    active_network: Network = get_active_network()
    run_deposit_script(usdc, arb, active_network)

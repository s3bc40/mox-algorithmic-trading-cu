import boa

from boa.contracts.abi.abi_contract import ABIContract
from moccasin.config import get_or_initialize_config, get_active_network, Network
from script.workshop.constants import STARTING_ARB_BALANCE, STARTING_USDC_BALANCE
from typing import Tuple


def _add_token_balance(usdc: ABIContract, arb: ABIContract):
    our_address = boa.env.eoa

    print(f"Starting balance of arb: {arb.balanceOf(our_address)}")
    with boa.env.prank(arb.owner()):
        arb.transferOwnership(our_address)
    arb.mint(our_address, STARTING_ARB_BALANCE)
    print(f"Ending balance of ARB: {arb.balanceOf(our_address)}")

    print(f"Starting balance of USDC: {usdc.balanceOf(our_address)}")
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(our_address)
    usdc.configureMinter(our_address, STARTING_USDC_BALANCE)
    usdc.mint(our_address, STARTING_USDC_BALANCE)
    print(f"Ending balance of USDC: {usdc.balanceOf(our_address)}")


def setup_script() -> Tuple[ABIContract, ABIContract, ABIContract, ABIContract]:
    """
    Sets up the environment for the workshop by depositing USDC and ARB to the current account.

    This script is meant to be run from a fork of the Arbitrum network. It deposits USDC and ARB
    from the current account into the Aave protocol pool on the forked network.
    """
    print("Starting setup script...")
    config = get_or_initialize_config()
    config.set_active_network("arb-forked")
    active_network: Network = get_active_network()

    print(f"Active network: {active_network.name}")

    usdc = active_network.manifest_named("usdc")
    arb = active_network.manifest_named("arb")

    if active_network.is_local_or_forked_network():
        _add_token_balance(usdc, arb)

    return (usdc, arb, None, None)


def moccasin_main() -> Tuple[ABIContract, ABIContract, ABIContract, ABIContract]:
    return setup_script()

import boa
from boa.contracts.abi.abi_contract import ABIContract
from typing import Tuple
from moccasin.config import get_active_network, Network

STARTTING_ETH_BALANCE = int(1000e18)
STARTTING_WETH_BALANCE = int(1e18)
STARTTING_USDC_BALANCE = int(100e6)  # usdc 6 decimals!


def _add_eth_balance():
    boa.env.set_balance(boa.env.eoa, STARTTING_ETH_BALANCE)


def _add_token_balance(usdc: ABIContract, weth: ABIContract):
    our_address = boa.env.eoa

    print(f"Starting balance of WETH: {weth.balanceOf(our_address)}")
    weth.deposit(value=STARTTING_WETH_BALANCE)
    print(f"Ending balance of WETH: {weth.balanceOf(our_address)}")

    print(f"Starting balance of USDC: {usdc.balanceOf(our_address)}")
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(our_address)
    usdc.configureMinter(our_address, STARTTING_USDC_BALANCE)
    usdc.mint(our_address, STARTTING_USDC_BALANCE)
    print(f"Ending balance of USDC: {usdc.balanceOf(our_address)}")


def setup_script() -> Tuple[ABIContract, ABIContract, ABIContract, ABIContract]:
    print("Starting setup script...")
    active_network: Network = get_active_network()

    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")

    if active_network.is_local_or_forked_network():
        _add_eth_balance()
        _add_token_balance(usdc, weth)

    return (usdc, weth, None, None)


def moccasin_main():
    setup_script()

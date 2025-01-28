import boa
from boa.contracts.abi.abi_contract import ABIContract
from typing import Tuple
from moccasin.config import get_active_network, Network

STARTTING_ETH_BALANCE = int(1000e18)

def _add_eth_balance():
    boa.env.set_balance(boa.env.eoa, STARTTING_ETH_BALANCE)

def _add_token_balance(usdc: ABIContract, weth: ABIContract, active_netowrk: Network):
    pass

def setup_script() -> Tuple[ABIContract, ABIContract, ABIContract, ABIContract]:
    print("Starting setup script...")
    active_network: Network = get_active_network()

    usdc = active_network.manifest_named("usdc")
    weth = active_network.manifest_named("weth")

    if active_network.is_local_or_forked_network():
        _add_eth_balance()
        _add_token_balance(usdc, weth, active_network)


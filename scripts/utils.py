"""Utility functions"""

from brownie import (
    network,
    accounts,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)
from web3 import Web3


DECIMALS = 8
STARTING_PRICE = 200000000000
FORKED_LOCAL_ENVIRONMENTS = {"mainnet-forked", "mainnet-fork"}
LOCAL_BLOCKCHAIN_ENVIRONMENTS = {"development", "ganache-local"}
CONTRACT_TO_MOCK = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_account(index=None, id=None) -> network.account.LocalAccount:
    """Return an account based on running environment"""
    if index is not None:
        return accounts[index]
    elif id is not None:
        return accounts.load(id)
    elif (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


def deploy_mock():
    """Deploy a mock contract to a local network"""
    MockV3Aggregator.deploy(DECIMALS, STARTING_PRICE, {"from": get_account()})
    link_token = LinkToken.deploy({"from": get_account()})
    VRFCoordinatorMock.deploy(link_token.address, {"from": get_account()})


def get_contract(contract_name: str) -> network.contract.ProjectContract:
    """Grab contract from brownie config or deploy mock version of those contracts"""
    contract_type = CONTRACT_TO_MOCK[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mock()
        return contract_type[-1]

    contract_address = config["networks"][network.show_active()][contract_name]
    return Contract.from_abi(contract_type._name, contract_address, contract_type.abi)


def fund_with_link(
    contract_addr, account=None, link_token=None, amount=10000_00000_0000_0000
):  # 0.1 Link
    account = account or get_account()
    link_token = link_token or get_contract("link_token")
    # tx = link_token.transfer(contract_addr, amount, {"from": account})
    link_token_contract = interface.LinkTokenInterface(link_token.address)
    tx = link_token_contract.transfer(contract_addr, amount, {"from": account})
    tx.wait(1)
    print("Funded contract with {} LINK".format(amount))
    return tx

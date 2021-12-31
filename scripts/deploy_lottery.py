from scripts.utils import get_account, get_contract, fund_with_link
from brownie import network, accounts, config, Lottery
import time


def deploy_lottery():
    acc = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": acc},
        publish_source=config["networks"][network.show_active()].get(
            "publish_source", False
        ),
    )
    print("Deployed lottery contract at: ", lottery.address)
    return lottery

def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    start_tx = lottery.startLottery({"from": account})

    print("Started lottery")
    start_tx.wait(1)


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    entrance_fee = lottery.getEntranceFee() + 100_000_000
    tx = lottery.enter({"from": account, "value": entrance_fee})
    tx.wait(1)
    print("Entered lottery")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # need to fund the contract so it can get a random number
    fund_with_link(lottery.address)
    tx = lottery.endLottery({"from": account})
    tx.wait(1)
    time.sleep(60)
    print(f"{lottery.lastWinner()} is the winner")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()

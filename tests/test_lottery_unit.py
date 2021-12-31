from brownie import Lottery, config, network, exceptions
from scripts.utils import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    fee = lottery.getEntranceFee()
    print(fee)
    # eth ~ $4000
    expected_fee = Web3.toWei(0.025, "ether")
    assert fee == expected_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    fee = lottery.getEntranceFee()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": fee + 10000_00000})


def can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    fee = lottery.getEntranceFee()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": fee + 10000_00000})
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    fee = lottery.getEntranceFee()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": fee + 10000_00000})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    assert lottery.lotteryState() == 2  # calculating winner


def test_choose_wiiner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)

    starting_bal = account.balance()
    lottery_bal = lottery.balance()

    tx = lottery.endLottery({"from": account})
    request_id = tx.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777  # 777 % 3 == 0
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    assert lottery.lastWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_bal + lottery_bal

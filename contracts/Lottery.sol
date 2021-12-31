// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    uint256 public usdEntryFee;
    uint256 public randomness;
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lotteryState;
    uint256 public fee;
    bytes32 public keyhash;
    address payable public lastWinner;
    event RequestedRandomness(bytes32 requestId);

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        fee = _fee;
        keyhash = _keyhash;
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lotteryState = LOTTERY_STATE.CLOSED;
    }

    function enter() public payable {
        require(lotteryState == LOTTERY_STATE.OPEN, "Lottery is not open");
        // $50 min
        require(msg.value >= getEntranceFee(), "Not enough eth");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * (10**10); // 18 decimals
        uint256 costToEnter = (usdEntryFee * (10**18)) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lotteryState == LOTTERY_STATE.CLOSED,
            "Lottery is already open"
        );
        lotteryState = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        require(lotteryState == LOTTERY_STATE.OPEN, "Lottery is not open");
        // Bad way
        // uint256(
        //     keccak256(
        //         abi.encodePacked(
        //             nonce,
        //             msg.sender,
        //             block.difficulty,
        //             block.timestamp
        //         )
        //     )
        // );
        lotteryState = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lotteryState == LOTTERY_STATE.CALCULATING_WINNER,
            "Lottery is not calculating winner"
        );
        require(_randomness > 0, "Random failed");
        uint256 randomNumber = uint256(
            keccak256(abi.encodePacked(_randomness))
        );
        uint256 winnerIndex = randomNumber % players.length;
        lastWinner = players[winnerIndex];
        lastWinner.transfer(address(this).balance);
        // reset lottery
        players = new address payable[](0);
        randomness = _randomness;
        lotteryState = LOTTERY_STATE.CLOSED;
    }
}

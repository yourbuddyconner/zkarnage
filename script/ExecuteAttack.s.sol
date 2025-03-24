// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

contract ExecuteAttackScript is Script {
    // The address of the deployed attack contract
    address public attackContractAddress;
    
    function setUp() public {
        // Set the address of the deployed contract (replace with your deployed address)
        attackContractAddress = vm.envAddress("ATTACK_CONTRACT");
    }
    
    function run() external {
        // Fetch private key from environment variable
        uint256 attackerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get target contract addresses from the library
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        console.log("Using", targetContracts.length, "target contract addresses");
        console.log("First few targets:");
        for (uint i = 0; i < 5 && i < targetContracts.length; i++) {
            console.log(targetContracts[i]);
        }
        
        // Start broadcasting transactions
        vm.startBroadcast(attackerPrivateKey);
        
        // Get reference to the attack contract
        WorstCaseAttack attackContract = WorstCaseAttack(attackContractAddress);
        
        // Execute the attack
        attackContract.executeAttack(targetContracts);
        
        console.log("Attack executed against", targetContracts.length, "contracts");
        
        vm.stopBroadcast();
    }
} 
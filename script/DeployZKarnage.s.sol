// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/ZKarnage.sol";

contract DeployZKarnageScript is Script {
    function run() external {
        // Fetch private key from environment variable
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the attack contract
        ZKarnage zkarnage = new ZKarnage();
        
        // Log the deployed contract
        console.log("ZKarnage contract deployed at:", address(zkarnage));
        
        vm.stopBroadcast();
    }
}
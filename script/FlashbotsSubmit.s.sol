// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

contract FlashbotsSubmitScript is Script {
    function run() external {
        uint256 txPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get the attack contract address from environment (deployed earlier)
        address attackContractAddress;
        try vm.envAddress("ATTACK_CONTRACT") returns (address addr) {
            attackContractAddress = addr;
            console.log("Using existing attack contract:", attackContractAddress);
        } catch {
            revert("ATTACK_CONTRACT environment variable not set or invalid");
        }

        // Start broadcast to get the signed transaction
        vm.startBroadcast(txPrivateKey);
        
        // Get target contract addresses
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        bytes memory attackCalldata = abi.encodeCall(WorstCaseAttack.executeAttack, (targetContracts));
        
        vm.stopBroadcast();

        // Write each piece of data to a separate file
        vm.writeFile("contract_address.txt", vm.toString(attackContractAddress));
        vm.writeFile("transaction_data.txt", vm.toString(attackCalldata));
        
        console.log("Contract address:", attackContractAddress);
        console.log("Data written to separate files");
    }
} 
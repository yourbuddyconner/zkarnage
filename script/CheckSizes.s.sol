// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/AddressList.sol";

contract CheckSizesScript is Script {
    // Constants for gas calculations
    uint256 constant EXTCODESIZE_BASE_COST = 100;
    uint256 constant WORD_SIZE = 32;  // 32 bytes per word
    uint256 constant COLD_SLOAD_COST = 2100; // Cold storage access
    uint256 constant TARGET_GAS = 6_000_000; // Target gas usage
    
    function run() external {
        // Get target contract addresses from the library
        address[] memory targets = AddressList.getTargetAddresses();
        
        uint256 totalSize = 0;
        uint256 totalGas = 0;
        uint256 count = 0;
        
        console.log("Checking bytecode sizes and calculating gas costs...");
        console.log("------------------------------------------------");
        
        for (uint i = 0; i < targets.length; i++) {
            address target = targets[i];
            uint256 size = target.code.length;
            
            if (size > 0) {
                // Calculate gas cost for this contract
                uint256 words = (size + 31) / 32; // Round up division
                uint256 contractGas = EXTCODESIZE_BASE_COST + // Base cost
                                    COLD_SLOAD_COST +         // Cold slot access
                                    (words * 200);            // Cost per word loaded
                
                totalGas += contractGas;
                
                console.log(
                    string.concat(
                        "Contract ",
                        vm.toString(i),
                        ": ",
                        vm.toString(target),
                        "\n  Size: ",
                        vm.toString(size),
                        " bytes (",
                        vm.toString(size / 1024),
                        " KB)",
                        "\n  Gas: ",
                        vm.toString(contractGas)
                    )
                );
                totalSize += size;
                count++;
            } else {
                console.log(
                    string.concat(
                        "Contract ",
                        vm.toString(i),
                        ": ",
                        vm.toString(target),
                        " -> No code"
                    )
                );
            }
        }
        
        console.log("------------------------------------------------");
        console.log(
            string.concat(
                "Total Contracts: ",
                vm.toString(count),
                "\nTotal Size: ",
                vm.toString(totalSize),
                " bytes (",
                vm.toString(totalSize / 1024),
                " KB, ",
                vm.toString(totalSize / (1024 * 1024)),
                " MB)",
                "\nTotal Gas: ",
                vm.toString(totalGas),
                " gas"
            )
        );
        
        // Calculate how many more contracts of average size we need
        if (totalGas < TARGET_GAS && count > 0) {
            uint256 avgGasPerContract = totalGas / count;
            uint256 remainingGas = TARGET_GAS - totalGas;
            uint256 additionalContractsNeeded = (remainingGas + avgGasPerContract - 1) / avgGasPerContract; // Round up
            
            console.log("------------------------------------------------");
            console.log(
                string.concat(
                    "To reach ",
                    vm.toString(TARGET_GAS),
                    " gas target:",
                    "\nCurrent gas usage: ",
                    vm.toString(totalGas),
                    " gas (",
                    vm.toString((totalGas * 100) / TARGET_GAS),
                    "% of target)",
                    "\nAverage gas per contract: ",
                    vm.toString(avgGasPerContract),
                    "\nAdditional contracts needed: ~",
                    vm.toString(additionalContractsNeeded)
                )
            );
        }
    }
} 
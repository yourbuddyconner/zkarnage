// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/AddressList.sol";

contract CheckSizesScript is Script {
    function run() external {
        // Get target contract addresses from the library
        address[] memory targets = AddressList.getTargetAddresses();
        
        uint256 totalSize = 0;
        uint256 count = 0;
        
        console.log("Checking bytecode sizes for target contracts...");
        console.log("------------------------------------------------");
        
        for (uint i = 0; i < targets.length; i++) {
            address target = targets[i];
            uint256 size = target.code.length;
            
            if (size > 0) {
                console.log(
                    string.concat(
                        "Contract ",
                        vm.toString(i),
                        ": ",
                        vm.toString(target),
                        " -> ",
                        vm.toString(size),
                        " bytes (",
                        vm.toString(size / 1024),
                        " KB)"
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
                "Total: ",
                vm.toString(count),
                " contracts with code, totaling ",
                vm.toString(totalSize),
                " bytes (",
                vm.toString(totalSize / 1024),
                " KB, ",
                vm.toString(totalSize / (1024 * 1024)),
                " MB)"
            )
        );
    }
} 
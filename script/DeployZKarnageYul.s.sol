// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";
import {stdJson} from "../lib/forge-std/src/StdJson.sol";

contract DeployZKarnageYul is Script {
    using stdJson for string;
    
    function setUp() public {}

    function run() public {
        // Compile the contract using forge build
        string[] memory compileCmd = new string[](4);
        compileCmd[0] = "forge";
        compileCmd[1] = "build";
        compileCmd[2] = "--root";
        compileCmd[3] = ".";
        
        console.log("Compiling contract...");
        vm.ffi(compileCmd);
        
        // The artifact path for Yul files follows a specific pattern
        string memory artifactPath = "out/ZKarnage.yul/ZKarnage.json";
        
        // Read the bytecode from the artifact
        console.log("Reading artifact from:", artifactPath);
        string memory artifactJson = vm.readFile(artifactPath);
        
        // Extract bytecode from JSON
        string memory bytecodeStr = stdJson.readString(artifactJson, ".bytecode.object");
        console.log("Bytecode string:", bytecodeStr);
        
        // Convert the string to bytes, ensuring proper 0x prefix handling
        bytes memory bytecode;
        if (bytes(bytecodeStr).length > 0) {
            bytecode = vm.parseBytes(bytecodeStr);
        } else {
            revert("Failed to read bytecode from artifact");
        }
        
        console.log("Bytecode length:", bytecode.length);
        
        // Start broadcasting transactions to the network
        vm.startBroadcast();
        
        // Deploy the contract
        address zkarnageAddr;
        
        assembly {
            // Create the contract with the bytecode
            zkarnageAddr := create(0, add(bytecode, 0x20), mload(bytecode))
            if iszero(extcodesize(zkarnageAddr)) {
                revert(0, 0)
            }
        }
        
        console.log("ZKarnage.yul deployed at:", zkarnageAddr);
        
        // Stop broadcasting
        vm.stopBroadcast();
        
        // Write the address to a file for later use
        string memory addressString = vm.toString(zkarnageAddr);
        vm.writeFile("zkarnage_yul_address.txt", addressString);
        console.log("Address saved to zkarnage_yul_address.txt");
    }
} 
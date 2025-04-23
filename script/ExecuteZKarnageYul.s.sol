// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "../lib/forge-std/src/Script.sol";
import {console} from "../lib/forge-std/src/console.sol";

interface IZKarnageYul {
    function f(uint256 opCode, uint256 gasThreshold, uint256 extra) external returns (uint256);
}

contract ExecuteZKarnageYul is Script {
    // Operation codes as defined in ZKarnage.yul
    uint256 constant OP_KECCAK = 0x0003;
    uint256 constant OP_SHA256 = 0x0023;
    uint256 constant OP_ECRECOVER = 0x0021;
    uint256 constant OP_MODEXP = 0x0027;

    function setUp() public {}

    function run() public {
        // Read command-line arguments
        string memory opTypeArg = vm.envOr("OP_TYPE", string("keccak"));
        uint256 gasThreshold = vm.envOr("GAS_THRESHOLD", uint256(50000));
        address contractAddress = vm.envOr("CONTRACT_ADDRESS", address(0));
        
        // If no contract address provided, try to read from file
        if (contractAddress == address(0)) {
            try vm.readFile("zkarnage_yul_address.txt") returns (string memory addressStr) {
                contractAddress = vm.parseAddress(addressStr);
                console.log("Loaded contract address from file:", contractAddress);
            } catch {
                revert("No contract address provided. Set CONTRACT_ADDRESS env var or run DeployZKarnageYul.s.sol first.");
            }
        }
        
        // Verify the contract exists at the address
        uint256 codeSize = contractAddress.code.length;
        console.log("Contract code size at address:", codeSize);
        if (codeSize == 0) {
            revert("No contract exists at the provided address");
        }
        
        console.log("Using contract at address:", contractAddress);
        IZKarnageYul zkarnage = IZKarnageYul(contractAddress);
        
        // Parse operation type and get the corresponding code
        uint256 opCode;
        if (keccak256(bytes(opTypeArg)) == keccak256(bytes("keccak"))) {
            opCode = OP_KECCAK;
            console.log("Operation type: KECCAK256");
        } else if (keccak256(bytes(opTypeArg)) == keccak256(bytes("sha256"))) {
            opCode = OP_SHA256;
            console.log("Operation type: SHA256");
        } else if (keccak256(bytes(opTypeArg)) == keccak256(bytes("ecrecover"))) {
            opCode = OP_ECRECOVER;
            console.log("Operation type: ECRECOVER");
        } else if (keccak256(bytes(opTypeArg)) == keccak256(bytes("modexp"))) {
            opCode = OP_MODEXP;
            console.log("Operation type: MODEXP");
        } else {
            revert(string.concat("Unknown operation type: ", opTypeArg));
        }
        
        console.log("Gas threshold:", gasThreshold);
        
        // Start broadcasting
        vm.startBroadcast();
        
        // Execute the operation and measure gas usage
        console.log("Executing operation...");
        uint256 gasStart = gasleft();
        
        try zkarnage.f(opCode, gasThreshold, 0) returns (uint256 result) {
            uint256 gasUsed = gasStart - gasleft();
            console.log("Operation successful!");
            console.log("Result:", result);
            console.log("Gas used:", gasUsed);
        } catch (bytes memory reason) {
            vm.stopBroadcast();
            console.log("Operation failed!");
            console.logBytes(reason);
            revert("Operation execution failed");
        }
        
        // Stop broadcasting
        vm.stopBroadcast();
    }
} 
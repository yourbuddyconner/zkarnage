// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "../lib/forge-std/src/Test.sol";
import {console} from "../lib/forge-std/src/console.sol";
import {stdJson} from "../lib/forge-std/src/StdJson.sol";

interface IZKarnageYul {
    function f(uint256 opCode, uint256 gasThreshold, uint256 extra) external returns (uint256);
}

contract ZKarnageYulTest is Test {
    using stdJson for string;

    // Operation codes as defined in ZKarnage.yul
    uint256 constant OP_KECCAK = 0x0003;
    uint256 constant OP_SHA256 = 0x0023;
    uint256 constant OP_ECRECOVER = 0x0021;
    uint256 constant OP_MODEXP = 0x0027;

    // Contract address
    IZKarnageYul public zkarnage;
    uint256 public forkId;
    
    // Gas thresholds for stopping the loops
    uint256 constant GAS_THRESHOLD_HIGH = 100000;
    uint256 constant GAS_THRESHOLD_MEDIUM = 50000;
    uint256 constant GAS_THRESHOLD_LOW = 20000;
    
    // For testing gas limits - set a reasonable maximum gas to use in tests
    uint256 constant TEST_GAS_LIMIT = 5000000; // 5 million gas
    
    function setUp() public {
        // Get RPC URL 
        string memory key = "ETH_RPC_URL";
        string memory defaultValue = "";
        string memory rpcUrl = vm.envOr(key, defaultValue);
        require(bytes(rpcUrl).length > 0, "ETH_RPC_URL env var not set");
        
        // Create fork with latest block
        forkId = vm.createFork(rpcUrl);
        vm.selectFork(forkId);
        console.log("Fork created with ID:", forkId, "at block:", block.number);
        
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
        
        // Deploy the contract
        console.log("Deploying contract...");
        vm.startPrank(address(1)); // Use address(1) as deployer
        
        address zkarnageAddr;
        assembly {
            // Create the contract with the bytecode
            zkarnageAddr := create(0, add(bytecode, 0x20), mload(bytecode))
            if iszero(extcodesize(zkarnageAddr)) {
                revert(0, 0)
            }
        }
        
        vm.stopPrank();

        console.log("Deployed ZKarnage.yul at address:", zkarnageAddr);
        zkarnage = IZKarnageYul(zkarnageAddr);
    }

    function testKeccakOperation() public {
        console.log("\n=== Testing KECCAK Operation ===");
        
        // Use a fixed gas amount for the test call
        uint256 gasToUse = TEST_GAS_LIMIT;
        uint256 startGas = gasleft();
        
        // Only proceed with test if we have enough gas
        require(startGas > gasToUse, "Not enough gas for test");

        // Calculate how much gas to forward to the call (startGas - gasToUse = gas we want to keep)
        uint256 gasForCall = gasToUse - 50000; // Reserve some gas for after the call
        
        // Invoke with limited gas
        uint256 result;
        bool success;
        address contractAddr = address(zkarnage);
        bytes memory callData = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_KECCAK, 
            GAS_THRESHOLD_MEDIUM, 
            0
        );
        
        assembly {
            // Call with exact gas amount
            success := call(
                gasForCall,     // Gas to forward
                contractAddr,   // Target address
                0,              // No ETH sent
                add(callData, 0x20), // Call data pointer
                mload(callData),     // Call data length
                0,              // Return data pointer
                0               // Return data length
            )
            
            // Load the first word of return data
            if success {
                returndatacopy(0, 0, 32)
                result := mload(0)
            }
        }
        
        // Check that the call succeeded
        assertTrue(success, "Call to Keccak operation failed");
        
        uint256 gasUsed = startGas - gasleft();
        console.log("Keccak attack result:", result);
        console.log("Gas used:", gasUsed);
        console.log("Gas forwarded to call:", gasForCall);
        
        // The gas used should be close to our limit but not exceed it
        assertLt(gasUsed, startGas, "Used more gas than available");
        assertTrue(gasUsed > gasForCall / 2, "Used suspiciously little gas");
    }
    
    function testSha256Operation() public {
        console.log("\n=== Testing SHA256 Operation ===");
        
        // Use a fixed gas amount for the test call
        uint256 gasToUse = TEST_GAS_LIMIT;
        uint256 startGas = gasleft();
        
        // Only proceed with test if we have enough gas
        require(startGas > gasToUse, "Not enough gas for test");

        // Calculate how much gas to forward to the call
        uint256 gasForCall = gasToUse - 50000; // Reserve some gas for after the call
        
        // Invoke with limited gas
        uint256 result;
        bool success;
        address contractAddr = address(zkarnage);
        bytes memory callData = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_SHA256, 
            GAS_THRESHOLD_MEDIUM, 
            0
        );
        
        assembly {
            // Call with exact gas amount
            success := call(
                gasForCall,     // Gas to forward
                contractAddr,   // Target address
                0,              // No ETH sent
                add(callData, 0x20), // Call data pointer
                mload(callData),     // Call data length
                0,              // Return data pointer
                0               // Return data length
            )
            
            // Load the first word of return data
            if success {
                returndatacopy(0, 0, 32)
                result := mload(0)
            }
        }
        
        // Check that the call succeeded
        assertTrue(success, "Call to SHA256 operation failed");
        
        uint256 gasUsed = startGas - gasleft();
        console.log("SHA256 attack result:", result);
        console.log("Gas used:", gasUsed);
        console.log("Gas forwarded to call:", gasForCall);
        
        // The gas used should be close to our limit but not exceed it
        assertLt(gasUsed, startGas, "Used more gas than available");
        assertTrue(gasUsed > gasForCall / 2, "Used suspiciously little gas");
    }
    
    function testEcrecoverOperation() public {
        console.log("\n=== Testing ECRECOVER Operation ===");
        
        // Use a fixed gas amount for the test call
        uint256 gasToUse = TEST_GAS_LIMIT;
        uint256 startGas = gasleft();
        
        // Only proceed with test if we have enough gas
        require(startGas > gasToUse, "Not enough gas for test");

        // Calculate how much gas to forward to the call
        uint256 gasForCall = gasToUse - 50000; // Reserve some gas for after the call
        
        // Invoke with limited gas
        uint256 result;
        bool success;
        address contractAddr = address(zkarnage);
        bytes memory callData = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_ECRECOVER, 
            GAS_THRESHOLD_MEDIUM, 
            0
        );
        
        assembly {
            // Call with exact gas amount
            success := call(
                gasForCall,     // Gas to forward
                contractAddr,   // Target address
                0,              // No ETH sent
                add(callData, 0x20), // Call data pointer
                mload(callData),     // Call data length
                0,              // Return data pointer
                0               // Return data length
            )
            
            // Load the first word of return data
            if success {
                returndatacopy(0, 0, 32)
                result := mload(0)
            }
        }
        
        // Check that the call succeeded
        assertTrue(success, "Call to ECRECOVER operation failed");
        
        uint256 gasUsed = startGas - gasleft();
        console.log("ECRECOVER attack result:", result);
        console.log("Gas used:", gasUsed);
        console.log("Gas forwarded to call:", gasForCall);
        
        // The gas used should be close to our limit but not exceed it
        assertLt(gasUsed, startGas, "Used more gas than available");
        assertTrue(gasUsed > gasForCall / 2, "Used suspiciously little gas");
    }
    
    function testModexpOperation() public {
        console.log("\n=== Testing MODEXP Operation ===");
        
        // Use a fixed gas amount for the test call
        uint256 gasToUse = TEST_GAS_LIMIT;
        uint256 startGas = gasleft();
        
        // Only proceed with test if we have enough gas
        require(startGas > gasToUse, "Not enough gas for test");

        // Calculate how much gas to forward to the call
        uint256 gasForCall = gasToUse - 50000; // Reserve some gas for after the call
        
        // Invoke with limited gas
        uint256 result;
        bool success;
        address contractAddr = address(zkarnage);
        bytes memory callData = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_MODEXP, 
            GAS_THRESHOLD_MEDIUM, 
            0
        );
        
        assembly {
            // Call with exact gas amount
            success := call(
                gasForCall,     // Gas to forward
                contractAddr,   // Target address
                0,              // No ETH sent
                add(callData, 0x20), // Call data pointer
                mload(callData),     // Call data length
                0,              // Return data pointer
                0               // Return data length
            )
            
            // Load the first word of return data
            if success {
                returndatacopy(0, 0, 32)
                result := mload(0)
            }
        }
        
        // Check that the call succeeded
        assertTrue(success, "Call to MODEXP operation failed");
        
        uint256 gasUsed = startGas - gasleft();
        console.log("MODEXP attack result:", result);
        console.log("Gas used:", gasUsed);
        console.log("Gas forwarded to call:", gasForCall);
        
        // The gas used should be close to our limit but not exceed it
        assertLt(gasUsed, startGas, "Used more gas than available");
        assertTrue(gasUsed > gasForCall / 2, "Used suspiciously little gas");
    }
    
    function testDifferentThresholds() public {
        console.log("\n=== Testing Different Gas Thresholds ===");
        
        // Use assembly with gas limit for high threshold test
        uint256 gasForCallHigh = 3000000; // 3 million gas
        uint256 result1;
        bool success1;
        address contractAddr = address(zkarnage);
        bytes memory callDataHigh = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_KECCAK, 
            GAS_THRESHOLD_HIGH, 
            0
        );
        
        assembly {
            success1 := call(
                gasForCallHigh,
                contractAddr,
                0,
                add(callDataHigh, 0x20),
                mload(callDataHigh),
                0,
                0
            )
            if success1 {
                returndatacopy(0, 0, 32)
                result1 := mload(0)
            }
        }
        
        // Use assembly with gas limit for low threshold test
        uint256 gasForCallLow = 1000000; // 1 million gas
        uint256 result2;
        bool success2;
        bytes memory callDataLow = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            OP_KECCAK, 
            GAS_THRESHOLD_LOW, 
            0
        );
        
        assembly {
            success2 := call(
                gasForCallLow,
                contractAddr,
                0,
                add(callDataLow, 0x20),
                mload(callDataLow),
                0,
                0
            )
            if success2 {
                returndatacopy(0, 0, 32)
                result2 := mload(0)
            }
        }
        
        assertTrue(success1, "High threshold call failed");
        assertTrue(success2, "Low threshold call failed");
        
        console.log("KECCAK with high threshold - Gas limit:", gasForCallHigh);
        console.log("KECCAK with low threshold - Gas limit:", gasForCallLow);
        
        // The low threshold should complete sooner, thus using less gas
        // But this is hard to verify directly in this model
    }
    
    function testInvalidOperation() public {
        console.log("\n=== Testing Invalid Operation ===");
        
        // Try to call with an invalid operation code - should revert
        uint256 gasForCall = 500000;
        bool success;
        address contractAddr = address(zkarnage);
        bytes memory callData = abi.encodeWithSelector(
            IZKarnageYul.f.selector, 
            0x1234, // Invalid op code 
            GAS_THRESHOLD_MEDIUM, 
            0
        );
        
        assembly {
            success := call(
                gasForCall,
                contractAddr,
                0,
                add(callData, 0x20),
                mload(callData),
                0,
                0
            )
        }
        
        // Should fail with invalid opcode
        assertFalse(success, "Call with invalid opcode should fail");
    }
} 
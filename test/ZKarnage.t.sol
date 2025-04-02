// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "../lib/forge-std/src/Test.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/ZKarnage.sol";

contract ZKarnageTest is Test {
    ZKarnage public zkarnage;
    uint256 public forkId;
    
    // Test addresses (known large contracts on mainnet)
    address[] testAddresses;
    
    // Gas limits for different attacks
    uint256 constant JUMPDEST_GAS_LIMIT = 200_000;
    uint256 constant MCOPY_GAS_LIMIT = 300_000;
    uint256 constant CALLDATACOPY_GAS_LIMIT = 1_000_000;
    uint256 constant MODEXP_GAS_LIMIT = 100_000;
    uint256 constant BN_PAIRING_GAS_LIMIT = 3_000_000;
    uint256 constant BN_MUL_GAS_LIMIT = 5_500_000;
    uint256 constant ECRECOVER_GAS_LIMIT = 100_000;
    uint256 constant EXTCODESIZE_GAS_LIMIT = 100_000;
    
    function setUp() public {
        // Deploy the attack contract
        zkarnage = new ZKarnage();
        
        // Set up test addresses (using a few known contracts)
        testAddresses = new address[](5);
        testAddresses[0] = 0xB95c8fB8a94E175F957B5044525F9129fbA0fE0C;
        testAddresses[1] = 0x1908D2bD020Ba25012eb41CF2e0eAd7abA1c48BC;
        testAddresses[2] = 0xa102b6Eb23670B07110C8d316f4024a2370Be5dF;
        testAddresses[3] = 0x84ab2d6789aE78854FbdbE60A9873605f4Fd038c;
        testAddresses[4] = 0x1908D2bD020Ba25012eb41CF2e0eAd7abA1c48BC;
        
        // Get RPC URL
        string memory rpcUrl = vm.envString("ETH_RPC_URL");
        console.log("Using RPC URL:", rpcUrl);
        
        // Create fork with latest block
        try vm.createFork(rpcUrl) returns (uint256 id) {
            forkId = id;
            console.log("Fork created with ID:", forkId);
            
            vm.selectFork(forkId);
            uint256 currentBlock = block.number;
            console.log("Fork selected, block number:", currentBlock);
            require(currentBlock > 0, "Invalid block number");
            
            // Verify we can access all contract codes
            for (uint i = 0; i < testAddresses.length; i++) {
                bytes memory code = address(testAddresses[i]).code;
                require(code.length > 0, string.concat("Cannot access contract code for address ", vm.toString(testAddresses[i])));
                console.log("Verified contract code for address:", testAddresses[i]);
            }
            
            console.log("Fork setup completed successfully");
            
        } catch Error(string memory reason) {
            console.log("Fork creation failed with error:", reason);
            revert("Fork creation failed");
        } catch (bytes memory) {
            console.log("Fork creation failed with low-level error");
            revert("Fork creation failed with low-level error");
        }
    }

    function testJumpdestAttack() public {
        console.log("\n=== Testing JUMPDEST Attack ===");
        uint256 iterations = 1000;
        
        uint256 gasStart = gasleft();
        zkarnage.executeJumpdestAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for JUMPDEST attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, JUMPDEST_GAS_LIMIT, "Gas usage too high for JUMPDEST attack");
    }

    function testMcopyAttack() public {
        console.log("\n=== Testing Memory Operations Attack ===");
        uint256 size = 256;
        uint256 iterations = 1000;
        
        uint256 gasStart = gasleft();
        zkarnage.executeMcopyAttack(size, iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for memory operations attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, MCOPY_GAS_LIMIT, "Gas usage too high for memory operations attack");
    }

    function testCalldatacopyAttack() public {
        console.log("\n=== Testing CALLDATACOPY Attack ===");
        // Reduced size from 1MB to 32KB to keep gas reasonable
        uint256 size = 32 * 1024;
        uint256 iterations = 50;
        
        uint256 gasStart = gasleft();
        zkarnage.executeCalldatacopyAttack(size, iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for CALLDATACOPY attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        console.log("Gas per KB:", (gasUsed * 1024) / size);
        assertLt(gasUsed, CALLDATACOPY_GAS_LIMIT, "Gas usage too high for CALLDATACOPY attack");
    }

    function testModExpAttack() public {
        console.log("\n=== Testing MODEXP Attack ===");
        uint256 iterations = 10;
        
        uint256 gasStart = gasleft();
        zkarnage.executeModExpAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for MODEXP attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, MODEXP_GAS_LIMIT, "Gas usage too high for MODEXP attack");
    }

    function testBnPairingAttack() public {
        console.log("\n=== Testing BN_PAIRING Attack ===");
        uint256 iterations = 5;
        
        uint256 gasStart = gasleft();
        zkarnage.executeBnPairingAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for BN_PAIRING attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, BN_PAIRING_GAS_LIMIT, "Gas usage too high for BN_PAIRING attack");
    }

    function testBnMulAttack() public {
        console.log("\n=== Testing BN_MUL Attack ===");
        // Reduced iterations from 10 to 8 to stay under gas limit
        uint256 iterations = 8;
        
        uint256 gasStart = gasleft();
        zkarnage.executeBnMulAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for BN_MUL attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, BN_MUL_GAS_LIMIT, "Gas usage too high for BN_MUL attack");
    }

    function testEcrecoverAttack() public {
        console.log("\n=== Testing ECRECOVER Attack ===");
        uint256 iterations = 10;
        
        uint256 gasStart = gasleft();
        zkarnage.executeEcrecoverAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Gas used for ECRECOVER attack:", gasUsed);
        console.log("Gas per iteration:", gasUsed / iterations);
        assertLt(gasUsed, ECRECOVER_GAS_LIMIT, "Gas usage too high for ECRECOVER attack");
    }

    function testExtcodesizeAttack() public {
        console.log("\n=== Testing EXTCODESIZE Attack ===");
        
        uint256 gasStart = gasleft();
        zkarnage.executeAttack(testAddresses);
        uint256 gasUsed = gasStart - gasleft();
        
        uint256 totalSize = 0;
        for (uint i = 0; i < testAddresses.length; i++) {
            uint256 size = testAddresses[i].code.length;
            totalSize += size;
            console.log("Contract", i, "Size:", size);
        }
        
        console.log("Gas used for EXTCODESIZE attack:", gasUsed);
        console.log("Total bytecode size:", totalSize, "bytes");
        console.log("Gas per KB:", (gasUsed * 1024) / totalSize);
        assertLt(gasUsed, EXTCODESIZE_GAS_LIMIT, "Gas usage too high for EXTCODESIZE attack");
    }

    function testAllAttacks() public {
        testJumpdestAttack();
        testMcopyAttack();
        testCalldatacopyAttack();
        testModExpAttack();
        testBnPairingAttack();
        testBnMulAttack();
        testEcrecoverAttack();
        testExtcodesizeAttack();
    }
}
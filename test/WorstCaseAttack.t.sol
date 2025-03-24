// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "../lib/forge-std/src/Test.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/WorstCaseAttack.sol";

contract WorstCaseAttackTest is Test {
    WorstCaseAttack public attackContract;
    uint256 public forkId;
    
    // Test addresses (known large contracts on mainnet)
    address[] testAddresses;
    
    function setUp() public {
        // Deploy the attack contract
        attackContract = new WorstCaseAttack();
        
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
            
            // Select the fork regardless of ID
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
    
    function testAttackGasConsumption() public {
        // Verify fork is working by checking block number
        uint256 currentBlock = block.number;
        require(currentBlock > 0, "Fork not working - invalid block number");
        console.log("Running test at block:", currentBlock);
        
        // Measure gas consumption for the attack
        uint256 gasStart = gasleft();
        attackContract.executeAttack(testAddresses);
        uint256 gasUsed = gasStart - gasleft();
        
        // Log results
        console.log("Gas used for attack execution:", gasUsed);
        
        // Get bytecode sizes for reference
        uint256 totalSize = 0;
        for (uint i = 0; i < testAddresses.length; i++) {
            uint256 size = testAddresses[i].code.length;
            totalSize += size;
            console.log("Contract", i);
            console.log("Size:", size);
        }
        
        console.log("Total bytecode size:", totalSize, "bytes");
        console.log("Gas per KB:", (gasUsed * 1024) / totalSize);
        
        // Make sure the gas is reasonable (this will need calibration)
        // This is a starting point, adjust based on your findings
        assertLt(gasUsed, 5_000_000, "Gas usage too high");
    }
    
    function testAttackWithCopy() public {
        // Verify fork is working by checking block number
        uint256 currentBlock = block.number;
        require(currentBlock > 0, "Fork not working - invalid block number");
        console.log("Running test at block:", currentBlock);
        
        // Measure gas consumption for the attack with copy
        uint256 gasStart = gasleft();
        attackContract.executeAttackWithCopy(testAddresses);
        uint256 gasUsed = gasStart - gasleft();
        
        // Log results
        console.log("Gas used for attack with copy execution:", gasUsed);
        
        // Get bytecode sizes for reference
        uint256 totalSize = 0;
        for (uint i = 0; i < testAddresses.length; i++) {
            console.log("Contract", i);
            uint256 size = testAddresses[i].code.length;
            console.log("Size:", size);
            totalSize += size;
        }
        
        console.log("Total bytecode size:", totalSize, "bytes");
        console.log("Gas per KB with copy:", (gasUsed * 1024) / totalSize);
        
        // Compare with normal attack
        uint256 gasStartNormal = gasleft();
        attackContract.executeAttack(testAddresses);
        uint256 gasUsedNormal = gasStartNormal - gasleft();
        
        console.log("Gas used for normal attack:", gasUsedNormal);
        console.log("Gas difference (copy - normal):", gasUsed > gasUsedNormal ? gasUsed - gasUsedNormal : 0);
        console.log("Gas per KB normal:", (gasUsedNormal * 1024) / totalSize);
        
        // Make sure the gas is reasonable
        assertLt(gasUsed, 5_000_000, "Gas usage too high for copy attack");
        assertLt(gasUsedNormal, 5_000_000, "Gas usage too high for normal attack");
    }
} 
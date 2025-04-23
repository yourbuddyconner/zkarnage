// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "../lib/forge-std/src/Test.sol";
import {console} from "../lib/forge-std/src/console.sol";
import "../src/ZKarnage.sol";

contract ZKarnageTest is Test {
    ZKarnage public zkarnage;
    uint256 public forkId;
    
    // --- Local Event Definitions (to satisfy vm.expectEmit syntax) ---
    // These must match the signatures in ZKarnage.sol exactly.
    event OpcodeResult(string name, uint256 gasUsed);
    event PrecompileResult(string name, uint256 gasUsed);
    event AttackSummary(uint256 numContracts, uint256 totalSize);
    // ContractAccessed event is not explicitly checked here, but could be added if needed.
    // event ContractAccessed(address indexed target, uint256 size);

    // Test addresses (known large contracts on mainnet)
    address[] testAddresses;
    
    // Gas limits for different attacks (Adjust as needed based on runs)
    uint256 constant JUMPDEST_GAS_LIMIT = 200_000;
    uint256 constant MCOPY_GAS_LIMIT = 300_000;
    uint256 constant CALLDATACOPY_GAS_LIMIT = 1_000_000;
    uint256 constant MODEXP_GAS_LIMIT = 500_000;
    uint256 constant BN_PAIRING_GAS_LIMIT = 5_000_000;
    uint256 constant BN_MUL_GAS_LIMIT = 5_500_000;
    uint256 constant ECRECOVER_GAS_LIMIT = 500_000;
    uint256 constant EXTCODESIZE_GAS_LIMIT = 100_000;
    uint256 constant KECCAK_GAS_LIMIT = 2_000_000;
    uint256 constant SHA256_GAS_LIMIT = 2_000_000;
    
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
        
        // Get RPC URL - Use string explicitly for envOr
        string memory key = "ETH_RPC_URL";
        string memory defaultValue = "";
        string memory rpcUrl = vm.envOr(key, defaultValue);
        require(bytes(rpcUrl).length > 0, "ETH_RPC_URL env var not set");
        console.log("Using RPC URL from ETH_RPC_URL"); // Avoid logging the URL itself
        
        // Create fork with latest block
        forkId = vm.createFork(rpcUrl);
        vm.selectFork(forkId);
        console.log("Fork created with ID:", forkId, "at block:", block.number);
        
        // Optional: Verify contract code access after fork selection
        // It's good practice but can be verbose, uncomment if needed
        /*
        for (uint i = 0; i < testAddresses.length; i++) {
            bytes memory code = address(testAddresses[i]).code;
            require(code.length > 0, string.concat("Cannot access contract code for address ", vm.toString(testAddresses[i])));
        }
        console.log("Verified contract code access on fork.");
        */
    }

    function testJumpdestAttack() public {
        console.log("\n=== Testing JUMPDEST Attack ===");
        uint256 iterations = 1000;
        
        uint256 gasStart = gasleft();
        // Expect OpcodeResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit OpcodeResult("JUMPDEST", 0);
        zkarnage.executeJumpdestAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for JUMPDEST attack tx:", gasUsed);
        if (iterations > 0) {
             console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, JUMPDEST_GAS_LIMIT, "Gas usage too high for JUMPDEST attack");
    }

    function testMcopyAttack() public {
        console.log("\n=== Testing Memory Operations (MCOPY) Attack ===");
        uint256 size = 256;
        uint256 iterations = 1000;
        
        uint256 gasStart = gasleft();
        // Expect OpcodeResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit OpcodeResult("MCOPY", 0);
        zkarnage.executeMcopyAttack(size, iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for memory operations attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, MCOPY_GAS_LIMIT, "Gas usage too high for memory operations attack");
    }

    function testCalldatacopyAttack() public {
        console.log("\n=== Testing CALLDATACOPY Attack ===");
        uint256 size = 32 * 1024; // 32KB
        uint256 iterations = 50;
        
        uint256 gasStart = gasleft();
        // Expect OpcodeResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit OpcodeResult("CALLDATACOPY", 0);
        zkarnage.executeCalldatacopyAttack(size, iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for CALLDATACOPY attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        console.log("Gas per KB (external):", (gasUsed * 1024) / size);
        assertLt(gasUsed, CALLDATACOPY_GAS_LIMIT, "Gas usage too high for CALLDATACOPY attack");
    }

    function testModExpAttack() public {
        console.log("\n=== Testing MODEXP Attack ===");
        uint256 iterations = 10;
        
        uint256 gasStart = gasleft();
        // Expect PrecompileResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit PrecompileResult("MODEXP", 0);
        zkarnage.executeModExpAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for MODEXP attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, MODEXP_GAS_LIMIT, "Gas usage too high for MODEXP attack");
    }

    function testBnPairingAttack() public {
        console.log("\n=== Testing BN_PAIRING Attack ===");
        uint256 iterations = 5;
        
        uint256 gasStart = gasleft();
         // Expect PrecompileResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit PrecompileResult("BN_PAIRING", 0);
        zkarnage.executeBnPairingAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for BN_PAIRING attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, BN_PAIRING_GAS_LIMIT, "Gas usage too high for BN_PAIRING attack");
    }

    function testBnMulAttack() public {
        console.log("\n=== Testing BN_MUL Attack ===");
        uint256 iterations = 8;
        
        uint256 gasStart = gasleft();
        // Expect PrecompileResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit PrecompileResult("BN_MUL", 0);
        zkarnage.executeBnMulAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for BN_MUL attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, BN_MUL_GAS_LIMIT, "Gas usage too high for BN_MUL attack");
    }

    function testEcrecoverAttack() public {
        console.log("\n=== Testing ECRECOVER Attack ===");
        uint256 iterations = 50; // Increased iterations
        
        uint256 gasStart = gasleft();
        // Expect PrecompileResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit PrecompileResult("ECRECOVER", 0);
        zkarnage.executeEcrecoverAttack(iterations);
        uint256 gasUsed = gasStart - gasleft();
        
        console.log("Total Gas used for ECRECOVER attack tx:", gasUsed);
        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, ECRECOVER_GAS_LIMIT, "Gas usage too high for ECRECOVER attack");
    }
    
    function testKeccakAttack() public {
        console.log("\n=== Testing KECCAK256 Attack ===");
        uint256 iterations = 1000;
        uint256 dataSize = 1024; // 1 KB

        uint256 gasStart = gasleft();
        // Expect OpcodeResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit OpcodeResult("KECCAK256", 0);
        zkarnage.executeKeccakAttack(iterations, dataSize);
        uint256 gasUsed = gasStart - gasleft();

        // Broke down the log statement
        console.log("Total Gas used for KECCAK256 attack tx:");
        console.log("- Iterations:", iterations);
        console.log("- Data Size:", dataSize);
        console.log("- Gas Used:", gasUsed);

        if (iterations > 0) {
            console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, KECCAK_GAS_LIMIT, "Gas usage too high for KECCAK256 attack");
    }

    function testSha256Attack() public {
        console.log("\n=== Testing SHA256 Attack ===");
        uint256 iterations = 1000;
        uint256 dataSize = 1024; // 1 KB

        uint256 gasStart = gasleft();
        // Expect PrecompileResult event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit PrecompileResult("SHA256", 0);
        zkarnage.executeSha256Attack(iterations, dataSize);
        uint256 gasUsed = gasStart - gasleft();

        // Broke down the log statement
        console.log("Total Gas used for SHA256 attack tx:");
        console.log("- Iterations:", iterations);
        console.log("- Data Size:", dataSize);
        console.log("- Gas Used:", gasUsed);

        if (iterations > 0) {
             console.log("Approx Gas per iteration (external):", gasUsed / iterations);
        }
        assertLt(gasUsed, SHA256_GAS_LIMIT, "Gas usage too high for SHA256 attack");
    }

    function testExtcodesizeAttack() public {
        console.log("\n=== Testing EXTCODESIZE Attack ===");
        
        uint256 gasStart = gasleft();
        // Expect AttackSummary event (only check emitter)
        vm.expectEmit(false, false, false, false, address(zkarnage));
        // Provide the expected event signature template
        emit AttackSummary(testAddresses.length, 0);
        zkarnage.executeAttack(testAddresses);
        uint256 gasUsed = gasStart - gasleft();
        
        uint256 totalSize = 0;
        for (uint i = 0; i < testAddresses.length; i++) {
            uint256 size = testAddresses[i].code.length;
            totalSize += size;
            // console.log("Contract", i, "Size:", size); // Uncomment for debugging
        }
        
        console.log("Total Gas used for EXTCODESIZE attack tx:", gasUsed);
        console.log("Total bytecode size accessed:", totalSize, "bytes");
        if (totalSize > 0) {
            console.log("Gas per KB (external):", (gasUsed * 1024) / totalSize);
        }
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
        testKeccakAttack();
        testSha256Attack();
        testExtcodesizeAttack();
    }
}
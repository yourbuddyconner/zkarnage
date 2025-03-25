<div align="center">

# ZKarnage
### Stress Testing ZK Systems Through Maximum Pain

This project implements a worst-case attack on Ethereum provers, specifically targeting the computational overhead required for generating zero-knowledge proofs for blocks. The attack exploits the cost of keccak hashing operations by forcing the EVM to load large contract bytecode into memory.

</div>

![circuit header](zkarnage.png)

> Credit: Original attack vector concept by [@ignaciohagopian](https://x.com/ignaciohagopian) from the Ethereum Foundation

## Background

Zero-knowledge proof systems that verify Ethereum blocks must perform keccak hash operations for every piece of data loaded from state. Contract bytecode is particularly expensive to prove because:

1. When contract code is accessed via `EXTCODESIZE`, the EVM loads the full bytecode
2. The loaded bytecode must be hashed with keccak-256 
3. ZK circuits for keccak are expensive to construct and verify

The attack targets blocks where block number % 100 == 0, as these are the blocks that [Ethproof provers](https://ethproofs.org/) focus on generating proofs for. Currently, these proofs:
- Take ~4-14 minutes to generate per block
- Cost $0.07-1.29 per proof depending on the prover
- Process blocks using ~30M gas on average

This makes them particularly susceptible to targeted worst-case scenarios.

## Attack Vector Analysis

The current implementation focuses on exploiting the high cost of Keccak hashing in ZK circuits. By forcing the prover to process ~45MiB of contract bytecode through EXTCODESIZE operations, we create a significant computational burden while keeping gas costs reasonable.

A particularly promising future direction is exploiting precompiled contracts, especially MODEXP. Precompiles are extremely expensive for ZK provers (often 100-1000x more costly to prove than their gas cost suggests) but have fixed gas costs. For example, a MODEXP operation costing 3,000 gas could generate millions of constraints in a ZK circuit.

The most effective approach would likely combine multiple vectors - for instance, using EXTCODESIZE on large contracts while also calling MODEXP precompiles with carefully selected large exponents and moduli. This would maximize the "proof stress to gas cost" ratio while staying within reasonable transaction fee limits.

### Technical Deep Dive: EXTCODESIZE Attack

The current attack implementation exploits the high cost of Keccak hashing in ZK circuits by forcing the EVM to load large contract bytecode through EXTCODESIZE operations. Here's how it works:

### Attack Mechanism
1. **Target Selection**: The attack targets 6 large contracts on mainnet, each with significant bytecode size
2. **Operation**: Uses `EXTCODESIZE` to force the EVM to load the full bytecode of each contract
3. **ZK Impact**: Each bytecode load requires:
   - Merkle Patricia trie lookups
   - Keccak-256 hashing of the bytecode
   - Complex memory management in ZK circuits

### Implementation Details
```solidity
function executeAttack(address[] calldata targets) external {
    uint256 totalSize = 0;
    
    for (uint256 i = 0; i < targets.length; i++) {
        address target = targets[i];
        
        // Force the EVM to load the contract bytecode via EXTCODESIZE
        uint256 size = target.code.length;
        totalSize += size;
        
        emit ContractAccessed(target, size);
    }
    
    emit AttackSummary(targets.length, totalSize);
}
```

### Why It's Effective for ZK Stress Testing
1. **Asymmetric Complexity**: Gas costs are minimal (~408 gas/KB) while ZK circuit complexity is high
2. **Linear Scaling**: Each contract adds its full bytecode size to the proof complexity
3. **Memory Intensive**: Forces ZK circuits to handle large memory operations
4. **No Circuit Optimizations**: Keccak hashing is inherently expensive to prove

### Performance Metrics
- Total bytecode loaded: ~45MiB across 6 contracts
- Gas consumption: ~39,000 gas (normal attack)
- Gas per KB: ~408 gas/KB
- Additional overhead with EXTCODECOPY: ~25,700 gas

### Target Contracts
The attack targets carefully selected large contracts on mainnet:
```solidity
address[] memory targets = new address[](6);
targets[0] = 0x1908D2bD020Ba25012eb41CF2e0eAd7abA1c48BC;
targets[1] = 0xa102b6Eb23670B07110C8d316f4024a2370Be5dF;
targets[2] = 0x84ab2d6789aE78854FbdbE60A9873605f4Fd038c;
targets[3] = 0xfd96A06c832f5F2C0ddf4ba4292988Dc6864f3C5;
targets[4] = 0xE233472882bf7bA6fd5E24624De7670013a079C1;
targets[5] = 0xd3A3d92dbB569b6cd091c12fAc1cDfAEB8229582;
```

### Future Improvements
1. **Contract Selection**: Expand target list to include more large contracts
2. **Operation Mixing**: Combine with other expensive ZK operations
3. **Timing Optimization**: Target specific blocks for maximum impact
4. **Gas Efficiency**: Further optimize gas usage while maintaining ZK complexity

## Project Structure

```
zkarnage/
├── src/                    # Source code
│   ├── WorstCaseAttack.sol    # Main attack contract implementation
│   └── AddressList.sol        # Library containing target contract addresses
├── script/                 # Deployment and execution scripts
│   ├── DeployAttack.s.sol     # Deploy the attack contract
│   ├── ExecuteAttack.s.sol    # Execute the attack with target addresses
│   ├── CheckSizes.s.sol       # Verify bytecode sizes of target contracts
│   ├── DeployAndAttack.s.sol  # Combined deploy & attack script
│   ├── FlashbotsSubmit.s.sol  # Prepare transaction data for Flashbots
│   └── submit_bundle.py       # Python script for Flashbots bundle submission
├── test/                  # Test files
│   └── WorstCaseAttack.t.sol  # Tests for attack contract functionality
├── out/                   # Output files
│   └── flashbots_data.json    # Flashbots transaction data
├── broadcast/             # Deployment transaction data
├── lib/                   # Dependencies
│   └── forge-std/            # Foundry standard library
├── .env.example          # Example environment variables
├── foundry.toml          # Foundry configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Key Components

- **Attack Contract**: Implements the EXTCODESIZE-based attack vector
- **Address Library**: Maintains list of target contracts with large bytecode
- **Deployment Scripts**: Handle contract deployment and attack execution
- **Flashbots Integration**: Ensures transaction inclusion in target blocks
- **Test Suite**: Validates attack effectiveness and gas consumption

## Setup

1. Install Foundry:
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. Clone this repo:
   ```bash
   git clone https://github.com/yourbuddyconner/zkarnage
   cd zkarnage
   ```

3. Install dependencies:
   ```bash
   forge install
   pip install -r requirements.txt
   ```

4. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # - ETH_RPC_URL: Your Ethereum node URL
   # - PRIVATE_KEY: Your private key (without 0x prefix)
   # - FLASHBOTS_RELAY_URL: Optional custom Flashbots relay URL
   ```

## Usage

### Check Contract Sizes

To verify the size of the target contracts:

```bash
forge script script/CheckSizes.s.sol --rpc-url $ETH_RPC_URL
```

### Submit Attack Bundle to Flashbots

To submit the attack bundle to Flashbots:

1. First, generate the transaction data:
```bash
forge script script/FlashbotsSubmit.s.sol --rpc-url $ETH_RPC_URL
```

2. Then submit the bundle to Flashbots:
```bash
python3 script/submit_bundle.py
```

The Python script will:
- Read the transaction data from the Foundry output
- Sign and package the transaction into a Flashbots bundle
- Submit the bundle to the Flashbots relay
- Wait for and report bundle inclusion status

You can target a specific block by setting the `TARGET_BLOCK` environment variable:
```bash
TARGET_BLOCK=1234567 forge script script/FlashbotsSubmit.s.sol --rpc-url $ETH_RPC_URL
```

### Deploy and Execute Normally (Non-Flashbots)

For testing or if you don't need Flashbots, you can deploy and execute the attack directly:

```bash
forge script script/DeployAndAttack.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

## Testing

Run the tests to measure gas consumption and effectiveness:

```bash
# Set your Ethereum RPC URL for forking mainnet
export ETH_RPC_URL="https://eth-mainnet.alchemyapi.io/v2/YOUR_API_KEY"

# Run tests with verbose output
forge test -vvvv
```

### Test Configuration

The tests require proper setup in `foundry.toml`:
```toml
[profile.default]
evm_version = "paris"  # Required for consistent fork testing
ffi = true            # Enable fork testing
test_timeout = 100000 # Increased timeout for fork tests

[rpc_endpoints]
mainnet = "${ETH_RPC_URL}"
```

### Test Results

The tests measure gas consumption for two attack variants:

1. Normal Attack:
   - Gas usage: ~39,000 gas
   - Gas per KB: ~408 gas/KB
   - Total bytecode loaded: 98,304 bytes (4 contracts × 24,576 bytes)

2. Attack with Copy:
   - Gas usage: ~40,000 gas
   - Gas per KB: ~420 gas/KB
   - Additional overhead: ~25,700 gas compared to normal attack

Both attack variants successfully load and process large contract bytecode while staying well under the block gas limit. The tests verify:
- Successful mainnet forking
- Access to contract bytecode
- Gas consumption measurements
- Comparison between attack variants

## Network Resilience Testing

This project demonstrates an important principle for decentralized networks:

1. Ethereum is a permissionless network where any theoretically supported operation is fair game
2. This research does not compromise user funds or exploit vulnerabilities - it simply utilizes supported EVM operations
3. Zero-knowledge proof systems must be designed to handle worst-case scenarios, not just typical usage
4. If ZK solutions are deployed to mainnet prematurely, malicious actors could exploit similar or worse patterns

By conducting this research in a transparent manner, we aim to strengthen the Ethereum ecosystem before ZK-based scaling solutions reach widespread adoption. It serves as a reminder that protocol designers must account for all valid operations, not just common ones.

## License

This project is licensed under MIT.

## Citation

If you use this work in your research, please cite it as:

```bibtex
@software{zkarnage2024,
  author = {Swann, Conner},
  title = {ZKarnage: Stress Testing ZK Systems Through Maximum Pain},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/yourbuddyconner/zkarnage}
}
```
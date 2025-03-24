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

Here's a ranking of potential attack vectors based on their projected cost efficiency (gas cost vs. ZK prover overhead):

### 1. Precompile Exploitation Attack
- **Why Efficient**: Precompiled contracts like MODEXP, ECRECOVER, and BLAKE2F are extremely expensive for ZK provers, often 100-1000x more costly to prove than their gas cost suggests
- **Gas Cost**: Very low (fixed gas costs for precompiles)
- **ZK Overhead**: Extremely high (requires custom circuit implementations)
- **Implementation**: Craft transactions that call the MODEXP precompiled with carefully selected large exponents and moduli
- **Example**: 3,000 gas could generate millions of constraints in a ZK circuit

### 2. Keccak Collision Search (Original Attack)
- **Why Efficient**: Keccak is notoriously inefficient in ZK circuits (~20,000 constraints per hash)
- **Gas Cost**: Moderate (6M gas in your example)
- **ZK Overhead**: Very high (forces ~45MiB of data through keccak)
- **Implementation**: EXTCODESIZE across many large contracts
- **Optimization**: Target contracts that are known to have very large bytecode

### 3. Witness Size Maximization
- **Why Efficient**: Some operations produce disproportionately large witnesses
- **Gas Cost**: Low to moderate
- **ZK Overhead**: High (forces prover to handle large non-compressible data)
- **Implementation**: Generate calldata with high entropy that's difficult to compress
- **Example**: 1MB of carefully crafted calldata might cost under 1M gas but produce 10+MB of proof witness

### 4. Storage Trie Path Divergence
- **Why Efficient**: Forces many distinct MPT proofs while updating minimal state
- **Gas Cost**: Moderate (each SLOAD/SSTORE has a base cost)
- **ZK Overhead**: High (forces proof system to generate many unique Merkle paths)
- **Implementation**: Make storage operations to keys that maximize Merkle path differences
- **Example**: Target accounts with 100+ storage slots at carefully selected keys

### 5. Cross-Contract Call Depth Attack
- **Why Efficient**: Creates complex execution traces with many context switches
- **Gas Cost**: Moderate (each CALL has overhead)
- **ZK Overhead**: High (requires proving many contract context changes)
- **Implementation**: Create a chain of contract calls where each contract makes minimal state changes
- **Example**: A→B→C→D→E→...→Z where each makes one tiny storage change

### 6. EVM Memory Expansion
- **Why Efficient**: Memory expansion is cheap in gas but expensive to prove
- **Gas Cost**: Low (3 gas per word, plus quadratic after certain thresholds)
- **ZK Overhead**: Moderate to high
- **Implementation**: Operations that create large memory allocations without much computation
- **Example**: Create large arrays in memory without extensive processing of their contents

### 7. Log Generation Overload
- **Why Efficient**: Events create receipt trie entries that must be proven
- **Gas Cost**: Moderate to high (LOG operations are not cheap)
- **ZK Overhead**: Moderate
- **Implementation**: Contract that emits many events with large data payloads
- **Optimization**: Use multiple topics to maximize Bloom filter impact

### Cost Efficiency Analysis

To maximize the "proof stress to gas cost" ratio, focus should be on:

1. **Precompile attacks** - By far the most efficient due to fixed gas costs but extremely complex ZK circuits. MODEXP with large inputs is particularly effective.
2. **Keccak-heavy operations** - The ratio of keccak proof cost to gas cost makes this highly effective, especially when targeting existing large contracts.
3. **Proof witness expansion** - Operations that produce large witnesses relative to their gas costs.

The most devastating attack would likely combine several of these vectors - for example, using EXTCODESIZE on large contracts while also calling MODEXP precompiles and structuring the attack to maximize memory expansion through carefully crafted array operations.

## Finding Large Contracts

To identify the largest contracts on Ethereum for maximum impact, we used the following BigQuery query against the public Ethereum dataset:

```sql
SELECT
  contracts.address,
  SAFE_DIVIDE(SAFE_SUBTRACT(LENGTH(contracts.bytecode), 2), 2) AS bytecode_length
FROM
  `bigquery-public-data.crypto_ethereum.contracts` as contracts
ORDER BY
  bytecode_length
  DESC
```

This query:
1. Accesses all deployed contracts on Ethereum
2. Calculates their bytecode length (removing the '0x' prefix and accounting for hex encoding)
3. Orders them by size in descending order

## Project Structure

```
zkarnage/
├── src/
│   ├── WorstCaseAttack.sol    # The main attack contract
│   └── AddressList.sol        # Library containing target addresses
├── script/
│   ├── DeployAttack.s.sol     # Script to deploy the attack contract
│   ├── ExecuteAttack.s.sol    # Script to execute the attack
│   ├── CheckSizes.s.sol       # Script to verify bytecode sizes
│   ├── DeployAndAttack.s.sol  # Combined deploy & attack script
│   ├── FindLargeContracts.s.sol  # Script to find large contracts on mainnet
│   └── TargetSpecificBlock.s.sol # Script to target blocks divisible by 100
├── test/
│   └── WorstCaseAttack.t.sol  # Tests for the attack contract
└── README.md                  # This file
```

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
   ```

## Usage

### Find Large Contracts

Before running the attack, you may want to identify large contracts on mainnet:

```bash
# Set your Ethereum RPC URL
export ETH_RPC_URL="https://eth-mainnet.alchemyapi.io/v2/YOUR_API_KEY"

# Run the script to find large contracts
forge script script/FindLargeContracts.s.sol --rpc-url $ETH_RPC_URL
```

This will generate a file called `large_contracts.txt` with addresses of large contracts sorted by size.

### Check Contract Sizes

To verify the size of the target contracts:

```bash
forge script script/CheckSizes.s.sol --rpc-url $ETH_RPC_URL
```

### Deploy the Attack Contract

To deploy the attack contract:

```bash
# Set your private key (use a burner wallet!)
export PRIVATE_KEY=0x...

# Deploy the contract
forge script script/DeployAttack.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

Take note of the deployed contract address for future steps.

### Execute the Attack

To execute the attack with a previously deployed contract:

```bash
# Set the deployed contract address
export ATTACK_CONTRACT=0x...

# Execute the attack
forge script script/ExecuteAttack.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

### Deploy and Execute in One Step

For convenience, you can deploy and execute the attack in one step:

```bash
forge script script/DeployAndAttack.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

### Target Specific Blocks

To target blocks where the block number is divisible by 100:

```bash
# Set the deployed contract address
export ATTACK_CONTRACT=0x...

# Run the targeting script
forge script script/TargetSpecificBlock.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

This script will calculate the next block divisible by 100 and wait for it to be close before executing the attack.

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

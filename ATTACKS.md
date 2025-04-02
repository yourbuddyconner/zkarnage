# ZKarnage Attack Vectors

This document details the specific attack vectors implemented in ZKarnage for stress testing ZK systems.

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
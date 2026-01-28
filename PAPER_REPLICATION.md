# Reproducing Paper Results

This document provides instructions for reproducing the results from **"Unaligned Incentives: Pricing Attacks Against Blockchain Rollups"** (Section 5: Prover Killer Attack on ZK-Rollups).

**Paper**: [https://arxiv.org/abs/2509.17126](https://arxiv.org/abs/2509.17126)

## Prerequisites

### Software Requirements

1. **Foundry** - Ethereum development toolkit
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. **Python 3.10+** with dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. **RSP (Reth State Provider)** from Succinct
   - Follow installation instructions at [https://github.com/succinctlabs/rsp](https://github.com/succinctlabs/rsp)
   - Ensure `rsp` is available in your PATH

4. **Ethereum RPC endpoint** (e.g., Alchemy, Infura, or local node)
   ```bash
   export ETH_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
   ```

## Reproducing Figure 6: Cycles-per-Gas Benchmarks (Section 5.3)

Figure 6 shows the cycles-per-gas ratios for EVM opcodes and precompiles, measured using RSP.

### Step 1: Run RSP Benchmarks

Benchmark opcodes over 100 consecutive mainnet blocks:

```bash
python script/rsp-bench.py \
  --rpc-url $ETH_RPC_URL \
  --start-block 22580901 \
  --num-blocks 100 \
  --report-path rsp_benchmark_report_opcode.csv \
  --extra-rsp-args "--opcode-tracking"
```

Benchmark precompiles:

```bash
python script/rsp-bench.py \
  --rpc-url $ETH_RPC_URL \
  --start-block 22580901 \
  --num-blocks 100 \
  --report-path rsp_benchmark_report_precompile.csv \
  --extra-rsp-args "--precompile-tracking"
```

### Step 2: Analyze Results

Generate cycles-per-gas analysis:

```bash
python script/analyze_cycles_per_gas.py \
  --input rsp_benchmark_report_precompile.csv \
  --output cycles_per_gas_analysis.json
```

Generate markdown tables:

```bash
python script/generate_opcode_table.py \
  --opcode-csv rsp_benchmark_report_opcode.csv \
  --precompile-csv rsp_benchmark_report_precompile.csv \
  --output benchmark_tables.md
```

### Expected Results (Figure 6)

| Opcode | Gas | Cycles | C/G |
|--------|-----|--------|-----|
| JUMPDEST | 1 | ~1039.8 | ~1039.79 |
| MULMOD | 8 | ~4640.8 | ~580.10 |
| CALLDATACOPY | 3 | ~1733.8 | ~577.93 |

| Precompile | Gas | Cycles | C/G |
|------------|-----|--------|-----|
| MODEXP | 200 | ~592,344 | ~2961.72 |
| BN_PAIRING | 45,000 | ~73,896,701 | ~1642.15 |
| BN_ADD | 150 | ~123,223 | ~821.49 |

## Reproducing Figure 8: Prover-Killer Attack Metrics (Section 5.5)

Figure 8 shows the impact of crafted prover-killer blocks on proving time and cost.

### Step 1: Generate Attack Blocks

Each attack type corresponds to a row in Figure 8:

```bash
# MODEXP attack (highest impact)
python script/generate_block.py \
  --attack-type modexp \
  --gas-limit 35000000 \
  --rpc-url $ETH_RPC_URL \
  --output-file out/blocks/block_modexp.json

# SHA256 attack
python script/generate_block.py \
  --attack-type sha256 \
  --gas-limit 35000000 \
  --rpc-url $ETH_RPC_URL \
  --output-file out/blocks/block_sha256.json

# BN_PAIRING attack
python script/generate_block.py \
  --attack-type pairings \
  --gas-limit 35000000 \
  --rpc-url $ETH_RPC_URL \
  --output-file out/blocks/block_pairings.json

# KECCAK attack
python script/generate_block.py \
  --attack-type keccak \
  --gas-limit 35000000 \
  --rpc-url $ETH_RPC_URL \
  --output-file out/blocks/block_keccak.json

# ECRECOVER attack
python script/generate_block.py \
  --attack-type ecrecover \
  --gas-limit 33000000 \
  --rpc-url $ETH_RPC_URL \
  --output-file out/blocks/block_ecrecover.json
```

### Step 2: Measure Proving Costs

Use RSP to prove each generated block and measure cycle counts:

```bash
rsp --block-json out/blocks/block_modexp.json --opcode-tracking
```

### Expected Results (Figure 8)

| Attack | Total Gas (M) | Total Cycles (M) | Proving Time (s) | Latency Delay |
|--------|---------------|------------------|------------------|---------------|
| MODEXP | 35.49 | 26,640.26 | ~30,575* | +9459.0%* |
| SHA256 | 35.49 | 2,110.15 | ~1,501 | +369.2% |
| BN_PAIRING | 35.51 | 1,904.79 | ~3,966 | +1139.8% |
| KECCAK | 35.49 | 988.12 | ~873 | +172.9% |
| ECRECOVER | 33.52 | 654.72 | ~1,729 | +440.5% |

*MODEXP values are approximate; RSP may crash due to extreme resource usage.

## Hardware Requirements

The paper's benchmarks were run on:
- **GPU**: NVIDIA A100 80GB
- **CPU**: 16 vCPUs (6 physical cores)
- **RAM**: 170GB
- **Disk**: 1TB

Results may vary on different hardware configurations.

## Troubleshooting

### RSP crashes on MODEXP blocks

The MODEXP attack generates extreme proving loads. Try:
- Increasing available memory
- Using a smaller `--gas-limit` (e.g., 10M instead of 35M)
- Running with `--timeout` flags if available

### Slow block generation

Block generation requires forking mainnet state. Ensure:
- Your RPC endpoint has sufficient rate limits
- Consider using a local archive node for faster access

## Citation

If you use this code in your research, please cite:

```bibtex
@article{chaliasos2025unaligned,
  title={Unaligned Incentives: Pricing Attacks Against Blockchain Rollups},
  author={Chaliasos, Stefanos and Swann, Conner and Pilehchiha, Sina and 
          Mohnblatt, Nicolas and Livshits, Benjamin and Kattis, Assimakis},
  journal={arXiv preprint arXiv:2509.17126},
  year={2025}
}
```

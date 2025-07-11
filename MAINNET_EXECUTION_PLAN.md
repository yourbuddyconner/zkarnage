# ZKarnage Mainnet Execution Plan

## Executive Summary

This document outlines the execution plan for deploying ZKarnage attacks on Ethereum mainnet to stress test zero-knowledge proof systems. With a generous grant from the Ethereum Foundation, we will execute prover killer transactions every 1,000 blocks, targeting at least 100 submissions while documenting impacts on ZK provers.

## Project Overview

### Objectives
- Execute ZKarnage attacks on mainnet to stress test ZK proving systems
- Document real-world impacts on prover performance and costs
- Provide valuable data to the ZK ecosystem for optimization
- Create public record of attack effectiveness and prover resilience

### Key Metrics
- **Budget**: Generous grant from the Ethereum Foundation
- **Frequency**: Every 1,000 blocks (~3.5 hours)
- **Target**: 100+ successful submissions
- **Duration**: ~17.5 days of continuous execution

## Execution Strategy

### Attack Timing
- **Block Selection**: Every block where `block.number % 1000 == 0`
- **Rationale**: Provides consistent, predictable attack windows while conserving budget
- **Coverage**: ~6-7 attacks per day

### Gas Management
- **Estimated gas per attack**: 8-10M gas
- **Gas price strategy**: Base fee + 10% priority fee

### Attack Rotation
To maximize impact and gather diverse data, we'll rotate through attack vectors:

1. **Week 1**: Focus on high-multiplier attacks (JUMPDEST, MODEXP)
2. **Week 2**: Precompile-heavy attacks (BN_PAIRING, BN_MUL)
3. **Week 3**: Memory-intensive attacks (MCOPY, CALLDATACOPY)

### Script Modifications
Minimal changes to existing scripts:
```python
# Modify run_attack.py
TARGET_BLOCK_INTERVAL = 1000  # Changed from 100
MAX_RETRIES = 3  # Add retry logic for failed submissions
GAS_BUFFER = 1.1  # 10% gas buffer
```

## Data Collection and Analysis Strategy

To maintain focus and simplicity, we will adopt a streamlined data collection and analysis workflow. 
### Data Flow

Our process will consist of three main steps:

1.  **Log On-Chain Data**: The `run_attack.py` script executes an attack and, upon confirmation, appends a JSON record of the transaction's details (hash, gas, cost, etc.) to a local `attack_log.json` file.
2.  **Combine with Prover Data**: Periodically, we will manually or semi-automatically download prover performance data from the EthProofs platform for the blocks we've targeted. A simple utility script will then merge our `attack_log.json` with the EthProofs data to create a final `public_data.json`.
3.  **Client-Side Analysis**: The `public_data.json` file will be the sole data source for our public-facing dashboard. All visualizations, calculations (like ROI, prover impact), and filtering will be handled directly in the browser using JavaScript.

### Data Schemas

#### 1. `attack_log.json` (from `run_attack.py`)
This file will be an array of JSON objects with the following structure:
```json
{
  "tx_hash": "0x...",
  "block_number": 19000000,
  "timestamp": 1234567890,
  "attack_config": {
    "type": "JUMPDEST",
    "iterations": 10000
  },
  "gas_metrics": {
    "gas_used": 28500000,
    "gas_price_gwei": 25.5
  }
}
```

#### 2. `public_data.json` (Combined Data)
This is the final file that will be committed to the repository and consumed by the frontend.
```json
{
  "tx_hash": "0x...",
  "block_number": 19000000,
  // ... other fields from attack_log.json ...
  "prover_performance": {
    "baseline": {
        "avg_proof_time_s": 220,
        "avg_cost_usd": 0.89
    },
    "results": {
      "succinct_sp1": {
        "proof_time_s": 1205,
        "cost_usd": 5.87,
        "cycles": 45622000, // zkVM-specific
        "status": "completed"
      },
      "risc0_zkvm": {
        "proof_time_s": 847,
        "cost_usd": 3.42,
        "cycles": 38455000, // zkVM-specific
        "status": "completed"
      }
    }
  }
}
```

This simplified approach ensures that our efforts are focused on executing attacks and presenting the findings, rather than on building and maintaining a complex data infrastructure.

## Reporting Framework

### Deliverables Structure

#### 1. Live Dashboard (GitHub Pages)
```
prooflab.dev/
├── index.html
├── data/
│   └── public_data.json
└── js/
    ├── main.js
    └── charts.js
```

#### 2. Weekly Reports

**Format**: Markdown, published as blog posts on the project website.

**Structure**:

```markdown
# ZKarnage Weekly Report - Week X

## Executive Summary
- Attacks executed: X
- Total ETH spent: X
- Average prover impact: X%
- Most effective attack: TYPE

## Key Metrics
[Interactive charts embedded from the live dashboard]

## Notable Findings
1. Finding with data
2. Finding with data
3. Finding with data

## Prover Performance Analysis
### Succinct SP1 (zkVM)
- Average proof time increase: X%
- Cycle count: X (zkVM-specific metric)
- Cost impact: $X
- Adaptation observed: Yes/No

### RISC Zero (zkVM)
- Average proof time increase: X%
- Cycle count: X (zkVM-specific metric)
- Cost impact: $X
- Adaptation observed: Yes/No

### Other Provers
[Similar structure for each]

## Next Week Preview
- Planned attack types
- Expected outcomes
- Budget remaining
```

#### 3. Final Comprehensive Report

**Format**: PDF

**Structure**:

```
1. Executive Summary (1 page)
   - Key findings & impact summary
   - Main recommendations

2. Methodology (2 pages)
   - Attack implementation details
   - Simplified data collection process
   - Analysis framework (client-side)
   - Limitations and assumptions

3. Results Analysis (8 pages)
   - Per-Attack Analysis (JUMPDEST, MODEXP, etc.)
   - Comparative effectiveness
   - Prover Impact Study
   - Resilience rankings

4. Economic Analysis (5 pages)
   - Total costs vs. impacts
   - ROI calculations
   - Gas market effects

5. Recommendations & Future Work (3 pages)
   - For prover developers
   - For protocol designers
   - For researchers

6. Appendices (1 page)
   - Link to raw data
   - Reproduction instructions
```

## Data Collection Implementation

### Required APIs and Data Sources

#### 1. Blockchain Data
- **Ethereum RPC**: Transaction receipts, block data, gas prices

#### 2. Prover Performance Data
- **EthProofs Platform**: Aggregated proof data from all prover implementations
- **Succinct SP1 (zkVM)**: Proof times and cycle counts via EthProofs
- **RISC Zero (zkVM)**: Proof times and cycle counts via EthProofs
- **Other provers**: Any additional implementations submitting to EthProofs

#### 3. Market Data
- **CoinGecko API**: Real-time ETH price
- **DeFiLlama**: L2 activity metrics
- **Dune Analytics**: Custom queries for analysis

### Data Collection Workflow

Our data collection process is a straightforward, three-step workflow designed for simplicity and efficiency:

1.  **Execute and Log Attack**:
    - The `run_attack.py` script initiates the on-chain attack.
    - Upon confirmation, it records the transaction details (hash, gas, cost) into a local `attack_log.json` file.

2.  **Enrich with Prover Data**:
    - At a later time, we will fetch performance data from EthProofs for the corresponding blocks.
    - This data, including proof times, costs, and zkVM cycle counts, is merged with our `attack_log.json` to create the final `public_data.json`.

3.  **Analyze and Visualize**:
    - The `public_data.json` serves as the single source of truth for all analysis.
    - The public dashboard will consume this file, performing all calculations and visualizations on the client-side.

## Final Deliverables

### 1. Raw Data Archive
- **Format**: JSON files organized by date
- **Storage**: GitHub repository
- **Access**: Public, MIT licensed
- **Size**: ~100MB estimated

### 2. Interactive Dashboard
- **URL**: prooflab.dev
- **Updates**: Real-time during execution
- **Features**:
  - Live attack feed
  - Cumulative statistics
  - Prover leaderboard
  - Cost tracker

### 3. Technical Report (~20 pages)

### 4. Public Presentations
- Twitter thread with key findings
- Blog post on Mirror/Medium
- Presentation at ETHDenver (if applicable)
- Research paper submission

### 5. Open Source Contributions
- Data collection scripts
- Analysis notebooks
- Visualization tools
- Attack monitoring dashboard

## Success Metrics

### Quantitative Goals
- ✓ 100+ successful attack executions
- ✓ 5+ prover systems analyzed via EthProofs

### Qualitative Goals
- ✓ Actionable insights for ZK optimization
- ✓ Positive engagement from prover teams
- ✓ Data contributed to EthProofs platform
- ✓ Reproducible research methodology
- ✓ Long-term monitoring framework established

## Project Timeline Summary

**Week -1**: Preparation and Testing
**Week 0**: Deploy and Initial Tests
**Week 1-2**: Main Execution Phase
**Week 3**: Final Attacks and Analysis
**Week 4-8**: Report Writing and Publication

Total Duration: 8 weeks from start to final deliverable

## Timeline & Milestones

### Week -1 (Preparation)
- [ ] Deploy ZKarnage contract to mainnet
- [ ] Test attack execution with small gas amounts
- [ ] Set up GitHub Pages infrastructure
- [ ] Prepare data collection scripts
- [ ] Establish prover API access

### Week 0 (Launch Week)
- [ ] Execute first test attack
- [ ] Verify data collection pipeline
- [ ] Announce project publicly
- [ ] Begin baseline data collection

### Week 1-2 (Main Execution)
- [ ] Execute 70+ attacks
- [ ] Daily data updates
- [ ] Weekly progress report
- [ ] Community engagement

### Week 3 (Final Push)
- [ ] Complete remaining attacks
- [ ] Begin data analysis
- [ ] Prepare visualizations
- [ ] Draft report sections

### Week 4-8 (Analysis & Reporting)
- [ ] Complete final report
- [ ] Publish all data
- [ ] Present findings
- [ ] Archive project

## Next Steps

1. **Immediate Actions** (This Week):
   - [ ] Finalize and review this plan
   - [ ] Set up GitHub Pages repository
   - [ ] Deploy ZKarnage contract
   - [ ] Test data collection pipeline

2. **Pre-Launch** (Next Week):
   - [ ] Notify prover teams (Succinct, RISC Zero, etc.)
   - [ ] Coordinate with EthProofs platform
   - [ ] Announce project timeline
   - [ ] Complete testing
   - [ ] Prepare first week's attacks

3. **Launch Criteria**:
   - [ ] Contract deployed and verified
   - [ ] Data pipeline tested
   - [ ] Communication plan ready
   - [ ] Team availability confirmed

---

**Project Lead**: Conner Swann
**Repository**: github.com/yourbuddyconner/zkarnage
**Live Dashboard**: prooflab.dev
**Contact**: @yourbuddyconner @TheProofLab

*This plan is a living document and will be updated as the project progresses.*
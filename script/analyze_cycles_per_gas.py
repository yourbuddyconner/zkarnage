#!/usr/bin/env python3
"""
Script to calculate average cycle count per gas for precompile benchmark blocks.

Analyzes the rsp_benchmark_report_precompile.csv file which contains cycle counts
for precompile operations (ecrecover, sha256, modexp, bn operations, etc.).

Usage:
    python analyze_cycles_per_gas.py [--verbose] [--output OUTPUT_FILE]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List


def analyze_csv(csv_path: Path) -> Dict:
    """Analyze a benchmark CSV file and calculate cycle count per gas statistics."""
    
    if not csv_path.exists():
        print(f"Error: File {csv_path} not found")
        return None
    
    cycle_per_gas_values = []
    total_gas = 0
    total_cycles = 0
    block_count = 0
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                gas_used = int(row['gas_used'])
                cycles = int(row['total_cycles_count'])
                
                if gas_used > 0 and cycles > 0:
                    cycles_per_gas = cycles / gas_used
                    cycle_per_gas_values.append(cycles_per_gas)
                    total_gas += gas_used
                    total_cycles += cycles
                    block_count += 1
                    
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping row due to error: {e}")
                continue
    
    if not cycle_per_gas_values:
        return None
    
    # Calculate statistics
    avg_cycles_per_gas = sum(cycle_per_gas_values) / len(cycle_per_gas_values)
    min_cycles_per_gas = min(cycle_per_gas_values)
    max_cycles_per_gas = max(cycle_per_gas_values)
    
    # Also calculate weighted average (total cycles / total gas)
    weighted_avg = total_cycles / total_gas if total_gas > 0 else 0
    
    return {
        'file': csv_path.name,
        'block_count': block_count,
        'total_gas': total_gas,
        'total_cycles': total_cycles,
        'avg_cycles_per_gas': avg_cycles_per_gas,
        'weighted_avg_cycles_per_gas': weighted_avg,
        'min_cycles_per_gas': min_cycles_per_gas,
        'max_cycles_per_gas': max_cycles_per_gas,
        'per_block_values': cycle_per_gas_values
    }


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate a specific percentile from a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100.0)
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def print_statistics(stats: Dict, verbose: bool = False):
    """Print formatted statistics."""
    if not stats:
        return
    
    print(f"\n{'='*80}")
    print(f"Analysis for: {stats['file']}")
    print(f"{'='*80}")
    print(f"Blocks analyzed:           {stats['block_count']:,}")
    print(f"Total gas used:            {stats['total_gas']:,}")
    print(f"Total cycles:              {stats['total_cycles']:,}")
    print(f"\n{'Cycles per Gas Statistics':^80}")
    print(f"{'-'*80}")
    print(f"Average (per block):       {stats['avg_cycles_per_gas']:.4f}")
    print(f"Weighted average:          {stats['weighted_avg_cycles_per_gas']:.4f}")
    print(f"Minimum:                   {stats['min_cycles_per_gas']:.4f}")
    print(f"Maximum:                   {stats['max_cycles_per_gas']:.4f}")
    
    # Add percentiles
    p25 = calculate_percentile(stats['per_block_values'], 25)
    p50 = calculate_percentile(stats['per_block_values'], 50)
    p75 = calculate_percentile(stats['per_block_values'], 75)
    p95 = calculate_percentile(stats['per_block_values'], 95)
    
    print(f"25th percentile:           {p25:.4f}")
    print(f"50th percentile (median):  {p50:.4f}")
    print(f"75th percentile:           {p75:.4f}")
    print(f"95th percentile:           {p95:.4f}")
    
    # Calculate standard deviation
    mean = stats['avg_cycles_per_gas']
    variance = sum((x - mean) ** 2 for x in stats['per_block_values']) / len(stats['per_block_values'])
    std_dev = variance ** 0.5
    print(f"Standard deviation:        {std_dev:.4f}")
    
    print(f"{'='*80}")
    
    if verbose:
        print(f"\nPer-block breakdown:")
        print(f"{'-'*80}")
        for i, value in enumerate(stats['per_block_values'], 1):
            print(f"Block {i:3d}: {value:8.4f} cycles/gas")
        print(f"{'='*80}")


def save_results(all_stats: List[Dict], output_file: Path):
    """Save results to a JSON file."""
    output_data = {
        'summary': {
            'total_blocks_analyzed': sum(s['block_count'] for s in all_stats),
            'total_gas_used': sum(s['total_gas'] for s in all_stats),
            'total_cycles': sum(s['total_cycles'] for s in all_stats),
        },
        'files': []
    }
    
    for stats in all_stats:
        file_data = {
            'filename': stats['file'],
            'block_count': stats['block_count'],
            'total_gas': stats['total_gas'],
            'total_cycles': stats['total_cycles'],
            'statistics': {
                'avg_cycles_per_gas': stats['avg_cycles_per_gas'],
                'weighted_avg_cycles_per_gas': stats['weighted_avg_cycles_per_gas'],
                'min_cycles_per_gas': stats['min_cycles_per_gas'],
                'max_cycles_per_gas': stats['max_cycles_per_gas'],
                'percentile_25': calculate_percentile(stats['per_block_values'], 25),
                'percentile_50': calculate_percentile(stats['per_block_values'], 50),
                'percentile_75': calculate_percentile(stats['per_block_values'], 75),
                'percentile_95': calculate_percentile(stats['per_block_values'], 95),
            },
            'per_block_values': stats['per_block_values']
        }
        output_data['files'].append(file_data)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate average cycle count per gas for benchmark blocks'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show per-block breakdown'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Get the script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Only analyze the precompile CSV file
    csv_files = [
        project_root / 'rsp_benchmark_report_precompile.csv',
    ]
    
    all_stats = []
    
    for csv_file in csv_files:
        print(f"\nProcessing {csv_file.name}...")
        stats = analyze_csv(csv_file)
        
        if stats:
            all_stats.append(stats)
            print_statistics(stats, verbose=args.verbose)
        else:
            print(f"No valid data found in {csv_file.name}")
    
    # Print summary
    if all_stats:
        stats = all_stats[0]  # Only one file now
        print(f"\n\n{'FINAL SUMMARY':^80}")
        print(f"{'='*80}")
        print(f"Blocks analyzed:           {stats['block_count']:,}")
        print(f"Total gas used:            {stats['total_gas']:,}")
        print(f"Total cycles:              {stats['total_cycles']:,}")
        print(f"Average cycles/gas:        {stats['avg_cycles_per_gas']:.4f}")
        print(f"Weighted average:          {stats['weighted_avg_cycles_per_gas']:.4f}")
        print(f"{'='*80}")
    
    # Save results if requested
    if args.output and all_stats:
        output_path = Path(args.output)
        save_results(all_stats, output_path)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())


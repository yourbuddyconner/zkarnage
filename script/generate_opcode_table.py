#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
from collections import defaultdict
import math

# Approximate base static gas costs (pre-Cancun). Ignores dynamic costs.
# Source: Ethereum Yellow Paper, EVM Opcodes website, etc.
# This is a simplification! Actual costs can be dynamic.
OPCODE_BASE_GAS = {
    # 0s: Stop and Arithmetic Operations
    "stop": 0, "add": 3, "mul": 5, "sub": 3, "div": 5, "sdiv": 5, "mod": 5, "smod": 5, "addmod": 8, "mulmod": 8, "exp": 10, # EXP base cost is 10, byte cost is 50
    "signextend": 5,
    # 10s: Comparison & Bitwise Logic Operations
    "lt": 3, "gt": 3, "slt": 3, "sgt": 3, "eq": 3, "iszero": 3, "and": 3, "or": 3, "xor": 3, "not": 3, "byte": 3,
    "shl": 3, "shr": 3, "sar": 3,
    # 20s: Keccak256
    "keccak256": 30, # Plus dynamic cost based on size
    # 30s: Environmental Information
    "address": 2, "balance": 100, "origin": 2, "caller": 2, "callvalue": 2, "calldataload": 3, "calldatasize": 2, "calldatacopy": 3, # Plus dynamic
    "codesize": 2, "codecopy": 3, # Plus dynamic
    "gasprice": 2, "extcodesize": 100, "extcodecopy": 100, # Plus dynamic
    "returndatasize": 2, "returndatacopy": 3, # Plus dynamic
    "extcodehash": 100,
    # 40s: Block Information
    "blockhash": 20, "coinbase": 2, "timestamp": 2, "number": 2, "difficulty": 2, "gaslimit": 2, "chainid": 2, "selfbalance": 5, "basefee": 2,
    # 50s: Stack, Memory, Storage and Flow Operations
    "pop": 2, "mload": 3, "mstore": 3, "mstore8": 3, "sload": 100, "sstore": 21000, # Highly variable! Using high base for simplicity
    "jump": 8, "jumpi": 10, "pc": 2, "msize": 2, "gas": 2, "jumpdest": 1,
    # 60s & 70s: Push Operations
    **{f"push{i}": 3 for i in range(1, 33)}, "push0": 2, # Push0 added in Shanghai
    # 80s: Duplication Operations
    **{f"dup{i}": 3 for i in range(1, 17)},
    # 90s: Exchange Operations
    **{f"swap{i}": 3 for i in range(1, 17)},
    # a0s: Logging Operations
    "log0": 375, "log1": 375 * 2, "log2": 375 * 3, "log3": 375 * 4, "log4": 375 * 5, # Plus dynamic
    # b0s: System operations (Introduced in Shanghai/Cancun)
    "tload": 100, "tstore": 100, "mcopy": 3, # Plus dynamic (Base cost from EIP-5656)
    # e0s: EOF Opcodes (Placeholders, likely 0 gas until specified)
    "rjump": 0, "rjumpi": 0, "rjumpv": 0, "callf": 0, "retf": 0, "jumpf": 0,
    "dupn": 0, "swapn": 0, "exchange": 0, "eofcreate": 0, "returncontract": 0,
    "dataload": 0, "dataloadn": 0, "datasize": 0, "datacopy": 0,
    "returndataload": 0, "extcall": 0, "extdelegatecall": 0, "extstaticcall": 0,
    # f0s: System Operations
    "create": 32000, "call": 100, "callcode": 100, "return": 0, "delegatecall": 100, "create2": 32000,
    "staticcall": 100, "revert": 0, "invalid": 0, "selfdestruct": 5000,
    # Additional possible report entries (set to 0 if no standard gas cost)
    "blobhash": 0, # EIP-4844 - Gas cost handled differently
    "blobbasefee": 0, # EIP-4844
}

# Approximate base gas costs for precompiles. Many are dynamic.
# Keys should match the expected names in the CSV header (e.g., "ecrecover")
PRECOMPILE_BASE_GAS = {
    "ecrecover": 3000,
    "sha256": 60,      # + 12 per word
    "ripemd160": 600, # + 120 per word
    "identity": 15,    # + 3 per word
    "modexp": 200,     # Highly dynamic base
    "bn-add": 150,      # (BN254) Was 500 pre-Istanbul (Mapped from precompile_ecadd)
    "bn-mul": 6000,     # (BN254) Was 40000 pre-Istanbul (Mapped from precompile_ecmul)
    "bn-pair": 45000, # (BN254) + 34000 per pair, was 100k+80k (Mapped from precompile_ecpairing)
    "blake2f": 0,     # Dynamic based on rounds
    "kzg-point-evaluation": 50000, # EIP-4844 (Mapped from precompile_pointevaluation)
}

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Markdown tables of opcode and precompile cycles from RSP benchmark reports."
    )
    parser.add_argument(
        "--opcode-report-csv",
        type=str,
        default="rsp_benchmark_report_opcode.csv",
        help="Path to the input opcode benchmark report CSV file.",
    )
    parser.add_argument(
        "--precompile-report-csv",
        type=str,
        default="rsp_benchmark_report_precompile.csv",
        help="Path to the input precompile benchmark report CSV file.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="benchmark_tables.md",
        help="Path to save the output Markdown tables (default: benchmark_tables.md).",
    )
    parser.add_argument(
        "--sort-by",
        choices=['name', 'gas', 'cycles', 'ratio'],
        default='ratio',
        help="Column to sort the tables by (name, gas, cycles, ratio; default: ratio)."
    )
    return parser.parse_args()

# Helper function to calculate ratio
def calculate_ratio(avg_cycles, base_gas):
    ratio = "N/A"
    if isinstance(base_gas, int) and base_gas > 0 and not math.isnan(avg_cycles):
        ratio = round(avg_cycles / base_gas, 2)
    elif isinstance(base_gas, int) and base_gas == 0 and not math.isnan(avg_cycles) and avg_cycles > 0:
        ratio = float('inf') # Use 'inf' for division by zero gas
    # Keep "N/A" if base_gas is "N/A", avg_cycles is NaN, or avg_cycles is 0 when gas is 0
    elif isinstance(base_gas, int) and base_gas == 0 and not math.isnan(avg_cycles) and avg_cycles == 0:
        ratio = 0.0 # Convention: 0 cycles / 0 gas = 0 ratio
    return ratio

# Helper function to generate markdown table
def generate_markdown_table(title, results, sort_by):
    if not results:
        return f"""## {title}

No data found or processed.
"""

    # Sort results based on the chosen key
    if sort_by == 'name':
        results.sort(key=lambda x: x['Name'])
    elif sort_by == 'gas':
        results.sort(key=lambda x: float('inf') if x['Base Gas'] == 'N/A' else x['Base Gas'])
    elif sort_by == 'cycles':
        results.sort(key=lambda x: float('-inf') if x['Avg Cycles'] == 'N/A' else x['Avg Cycles']) # Treat N/A cycles as low
    elif sort_by == 'ratio':
        def sort_key_ratio_desc(item):
            ratio = item['Cycles/Gas']
            if ratio == 'N/A' or ratio == float('inf'):
                return -float('inf') # Place N/A and inf at the bottom when reversed
            return ratio
        results.sort(key=sort_key_ratio_desc, reverse=True)

    # Determine column name based on title
    col_name = "Opcode" if "Opcode" in title else "Precompile"

    # Generate Markdown table header dynamically
    md_parts = [
        f"## {title}\n",
        f"| {col_name:<17} | Base Gas | Avg Cycles | Cycles/Gas |",
        "|-------------------|----------|------------|------------|"
    ]

    # Populate table rows
    for res in results:
        gas_str = str(res['Base Gas'])
        cycles_str = str(res['Avg Cycles'])
        ratio_str = str(res['Cycles/Gas'])
        if ratio_str == 'inf': ratio_str = "Inf" # More readable infinity

        md_parts.append(f"| {res['Name']:<17} | {gas_str:<8} | {cycles_str:<10} | {ratio_str:<10} |")

    return "\n".join(md_parts) + "\n\n" # Join with newline and add trailing newlines

def read_benchmark_csv(report_path: Path, base_gas_map: dict, entry_type_name: str):
    """Reads a benchmark CSV, calculates weighted averages for entries, and returns data.

    Args:
        report_path: Path to the CSV file.
        base_gas_map: Dictionary mapping entry names to their base gas costs.
        entry_type_name: String name for the type of entry (e.g., 'opcode', 'precompile').

    Returns:
        A tuple containing:
        - data (defaultdict): Aggregated cycle data for each entry found.
        - entries_in_header (list): List of valid entry names found in the header.
    """
    data = defaultdict(lambda: {"total_weighted_cycles": 0, "total_count": 0})
    entries_in_header = []
    entry_indices = {} # Stores indices for count and avg for entries
    row_num = 1 # Initialize for potential error reporting before loop

    try:
        with open(report_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            header_len = len(header)
            row_num = 2 # Start data processing from row 2

            # Iterate through the header to find entry columns (name, count, avg)
            i = 0
            while i < header_len:
                col_name = header[i].lower()

                is_entry = col_name in base_gas_map
                # Removed special handling for precompile_ prefix
                # if entry_type_name == 'precompile' and not is_entry and col_name.startswith("precompile_"):
                #     print(f"Info: Found potential precompile '{col_name}' not in defined list. Assigning N/A base gas.")
                #     base_gas_map[col_name] = "N/A" # Add placeholder
                #     is_entry = True

                if is_entry:
                    entry_name = col_name
                    if i + 2 < header_len and header[i+1].lower() == 'count' and header[i+2].lower() == 'avg':
                        count_idx = i + 1
                        avg_idx = i + 2
                        entry_indices[entry_name] = {'count': count_idx, 'avg': avg_idx}
                        entries_in_header.append(entry_name)
                        # Skip the 'count' and 'avg' columns we just processed
                        i += 3
                        continue
                    else:
                        print(f"Warning: Found potential {entry_type_name} entry '{entry_name}' in {report_path.name} at index {i}, "
                              f"but subsequent columns are not 'count' and 'avg'. Header part: "
                              f"[...{header[i:min(i+3, header_len)]}...]. Skipping this entry.")
                        i += 1
                else:
                    i += 1

            if not entry_indices:
                print(f"Warning: No known {entry_type_name}s with corresponding 'count' and 'avg' columns found in the CSV header of {report_path.name}.")

            # Process data rows
            for row in reader:
                if len(row) < header_len:
                    print(f"Warning: Skipping short row {row_num} in {report_path.name}: {row}")
                    row_num += 1
                    continue

                for entry_name, indices in entry_indices.items():
                    try:
                        count_str = row[indices['count']]
                        avg_str = row[indices['avg']]

                        if not count_str or not avg_str:
                            continue # Skip if count or avg is empty

                        count = int(float(count_str))
                        avg_cycles = float(avg_str)

                        if count > 0 and not math.isnan(avg_cycles):
                            data[entry_name]["total_weighted_cycles"] += count * avg_cycles
                            data[entry_name]["total_count"] += count
                    except ValueError:
                        # Silently skip rows with parsing errors for count/avg, as this can be common
                        # print(f"Warning: Row {row_num} in {report_path.name}: Could not parse count/avg for {entry_name}. Count='{count_str}', Avg='{avg_str}'. Skipping.")
                        pass
                    except IndexError:
                        print(f"Warning: Row {row_num} in {report_path.name}: IndexError processing {entry_name}. Indices: {indices}. Row length: {len(row)}. Skipping.")
                        # No need to continue inner loop if row is too short
                        break
                row_num += 1

    except FileNotFoundError:
        # Error handled in main, but good practice to catch here too
        print(f"Error: File not found at {report_path}")
        raise # Re-raise to be handled by main
    except StopIteration:
        print(f"Error: CSV file {report_path.name} appears to be empty or only contains a header.")
        # Return empty data, allows script to continue if other file is valid
        return data, entries_in_header
    except Exception as e:
        print(f"An unexpected error occurred reading CSV file {report_path.name} near row {row_num}: {e}")
        raise # Re-raise to be handled by main

    return data, entries_in_header

def main():
    args = parse_args()

    opcode_report_path = Path(args.opcode_report_csv)
    precompile_report_path = Path(args.precompile_report_csv)
    output_path = Path(args.output_md)

    # Check if files exist before attempting to read
    if not opcode_report_path.is_file():
        print(f"Error: Opcode report file not found at {opcode_report_path}")
        return # Or exit
    if not precompile_report_path.is_file():
        print(f"Error: Precompile report file not found at {precompile_report_path}")
        return # Or exit

    # Read data using the helper function
    opcode_data = None
    opcodes_in_header = []
    precompile_data = None
    precompiles_in_header = []

    try:
        print(f"Reading opcode data from: {opcode_report_path}")
        opcode_data, opcodes_in_header = read_benchmark_csv(opcode_report_path, OPCODE_BASE_GAS, 'opcode')

        print(f"Reading precompile data from: {precompile_report_path}")
        # Pass a copy of PRECOMPILE_BASE_GAS because the function might modify it for unknown precompiles
        precompile_gas_map_copy = PRECOMPILE_BASE_GAS.copy()
        precompile_data, precompiles_in_header = read_benchmark_csv(precompile_report_path, precompile_gas_map_copy, 'precompile')

    except (FileNotFoundError, StopIteration, Exception) as e:
        # Errors are logged within read_benchmark_csv, just exit gracefully here
        print(f"Stopping script due to error processing input files: {e}")
        return

    # --- Calculate final results for Opcodes ---
    opcode_results = []
    if opcode_data:
        for op_name in opcodes_in_header:
            if op_name in opcode_data:
                data = opcode_data[op_name]
                total_count = data["total_count"]
                if total_count > 0:
                    avg_cycles = data["total_weighted_cycles"] / total_count
                    base_gas = OPCODE_BASE_GAS.get(op_name, "N/A") # Should always be found if in header list
                    ratio = calculate_ratio(avg_cycles, base_gas)

                    opcode_results.append({
                        "Name": op_name,
                        "Base Gas": base_gas if isinstance(base_gas, int) else "N/A",
                        "Avg Cycles": round(avg_cycles, 1) if not math.isnan(avg_cycles) else "N/A",
                        "Cycles/Gas": ratio
                    })

    # --- Calculate final results for Precompiles ---
    precompile_results = []
    if precompile_data:
        # Use the potentially updated precompile_gas_map_copy for lookup
        current_precompile_gas_map = precompile_gas_map_copy
        for pre_name in precompiles_in_header:
            if pre_name in precompile_data:
                data = precompile_data[pre_name]
                total_count = data["total_count"]
                if total_count > 0:
                    avg_cycles = data["total_weighted_cycles"] / total_count
                    base_gas = current_precompile_gas_map.get(pre_name, "N/A") # Use N/A if not defined
                    ratio = calculate_ratio(avg_cycles, base_gas)

                    precompile_results.append({
                        "Name": pre_name,
                        "Base Gas": base_gas if isinstance(base_gas, int) else "N/A",
                        "Avg Cycles": round(avg_cycles, 1) if not math.isnan(avg_cycles) else "N/A",
                        "Cycles/Gas": ratio
                    })


    # --- Generate and Write Markdown ---
    opcode_table_md = generate_markdown_table("Opcode Benchmarks", opcode_results, args.sort_by)
    precompile_table_md = generate_markdown_table("Precompile Benchmarks", precompile_results, args.sort_by)

    try:
        with open(output_path, 'w') as f:
            f.write(opcode_table_md)
            f.write(precompile_table_md)
        print(f"Markdown tables generated successfully at: {output_path}")
        if not opcode_results: print("Warning: No opcode data was processed.")
        if not precompile_results: print("Warning: No precompile data was processed.")

    except Exception as e:
        print(f"Error writing Markdown file: {e}")

if __name__ == "__main__":
    main() 
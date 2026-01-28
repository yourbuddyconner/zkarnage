#!/usr/bin/env python3

# a script that wraps rsp to execute blocks and save the output
# it takes the following arguments:
# - rpc url 
# - start block
# - number of blocks to execute
# report path (default rsp_benchmark_report.csv)

import argparse
import subprocess
import sys
import os
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark RSP execution over a range of blocks."
    )
    parser.add_argument(
        "--rpc-url",
        required=True,
        type=str,
        help="JSON-RPC URL for the Ethereum node.",
    )
    parser.add_argument(
        "--start-block",
        type=int,
        default=22222222,
        help="The starting block number (inclusive).",
    )
    parser.add_argument(
        "--num-blocks",
        type=int,
        default=100,
        help="The total number of blocks to execute.",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="rsp_benchmark_report.csv",
        help="Path to save the benchmark report CSV file (default: rsp_benchmark_report.csv).",
    )
    parser.add_argument(
        "--rsp-path",
        type=str,
        default="rsp",
        help="Path to the rsp executable if not in PATH (default: rsp).",
    )

    args = parser.parse_args()

    if args.num_blocks <= 0:
        parser.error("--num-blocks must be a positive integer.")
    if args.start_block < 0:
         parser.error("--start-block cannot be negative.")

    return args

def run_rsp_for_block(rsp_path: str, block_number: int, rpc_url: str, report_path: str, tracking_flag: str):
    """Executes the rsp command for a single block with a specific tracking flag, with one retry on failure."""
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        cmd = [
            rsp_path,
            "--block-number", str(block_number),
            "--rpc-url", rpc_url,
            "--report-path", report_path,
        ]
        # Add the specific tracking flag
        if tracking_flag:
             cmd.append(tracking_flag)

        print(f"--- Running RSP for Block {block_number} with {tracking_flag} (Attempt {attempt}/{max_attempts}) ---")
        print(f"Command: {' '.join(cmd)}")

        try:
            # Use stderr=subprocess.STDOUT to capture both stdout and stderr together
            result = subprocess.run(
                cmd,
                check=True, # Raise exception on non-zero exit code
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace' # Handle potential encoding issues in output
            )
            print("--- RSP Output ---")
            print(result.stdout)
            print(f"--- Successfully processed Block {block_number} with {tracking_flag} ---")
            return True # Success, exit the function

        except subprocess.CalledProcessError as e:
            print(f"--- Error executing RSP for Block {block_number} with {tracking_flag} on Attempt {attempt}/{max_attempts} ---", file=sys.stderr)
            print(f"Return Code: {e.returncode}", file=sys.stderr)
            print("--- RSP Output (stdout) ---", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
            print("--- RSP Output (stderr) ---", file=sys.stderr)
            print(e.stderr, file=sys.stderr)

            if attempt < max_attempts:
                print(f"--- Retrying Block {block_number} with {tracking_flag} ---", file=sys.stderr)
                # Continue to the next attempt in the loop
            else:
                print(f"--- Failed to process Block {block_number} with {tracking_flag} after {max_attempts} attempts ---", file=sys.stderr)
                return False # Final failure after all attempts

        except FileNotFoundError:
            print(f"Error: '{rsp_path}' command not found.", file=sys.stderr)
            print("Please ensure rsp is installed and in your PATH, or specify its location with --rsp-path.", file=sys.stderr)
            sys.exit(1) # No point retrying if the command is not found
        except Exception as e:
            print(f"An unexpected error occurred while running RSP for Block {block_number} with {tracking_flag} on attempt {attempt}: {e}", file=sys.stderr)
            # Decide if retry makes sense for generic exceptions? Probably not.
            print(f"--- Failed to process Block {block_number} with {tracking_flag} due to unexpected error ---", file=sys.stderr)
            return False # Failed due to unexpected error

    # This part should technically not be reached if logic is correct,
    # but added for completeness. Should have returned True or False within the loop.
    print(f"--- Unexpected exit from attempt loop for Block {block_number} with {tracking_flag} ---", file=sys.stderr)
    return False


def main():
    args = parse_args()

    # Determine the base report path and directory
    base_report_path = Path(args.report_path).resolve()
    report_dir = base_report_path.parent
    report_stem = base_report_path.stem
    report_suffix = base_report_path.suffix
    report_dir.mkdir(parents=True, exist_ok=True)

    # Define the two fixed report file paths
    precompile_report_path = report_dir / f"{report_stem}_precompile{report_suffix}"
    opcode_report_path = report_dir / f"{report_stem}_opcode{report_suffix}"

    print(f"Using precompile report file: {precompile_report_path}")
    print(f"Using opcode report file: {opcode_report_path}")

    successful_blocks = 0
    failed_blocks = 0

    end_block = args.start_block + args.num_blocks
    print(f"Starting benchmark for blocks {args.start_block} to {end_block - 1}")

    for block_num in range(args.start_block, end_block):
        print(f"\n=== Processing Block {block_num} ===")

        # Run with --precompile-tracking, appending to the precompile report
        precompile_success = run_rsp_for_block(
            args.rsp_path, block_num, args.rpc_url, str(precompile_report_path), "--precompile-tracking"
        )

        # Run with --opcode-tracking, appending to the opcode report
        opcode_success = run_rsp_for_block(
            args.rsp_path, block_num, args.rpc_url, str(opcode_report_path), "--opcode-tracking"
        )

        # A block is considered successful only if BOTH runs succeeded
        if precompile_success and opcode_success:
            successful_blocks += 1
            print(f"=== Successfully processed Block {block_num} for both tracking types ===")
        else:
            failed_blocks += 1
            print(f"=== Failed to process Block {block_num} for one or both tracking types ===", file=sys.stderr)
            # Optionally, you might want to stop the script if one block fails
            # print("Stopping benchmark due to error.", file=sys.stderr)
            # break # Uncomment to stop on first block failure

    print("\n--- Benchmark Summary ---")
    print(f"Total blocks attempted: {args.num_blocks}")
    print(f"Successfully processed (both runs): {successful_blocks}")
    print(f"Failed (one or both runs): {failed_blocks}")
    # Update summary message about the two reports
    print(f"Precompile report saved to: {precompile_report_path}")
    print(f"Opcode report saved to: {opcode_report_path}")
    print("--- Benchmark Finished ---")

if __name__ == "__main__":
    main()

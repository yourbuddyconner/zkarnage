#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from web3 import Web3

# Operation code mapping
OPERATION_CODES = {
    "keccak": "0x0003",
    "sha256": "0x0023",
    "modexp": "0x0027",
    "ecrecover": "0x0021",
}

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a prover killer block using ZKarnage")
    parser.add_argument(
        "--attack-type",
        required=True,
        choices=list(OPERATION_CODES.keys()),
        help="The type of operation to test",
    )
    parser.add_argument(
        "--gas-limit",
        type=int,
        default=5000000,
        help="Gas limit for the transaction (default: 5,000,000)",
    )
    parser.add_argument(
        "--gas-threshold",
        type=int,
        default=50000,
        help="Gas threshold at which to stop looping (default: 50,000)",
    )
    parser.add_argument(
        "--fork-block",
        type=int,
        default=22222222,
        help="Block number to fork from (default: 22,222,222)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file for the block JSON (default: out/block_{attack_type}_{gas_limit}_{gas_threshold}_fork_{fork_block}.json)",
    )
    parser.add_argument(
        "--rpc-url",
        type=str,
        required=True,
        help="Mainnet RPC URL for forking",
    )
    parser.add_argument(
        "--anvil-port",
        type=int,
        default=8545,
        help="Port for the Anvil instance (default: 8545)",
    )
    parser.add_argument(
        "--private-key",
        type=str,
        default="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",  # Anvil default account
        help="Private key for sending transactions (default: Anvil's first account)",
    )
    parser.add_argument(
        "--contract-path",
        type=str,
        default="src/ZKarnage.yul",
        help="Path to the Yul contract (default: src/ZKarnage.yul)",
    )
    args = parser.parse_args()
    
    # Set default output file if not provided
    if not args.output_file:
        # Create a directory structure for outputs
        out_dir = Path("out")
        blocks_dir = out_dir / "blocks"
        
        # Create the directories if they don't exist
        blocks_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a descriptive filename
        args.output_file = f"{blocks_dir}/block_{args.attack_type}_{args.gas_limit}_{args.gas_threshold}_fork_{args.fork_block}.json"
        print(f"Output will be saved to: {args.output_file}")
    
    return args

def start_anvil(rpc_url: str, fork_block: int, port: int) -> subprocess.Popen:
    """Start anvil process forking from the specified block and forward its output"""
    cmd = [
        "anvil",
        "--fork-url", rpc_url,
        "--fork-block-number", str(fork_block),
        "--port", str(port),
        # Enable more verbose logging
        "-vvvv"
    ]
    
    print("Starting Anvil...")
    # Start Anvil without redirecting stdout/stderr so logs show in console
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Start a thread to read and print Anvil's output
    def print_output(process):
        for line in iter(process.stdout.readline, ''):
            print(f"Anvil: {line.rstrip()}")
    
    import threading
    anvil_thread = threading.Thread(target=print_output, args=(process,), daemon=True)
    anvil_thread.start()
    
    # Wait for anvil to start
    time.sleep(3)
    return process

def deploy_contract(contract_path: str, rpc_url: str, private_key: str) -> str:
    """Deploy the ZKarnage.yul contract using forge and cast send --create"""
    print(f"Deploying contract from {contract_path}...")
    
    # Compile the contract
    compile_cmd = ["forge", "build", "--root", "."]
    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error compiling contract: {result.stderr}")
        sys.exit(1)
    
    # Get the contract name from the path
    contract_name = "ZKarnage" # Hardcoded based on user edit
    # Construct the path to the build artifact
    artifact_path = Path("out") / f"{Path(contract_path).name}" / f"{contract_name}.json"

    # Read the bytecode from the artifact
    try:
        with open(artifact_path, "r") as f:
            artifact = json.load(f)
            bytecode = artifact["bytecode"]["object"]
            if not bytecode.startswith("0x"):
                bytecode = "0x" + bytecode
    except FileNotFoundError:
        print(f"Error: Build artifact not found at {artifact_path}")
        sys.exit(1)
    except KeyError:
        print(f"Error: Could not find bytecode in artifact {artifact_path}")
        sys.exit(1)

    print(f"Bytecode length: {len(bytecode)//2 -1}")
    
    # Deploy the contract using cast send --create
    deploy_cmd = [
        "cast", "send",
        "--rpc-url", rpc_url,
        "--private-key", private_key,
        "--create", bytecode,
    ]
    
    result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Check if the error is due to insufficient funds
        if "insufficient funds" in result.stderr.lower():
             print(f"Deployment failed: Insufficient funds for account associated with private key.")
        else:
            print(f"Error deploying contract with cast send --create: {result.stderr}")
        sys.exit(1)
    
    # Extract deployed address from output
    output = result.stdout
    # Look for contractAddress in the output JSON (less likely for cast send)
    try:
        receipt_json = json.loads(output)
        address = receipt_json.get("contractAddress")
        if address:
             print(f"Contract deployed at: {address}")
             return address
        else:
            print(f"Could not find 'contractAddress' in cast send output JSON: {output}")
            # Don't exit here, try text parsing next
    except json.JSONDecodeError:
        pass # Expected if output is not JSON, try text parsing

    # Fallback: Parse text output for contract address
    for line in output.split("\n"):
        line_stripped = line.strip()
        # Look for lines starting with 'contractAddress' followed by whitespace
        if line_stripped.lower().startswith("contractaddress"):
            parts = line_stripped.split()
            if len(parts) >= 2:
                potential_address = parts[-1]
                if potential_address.startswith("0x") and len(potential_address) == 42:
                    print(f"Contract deployed at: {potential_address}")
                    return potential_address
        # Check for older formats just in case
        elif "contractAddress:" in line:
             address = line.split("contractAddress:")[1].strip()
             if address.startswith("0x") and len(address) == 42:
                 print(f"Contract deployed at: {address}")
                 return address

                    
    print(f"Could not find deployed contract address in cast send --create output: {output}")
    sys.exit(1)

def execute_attack_tx(
    contract_address: str,
    attack_type: str, 
    gas_limit: int,
    gas_threshold: int,
    rpc_url: str,
    private_key: str,
) -> str:
    """Execute the attack transaction and return the transaction hash"""
    print(f"Executing {attack_type} attack...")
    
    # Get operation code from mapping
    op_code = OPERATION_CODES[attack_type]
    
    # First, calculate the function selector for f(uint256,uint256,uint256)
    print("Calculating function selector...")
    function_hash_cmd = ["cast", "sig", "f(uint256,uint256,uint256)"]
    print(f"Running: {' '.join(function_hash_cmd)}")
    result = subprocess.run(function_hash_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error calculating function selector: {result.stderr}")
        sys.exit(1)
    
    # The output of 'cast sig' is already the full selector with 0x prefix
    function_selector = result.stdout.strip()
    print(f"Function selector: {function_selector}")
    
    # Now encode the parameters using abi-encode
    print("Encoding parameters...")
    param_cmd = [
        "cast", "abi-encode", 
        "f(uint256,uint256,uint256)", 
        op_code, 
        str(gas_threshold), 
        "0x0000000000000000000000000000000000000000"
    ]
    print(f"Running: {' '.join(param_cmd)}")
    result = subprocess.run(param_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error generating transaction data: {result.stderr}")
        sys.exit(1)
    
    param_data = result.stdout.strip()
    print(f"Raw encoded parameters: {param_data}")
    
    # Extract just the parameter data (removing function selector if present)
    if param_data.startswith("0x"):
        # Check if it already includes a function selector (first 10 chars including 0x)
        if len(param_data) >= 10:
            encoded_params = param_data[10:]  # Skip "0x" + 8 chars of selector
        else:
            encoded_params = param_data[2:]   # Just skip "0x"
    else:
        encoded_params = param_data
        
    # Create transaction data by combining selector and parameters
    tx_data = function_selector + encoded_params
    print(f"Final transaction data: {tx_data}")
    
    # Try an alternative approach as well - using cast calldata
    print("Alternative approach with cast calldata...")
    calldata_cmd = [
        "cast", "calldata", 
        "f(uint256,uint256,uint256)", 
        op_code, 
        str(gas_threshold), 
        "0x0000000000000000000000000000000000000000"
    ]
    print(f"Running: {' '.join(calldata_cmd)}")
    result = subprocess.run(calldata_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error generating calldata: {result.stderr}")
    else:
        alt_tx_data = result.stdout.strip()
        print(f"Alternative transaction data: {alt_tx_data}")
        # Use this alternative data if available
        if alt_tx_data.startswith("0x") and len(alt_tx_data) >= 10:
            tx_data = alt_tx_data
            print(f"Using alternative transaction data")
    
    # Send the transaction
    send_cmd = [
        "cast", "send",
        "--rpc-url", rpc_url,
        "--private-key", private_key,
        "--gas-limit", str(gas_limit),
        contract_address,
        tx_data
    ]
    print(f"Sending transaction: cast send --rpc-url <url> --private-key <key> --gas-limit {gas_limit} {contract_address} {tx_data}")
    
    result = subprocess.run(send_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Check for common errors like nonce issues or insufficient funds
        stderr_lower = result.stderr.lower()
        if "insufficient funds" in stderr_lower:
             print(f"Transaction failed: Insufficient funds for account.")
        elif "nonce too low" in stderr_lower or "invalid nonce" in stderr_lower:
            print(f"Transaction failed: Nonce issue. Try again or reset Anvil account state.")
        else:
            print(f"Error sending transaction: {result.stderr}")
        sys.exit(1)
    
    # Extract transaction hash from output
    output = result.stdout
    # Try parsing as JSON first
    try:
        receipt_json = json.loads(output)
        tx_hash = receipt_json.get("transactionHash")
        if tx_hash and tx_hash.startswith("0x") and len(tx_hash) == 66:
             print(f"Transaction sent: {tx_hash}")
             return tx_hash
        else:
            print(f"Could not find valid 'transactionHash' in cast send output JSON: {output}")
            # Don't exit, try text parsing
    except json.JSONDecodeError:
        pass # Expected if output is not JSON, try text parsing

    # Fallback: Parse text output for transaction hash
    for line in output.split("\n"):
        line_stripped = line.strip()
        # Look for lines starting with 'transactionHash'
        if line_stripped.lower().startswith("transactionhash"):
            parts = line_stripped.split()
            if len(parts) >= 2:
                potential_hash = parts[-1]
                if potential_hash.startswith("0x") and len(potential_hash) == 66:
                    print(f"Transaction sent: {potential_hash}")
                    return potential_hash
        # Original check as a final fallback
        elif line_stripped.startswith("0x") and len(line_stripped) == 66:
            tx_hash = line_stripped
            print(f"Transaction sent: {tx_hash}")
            return tx_hash
    
    print(f"Could not find transaction hash in cast output: {output}")
    sys.exit(1)

def get_block_data(w3: Web3, tx_hash: str, fork_block: int) -> Dict:
    """Get the block data containing the transaction and all blocks since fork"""
    print("Retrieving block data...")
    
    # Wait for transaction to be mined
    receipt = None
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt and receipt.blockNumber:
                break
        except Exception:
            pass
        time.sleep(1)
    
    if not receipt or not receipt.blockNumber:
        print(f"Transaction not mined after {max_attempts} attempts")
        sys.exit(1)
    
    block_number = receipt.blockNumber
    print(f"Transaction mined in block {block_number}")
    
    # Calculate block range to fetch
    start_block = fork_block + 1  # Start from block after fork
    end_block = block_number      # End at the attack block
    
    # Fetch all blocks in range
    blocks = {}
    print(f"Fetching all blocks from {start_block} to {end_block}...")
    
    for block_num in range(start_block, end_block + 1):
        try:
            print(f"Fetching block {block_num}...")
            block = w3.eth.get_block(block_num, full_transactions=True)
            blocks[block_num] = block
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")
    
    # Also save the attack transaction's block number for reference
    blocks['attack_block_number'] = block_number
    
    return blocks

def save_block_data(blocks: Dict, output_file: str):
    """Save all block data to a single JSON file with a 'blocks' key."""
    output_path = Path(output_file)
    output_dir = output_path.parent
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {output_dir}: {e}")
        sys.exit(1)
    
    # Get the attack block number
    attack_block_number = blocks.get('attack_block_number')
    if not attack_block_number:
        print("Warning: Could not determine attack block number")
    
    # Remove the special 'attack_block_number' key before processing blocks
    if 'attack_block_number' in blocks:
        del blocks['attack_block_number']
    
    # Create a dictionary to hold all block data
    output_data = {
        "attackBlockNumber": attack_block_number,
        "blocks": {}
    }
    
    # Convert all blocks to serializable format and add to output
    print(f"Processing {len(blocks)} blocks...")
    for block_num, block_data in blocks.items():
        try:
            # Convert block data to serializable format
            serializable_block = json.loads(Web3.to_json(block_data))
            output_data["blocks"][str(block_num)] = serializable_block
            print(f"Processed block {block_num}")
        except Exception as e:
            print(f"Error processing block {block_num}: {e}")
            # Attempt to manually serialize if possible
            try:
                serializable_block = {k: str(v) if isinstance(v, bytes) else v for k, v in dict(block_data).items()}
                # Further refine serialization for AttributeDict within transactions if needed
                if 'transactions' in serializable_block:
                    serializable_block['transactions'] = [
                        {k: str(v) if isinstance(v, bytes) else v for k, v in dict(tx).items()}
                        for tx in serializable_block['transactions']
                    ]
                output_data["blocks"][str(block_num)] = serializable_block
                print(f"Processed block {block_num} using simplified serialization")
            except Exception as e2:
                print(f"Failed to process block {block_num} even with simplified serialization: {e2}")
    
    # Save the complete data structure to the output file
    print(f"Saving all blocks to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"All blocks saved successfully to {output_path}")
    print(f"Saved data for {len(output_data['blocks'])} blocks with attack block #{attack_block_number}")

def main():
    args = parse_args()
    
    # Start anvil process
    anvil_process = start_anvil(args.rpc_url, args.fork_block, args.anvil_port)
    
    try:
        local_rpc_url = f"http://localhost:{args.anvil_port}"
        w3 = Web3(Web3.HTTPProvider(local_rpc_url))
        
        # Verify connection to anvil
        if not w3.is_connected():
            print(f"Failed to connect to Anvil at {local_rpc_url}")
            sys.exit(1)
        
        # Deploy contract
        contract_address = deploy_contract(args.contract_path, local_rpc_url, args.private_key)
        
        # Execute attack transaction
        tx_hash = execute_attack_tx(
            contract_address,
            args.attack_type,
            args.gas_limit,
            args.gas_threshold,
            local_rpc_url,
            args.private_key
        )
        
        # Get block data for all blocks from fork to attack
        blocks_data = get_block_data(w3, tx_hash, args.fork_block)
        
        # Save block data
        save_block_data(blocks_data, args.output_file)
        
        print("Block generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Terminate anvil process
        print("Terminating Anvil...")
        anvil_process.terminate()
        anvil_process.wait(timeout=5)

if __name__ == "__main__":
    main() 
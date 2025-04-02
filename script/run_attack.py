#!/usr/bin/env python3
"""
ZKarnage: Zero-Knowledge Proof Stress Testing System

Simplified script for targeting Flashbots transactions on hundred-block boundaries.
"""

import os
import sys
import json
import time
import uuid
import asyncio
import logging
import aiohttp
import traceback
import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
from eth_abi import encode
from eth_account import Account, messages
from eth_typing import Address

# Configure logging
def setup_logging():
    """Configure logging to both console and timestamped file."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate ISO format timestamp for the log filename
    timestamp = datetime.datetime.now().isoformat().replace(':', '-').replace('.', '-')
    log_filename = logs_dir / f"zkarnage-attack-{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Log format
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # Configure file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to file: {log_filename}")
    
    return logger

# Initialize logger
logger = setup_logging()

class ZKarnageError(Exception):
    """Base exception for ZKarnage errors."""
    pass

class FlashbotsManager:
    """Manages Flashbots bundle submission and simulation."""
    
    def __init__(self, w3: Web3, relay_url: str, account: Account):
        self.w3 = w3
        self.relay_url = relay_url
        self.account = account
    
    def _sign_flashbots_message(self, msg_body: str) -> str:
        """
        Create Flashbots-compatible signature for request authentication.
        
        Args:
            msg_body: JSON payload to be signed
        
        Returns:
            Signed message string in format 'address:signature'
        """
        # Get hash as hex string
        message_hash_hex = self.w3.keccak(text=msg_body).hex()
        
        # Create message object using the hash hex string
        message = messages.encode_defunct(text=message_hash_hex)
        
        # Sign the message
        signed_message = self.w3.eth.account.sign_message(message, self.account.key)
        
        # Format as address:signature
        signature = f"{self.account.address}:{signed_message.signature.hex()}"
        
        return signature
    
    async def simulate_bundle(
        self, 
        bundle: List[bytes], 
        target_block: int, 
        state_block: str = 'latest'
    ) -> Dict[str, Any]:
        """
        Simulate Flashbots bundle submission using eth_callBundle.
        
        Args:
            bundle: List of signed transaction bytes
            target_block: Block number to target
            state_block: State block to base simulation on
        
        Returns:
            Simulation result dictionary
        """
        try:
            # Convert transactions to hex strings without the 0x prefix for Flashbots
            hex_txs = [tx.hex() if not isinstance(tx, str) else tx for tx in bundle]
            
            # Ensure 0x prefix for Flashbots
            hex_txs = ["0x" + tx[2:] if tx.startswith("0x") else "0x" + tx for tx in hex_txs]
            
            # Debug print transaction data
            logger.info(f"Transaction data (first 100 chars): {hex_txs[0][:100]}...")
            logger.info(f"Transaction type: {hex_txs[0][2:4]}")  # Print transaction type (first byte after 0x)
            
            # Prepare simulation request
            sim_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_callBundle",
                "params": [{
                    "txs": hex_txs,
                    "blockNumber": hex(target_block),
                    "stateBlockNumber": state_block,
                    "timestamp": int(time.time())
                }]
            }
            
            # Convert request to JSON
            request_json = json.dumps(sim_request)
            
            # Debug print request
            logger.info(f"Simulation request: {request_json}")
            
            # Sign the request
            signature = self._sign_flashbots_message(request_json)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Flashbots-Signature': signature
            }
            
            # Debug print headers
            logger.info(f"Request headers: {headers}")
            
            # Send simulation request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.relay_url, 
                    data=request_json, 
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response body: {response_text}")
                    
                    if response.status != 200:
                        logger.error(f"Simulation request failed with status {response.status}")
                        return {"success": False, "error": response_text}
                    
                    result = json.loads(response_text)
                    
                    # Log simulation details
                    logger.info(f"Bundle simulation for block {target_block}")
                    logger.info(f"Gas used: {result.get('result', {}).get('totalGasUsed', 'N/A')}")
                    
                    # Check for simulation success (no reverts)
                    bundle_results = result.get('result', {}).get('results', [])
                    success = all(
                        not (res.get('error') or res.get('revert')) 
                        for res in bundle_results
                    )
                    
                    return {
                        "success": success,
                        "details": result.get('result', {}),
                        "raw_result": result
                    }
        
        except Exception as e:
            logger.error(f"Bundle simulation failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    async def submit_bundle(
        self, 
        bundle: List[bytes], 
        target_block: int, 
        min_timestamp: Optional[int] = None,
        max_timestamp: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Submit bundle to Flashbots relay using eth_sendBundle.
        
        Args:
            bundle: List of signed transaction bytes
            target_block: Block number to target
            min_timestamp: Minimum timestamp for bundle validity
            max_timestamp: Maximum timestamp for bundle validity
        
        Returns:
            Bundle submission result dictionary
        """
        try:
            # Convert transactions to hex strings with 0x prefix
            hex_txs = [tx.hex() if not isinstance(tx, str) else tx for tx in bundle]
            hex_txs = ["0x" + tx[2:] if tx.startswith("0x") else "0x" + tx for tx in hex_txs]
            
            # Debug print transaction data
            logger.info(f"Transaction data (first 100 chars): {hex_txs[0][:100]}...")
            logger.info(f"Transaction type: {hex_txs[0][2:4]}")  # Print transaction type (first byte after 0x)
            
            # Prepare bundle submission request
            bundle_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),  # Unique ID
                "method": "eth_sendBundle",
                "params": [{
                    "txs": hex_txs,
                    "blockNumber": hex(target_block),
                    "minTimestamp": min_timestamp or 0,
                    "maxTimestamp": max_timestamp or int(time.time()) + 420,  # 7 minutes from now
                    "replacementUuid": str(uuid.uuid4())
                }]
            }
            
            # Convert request to JSON
            request_json = json.dumps(bundle_request)
            
            # Debug print request
            logger.info(f"Bundle submission request: {request_json}")
            
            # Sign the request
            signature = self._sign_flashbots_message(request_json)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Flashbots-Signature': signature
            }
            
            # Debug print headers
            logger.info(f"Request headers: {headers}")
            
            # Send bundle submission request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.relay_url, 
                    data=request_json, 
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"Response status: {response.status}")
                    logger.info(f"Response body: {response_text}")
                    
                    if response.status != 200:
                        logger.error(f"Bundle submission failed with status {response.status}")
                        return None
                    
                    result = json.loads(response_text)
                    
                    # Extract bundle hash
                    bundle_hash = result.get('result', {}).get('bundleHash')
                    
                    if bundle_hash:
                        logger.info(f"Bundle submitted successfully to block {target_block}")
                        logger.info(f"Bundle Hash: {bundle_hash}")
                        return {
                            "bundle_hash": bundle_hash,
                            "raw_result": result
                        }
                    else:
                        logger.warning("No bundle hash returned")
                        return None
        
        except Exception as e:
            logger.error(f"Bundle submission failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def check_flashbots_status(self, bundle_hash: str, target_block: Optional[int] = None) -> Dict[str, Any]:
        """
        Check the status of a bundle submission with Flashbots using V2 API.
        
        Args:
            bundle_hash: The hash of the bundle to check
            target_block: The target block number (required for V2 API)
            
        Returns:
            Bundle status information
        """
        try:
            # V2 API requires blockNumber parameter
            if target_block is None:
                logger.error("Target block is required for flashbots_getBundleStatsV2")
                return {"success": False, "error": "Target block is required"}
            
            # Prepare params with required fields
            params = [{
                "bundleHash": bundle_hash,
                "blockNumber": hex(target_block)
            }]
            
            # Prepare bundle status request
            status_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "flashbots_getBundleStatsV2",
                "params": params
            }
            
            # Convert request to JSON
            request_json = json.dumps(status_request)
            
            # Debug print request
            logger.info(f"V2 Bundle status request: {request_json}")
            
            # Sign the request
            signature = self._sign_flashbots_message(request_json)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Flashbots-Signature': signature
            }
            
            # Send status request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.relay_url, 
                    data=request_json, 
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"Bundle V2 status response: {response_text}")
                    
                    if response.status != 200:
                        logger.error(f"Bundle status check failed with status {response.status}")
                        return {"success": False, "error": response_text}
                    
                    result = json.loads(response_text)
                    
                    # Log meaningful information from the V2 response
                    if 'result' in result:
                        status_result = result.get('result', {})
                        logger.info(f"Bundle is {'high priority' if status_result.get('isHighPriority') else 'standard priority'}")
                        logger.info(f"Bundle has{' ' if status_result.get('isSimulated') else ' not '}been simulated")
                        
                        if status_result.get('receivedAt'):
                            logger.info(f"Bundle was received at: {status_result.get('receivedAt')}")
                        
                        if status_result.get('simulatedAt'):
                            logger.info(f"Bundle was simulated at: {status_result.get('simulatedAt')}")
                        
                        builder_count = len(status_result.get('consideredByBuildersAt', []))
                        if builder_count > 0:
                            logger.info(f"Bundle was considered by {builder_count} builders")
                        
                        sealed_count = len(status_result.get('sealedByBuildersAt', []))
                        if sealed_count > 0:
                            logger.info(f"Bundle was sealed by {sealed_count} builders!")
                        elif builder_count > 0 and sealed_count == 0:
                            logger.warning("Bundle was considered but not sealed by any builders")
                    
                    return result
        
        except Exception as e:
            logger.error(f"Error checking bundle V2 status: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def check_user_stats(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Check user stats with Flashbots using flashbots_getUserStatsV2.
        
        Args:
            block_number: A recent block number (required to prevent replay attacks)
            
        Returns:
            User stats information
        """
        try:
            # Use current block if none provided
            if block_number is None:
                block_number = self.w3.eth.block_number
            
            # Prepare params with required fields
            params = [{
                "blockNumber": hex(block_number)
            }]
            
            # Prepare user stats request
            stats_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "flashbots_getUserStatsV2",
                "params": params
            }
            
            # Convert request to JSON
            request_json = json.dumps(stats_request)
            
            # Debug print request
            logger.info(f"User stats request: {request_json}")
            
            # Sign the request
            signature = self._sign_flashbots_message(request_json)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Flashbots-Signature': signature
            }
            
            # Send stats request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.relay_url, 
                    data=request_json, 
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"User stats response: {response_text}")
                    
                    if response.status != 200:
                        logger.error(f"User stats check failed with status {response.status}")
                        return {"success": False, "error": response_text}
                    
                    result = json.loads(response_text)
                    
                    # Log meaningful information from the response
                    if 'result' in result:
                        stats = result.get('result', {})
                        is_high_priority = stats.get('isHighPriority', False)
                        logger.info(f"User has {'HIGH' if is_high_priority else 'STANDARD'} priority status")
                        
                        # Format payments as ETH for better readability
                        all_time_payments = stats.get('allTimeValidatorPayments', '0')
                        all_time_eth = float(all_time_payments) / 1e18 if all_time_payments else 0
                        logger.info(f"All-time validator payments: {all_time_eth:.4f} ETH")
                        
                        last_7d_payments = stats.get('last7dValidatorPayments', '0')
                        last_7d_eth = float(last_7d_payments) / 1e18 if last_7d_payments else 0
                        logger.info(f"Last 7 days validator payments: {last_7d_eth:.4f} ETH")
                        
                        # Log gas usage
                        all_time_gas = stats.get('allTimeGasSimulated', '0')
                        logger.info(f"All-time gas simulated: {all_time_gas}")
                    
                    return result
        
        except Exception as e:
            logger.error(f"Error checking user stats: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    async def check_transaction_status(self, tx_hash: str, network: str = "mainnet") -> Dict[str, Any]:
        """
        Check transaction status using web3.py.
        
        Args:
            tx_hash: Transaction hash to check
            network: Network to check on (not used with web3.py implementation)
            
        Returns:
            Transaction status information
        """
        try:
            # Try to get the transaction receipt
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    # Transaction has been mined
                    success = receipt.status == 1
                    logger.info(f"Transaction Status: {'SUCCESS' if success else 'FAILED'}")
                    
                    # Get the full transaction for more details
                    tx = self.w3.eth.get_transaction(tx_hash)
                    
                    # Log transaction details
                    logger.info(f"From: {tx.get('from', 'N/A')}")
                    logger.info(f"To: {tx.get('to', 'N/A')}")
                    logger.info(f"Gas Limit: {tx.get('gas', 'N/A')}")
                    logger.info(f"Max Fee: {tx.get('maxFeePerGas', 'N/A')}")
                    logger.info(f"Priority Fee: {tx.get('maxPriorityFeePerGas', 'N/A')}")
                    logger.info(f"Block Number: {receipt.blockNumber}")
                    logger.info(f"Gas Used: {receipt.gasUsed}")
                    
                    return {
                        "success": True,
                        "status": "INCLUDED" if success else "FAILED",
                        "transaction": {
                            "from": tx.get('from'),
                            "to": tx.get('to'),
                            "gasLimit": tx.get('gas'),
                            "maxFeePerGas": tx.get('maxFeePerGas'),
                            "maxPriorityFeePerGas": tx.get('maxPriorityFeePerGas'),
                            "blockNumber": receipt.blockNumber,
                            "gasUsed": receipt.gasUsed
                        }
                    }
                
            except TransactionNotFound:
                # Transaction is not mined yet
                # Try to get pending transaction
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    if tx:
                        logger.info("Transaction Status: PENDING")
                        logger.info("Transaction is in mempool but not mined yet")
                        
                        return {
                            "success": True,
                            "status": "PENDING",
                            "transaction": {
                                "from": tx.get('from'),
                                "to": tx.get('to'),
                                "gasLimit": tx.get('gas'),
                                "maxFeePerGas": tx.get('maxFeePerGas'),
                                "maxPriorityFeePerGas": tx.get('maxPriorityFeePerGas')
                            }
                        }
                    else:
                        logger.warning("Transaction not found in mempool or blockchain")
                        return {
                            "success": False,
                            "status": "NOT_FOUND",
                            "error": "Transaction not found in mempool or blockchain"
                        }
                        
                except Exception as e:
                    logger.warning(f"Error checking pending transaction: {e}")
                    return {
                        "success": False,
                        "status": "ERROR",
                        "error": f"Error checking pending transaction: {str(e)}"
                    }
            
        except Exception as e:
            logger.error(f"Error checking transaction status: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "status": "ERROR",
                "error": str(e)
            }

class ZKarnage:
    """Main ZKarnage attack orchestration class."""
    
    def __init__(
        self, 
        w3: Web3, 
        account: Account, 
        relay_url: str, 
        contract_address: Optional[Address] = None
    ):
        self.w3 = w3
        self.account = account
        self.contract_address = contract_address
        self.flashbots = FlashbotsManager(w3, relay_url, account)
    
    def get_next_hundred_block(self, current_block: Optional[int] = None) -> int:
        """
        Calculate the next block divisible by 100.
        
        Args:
            current_block: Starting block number (default: current blockchain block)
        
        Returns:
            Next block number divisible by 100
        """
        current = current_block or self.w3.eth.block_number
        return current + (100 - (current % 100))
    
    async def check_bundle_status(self, bundle_hash: str, target_block: int, tx_hash: Optional[str] = None) -> bool:
        """
        Check if a bundle was included using Flashbots API.
        
        Args:
            bundle_hash: The hash of the bundle to check
            target_block: The target block number
            tx_hash: Optional transaction hash to check individual tx status
            
        Returns:
            Whether the bundle was included
        """
        try:
            # Wait until we've reached the target block
            current_block = self.w3.eth.block_number
            if current_block < target_block:
                logger.info(f"Waiting for target block {target_block}, current block is {current_block}")
                
                last_logged_block = current_block
                last_status_check = 0
                while current_block < target_block:
                    # Check bundle status every 15 seconds while waiting
                    if time.time() - last_status_check > 15:
                        logger.info(f"Checking current bundle status while waiting...")
                        
                        # Use the V2 API for more detailed status
                        status = await self.flashbots.check_flashbots_status(bundle_hash, target_block)
                        
                        if 'result' in status:
                            status_result = status.get('result', {})
                            
                            # Check for builder consideration
                            builders = status_result.get('consideredByBuildersAt', [])
                            seals = status_result.get('sealedByBuildersAt', [])
                            
                            if seals:
                                logger.info(f"EXCELLENT! Bundle has been sealed by {len(seals)} builders")
                                for sealed in seals:
                                    logger.info(f"  - Sealed by: {sealed.get('pubkey')[:16]}... at {sealed.get('timestamp')}")
                            elif builders:
                                logger.info(f"Bundle is being considered by {len(builders)} builders")
                            else:
                                # If no builders are considering it, analyze why
                                if status_result.get('isHighPriority', False):
                                    logger.info("Bundle is high priority but not yet considered by builders")
                            
                            # Check simulation status
                            if status_result.get('isSimulated', False):
                                logger.info(f"Bundle was simulated at: {status_result.get('simulatedAt')}")
                            else:
                                logger.warning("Bundle has not been simulated yet")
                        
                        last_status_check = time.time()
                
                    await asyncio.sleep(5)  # Check every 5 seconds
                    current_block = self.w3.eth.block_number
                    
                    # Only log when block number changes
                    if current_block > last_logged_block:
                        logger.info(f"Waiting for block {target_block}, current block is {current_block}")
                        last_logged_block = current_block
                
                logger.info(f"Target block {target_block} reached")
            
            # Now that we've reached the target block, check for our transaction
            logger.info(f"Checking block {target_block} for bundle inclusion")
            
            # Get the block and check for our transaction
            block = self.w3.eth.get_block(target_block, full_transactions=True)
            tx_count = len(block.transactions)
            logger.info(f"Block contains {tx_count} transactions")
            
            # Check for our transaction in the block
            for tx in block.transactions:
                # Try to match our bundle hash or tx hash
                tx_hash_current = self.w3.to_hex(tx.hash) if hasattr(tx, 'hash') else tx
                
                # If we have a tx_hash to match against, use it
                if tx_hash and tx_hash_current.lower() == tx_hash.lower():
                    logger.info(f"Found our transaction in the block: {tx_hash}")
                    return True
                
                # Get receipt to check status
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash_current)
                    if receipt:
                        # Check if this transaction is from our account
                        if receipt.get('from', '').lower() == self.account.address.lower():
                            logger.info(f"Found our transaction: {tx_hash_current}")
                            logger.info(f"Transaction status: {'Success' if receipt.status == 1 else 'Failed'}")
                            return receipt.status == 1
                except Exception as e:
                    logger.warning(f"Error checking receipt for tx {tx_hash_current}: {e}")
            
            # Now that target block has passed, check transaction status using the API
            if tx_hash:
                logger.info(f"Checking individual transaction status via Flashbots API after target block...")
                final_tx_status = await self.flashbots.check_transaction_status(tx_hash)
                
                status = final_tx_status.get("status", "UNKNOWN")
                logger.info(f"Transaction Status: {status}")
                
                if status == "INCLUDED":
                    logger.info(f"Transaction {tx_hash} was confirmed as included via Transaction Status API")
                    return True
            
            # Do one final check with the V2 API to confirm status
            final_status = await self.flashbots.check_flashbots_status(bundle_hash, target_block)
            
            if 'result' in final_status:
                status_result = final_status.get('result', {})
                seals = status_result.get('sealedByBuildersAt', [])
                
                if seals:
                    logger.warning(f"Bundle was sealed by {len(seals)} builders but not found in block {target_block}")
                    logger.warning("This is unusual and may indicate the bundle was outbid or the block producer chose a different bundle")
                else:
                    logger.warning(f"Bundle with hash {bundle_hash} was not sealed by any builders")
                    logger.warning("The bundle was likely not competitive enough for inclusion")
            
            logger.warning(f"Bundle with hash {bundle_hash} not found in block {target_block}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking bundle status: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def execute_attack(self, target_hundred: bool = True, fast_mode: bool = False) -> bool:
        """
        Execute ZKarnage attack.
        
        Args:
            target_hundred: Whether to target block divisible by 100
            fast_mode: If True, target a block just 2 blocks ahead instead of waiting for hundred-block
        
        Returns:
            Whether attack was successful
        """
        try:
            # Validate contract is deployed
            if not self.contract_address:
                raise ZKarnageError("No contract address specified")
            
            # Determine target block
            current_block = self.w3.eth.block_number
            if fast_mode:
                target_block = current_block + 2  # Target just 2 blocks ahead for quick testing
                logger.info("FAST MODE: Targeting block 2 blocks ahead")
            else:
                target_block = self.get_next_hundred_block(current_block) if target_hundred else current_block + 1
            
            # Log attack details
            logger.info(f"Preparing ZKarnage attack")
            logger.info(f"Current block: {current_block}")
            logger.info(f"Target block: {target_block}")
            
            # Check user stats to determine if we need higher fees
            logger.info("Checking Flashbots user stats and reputation...")
            user_stats = await self.flashbots.check_user_stats(current_block)
            is_high_priority = False
            
            if 'result' in user_stats:
                is_high_priority = user_stats.get('result', {}).get('isHighPriority', False)
                
                if not is_high_priority:
                    logger.warning("Account does not have high priority status with Flashbots")
                    logger.warning("Bundles may need higher priority fees to be competitive")
                else:
                    logger.info("Account has HIGH PRIORITY status with Flashbots - bundles will be prioritized")
            
            # Prepare transaction with priority fee adjusted based on reputation
            tx = self._prepare_attack_transaction(target_block, is_high_priority)
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            
            # Extract transaction hash for later status checks
            tx_hash = signed_tx.hash.hex()
            logger.info(f"Transaction hash: {tx_hash}")
            
            # Simulate bundle
            logger.info("Simulating bundle...")
            sim_result = await self.flashbots.simulate_bundle(
                [signed_tx.rawTransaction], 
                target_block
            )
            
            # Check for transaction revert in simulation results
            if sim_result.get('raw_result', {}).get('result', {}).get('results', []):
                tx_results = sim_result.get('raw_result', {}).get('result', {}).get('results', [])
                for i, tx_result in enumerate(tx_results):
                    if tx_result.get('error'):
                        logger.error(f"Transaction {i} failed with error: {tx_result.get('error')}")
                        # If there's a revert reason, try to decode it
                        if 'revert' in tx_result.get('error', '') and tx_result.get('revert'):
                            logger.error(f"Revert reason: {tx_result.get('revert')}")
            
            # Check simulation result in detail
            if not sim_result.get('success', False):
                logger.error("Bundle simulation failed")
                
                # Log detailed simulation error
                if 'error' in sim_result:
                    logger.error(f"Simulation error: {sim_result['error']}")
                
                # Provide additional helpful information
                logger.error("Possible issues:")
                logger.error("1. Verify contract function signature: executeAttack(address[])")
                logger.error("2. Check if target contract exists at the specified address")
                logger.error("3. Check if the account has sufficient gas")
                
                # Check if the transaction is actually successful despite errors
                if sim_result.get('raw_result', {}).get('result', {}).get('bundleHash'):
                    logger.info("Transaction produced a bundleHash, proceeding with submission anyway")
                else:
                    return False
            
            # Log simulation details
            sim_details = sim_result.get('details', {})
            logger.info(f"Simulation successful")
            logger.info(f"Total gas used: {sim_details.get('totalGasUsed', 'N/A')}")
            logger.info(f"Coinbase difference: {sim_details.get('coinbaseDiff', 'N/A')}")
            
            # Submit bundle
            logger.info("Submitting bundle to Flashbots...")
            bundle_submission = await self.flashbots.submit_bundle(
                [signed_tx.rawTransaction], 
                target_block
            )
            
            # Check bundle submission
            if not bundle_submission:
                logger.error("Bundle submission failed")
                return False
            
            # Log bundle submission details
            bundle_hash = bundle_submission.get('bundle_hash', 'N/A')
            logger.info(f"Bundle submitted successfully")
            logger.info(f"Bundle Hash: {bundle_hash}")
            
            # Check transaction status using the transaction status API
            logger.info(f"Checking individual transaction status via Flashbots API...")
            tx_status = await self.flashbots.check_transaction_status(tx_hash)
            logger.info(f"Transaction status API response: {json.dumps(tx_status, indent=2)}")
            
            # Check bundle status with Flashbots V2 API
            logger.info(f"Checking bundle status with Flashbots V2 API...")
            status = await self.flashbots.check_flashbots_status(bundle_hash, target_block)
            
            # Process the V2 API response
            if 'result' in status:
                status_result = status.get('result', {})
                logger.info(f"Bundle Status V2: {json.dumps(status_result, indent=2)}")
                
                # Display key bundle metrics
                is_high_priority = status_result.get('isHighPriority', False)
                is_simulated = status_result.get('isSimulated', False)
                
                logger.info(f"Bundle priority: {'HIGH' if is_high_priority else 'STANDARD'}")
                logger.info(f"Bundle simulation: {'COMPLETED' if is_simulated else 'PENDING'}")
                
                # Check if any builders are considering the bundle
                builders_considering = status_result.get('consideredByBuildersAt', [])
                if builders_considering:
                    logger.info(f"Bundle is being considered by {len(builders_considering)} builders")
                else:
                    logger.warning(f"Bundle is not being considered by any builders")
                
                # Check if any builders have sealed the bundle
                builders_sealed = status_result.get('sealedByBuildersAt', [])
                if builders_sealed:
                    logger.info(f"GREAT NEWS! Bundle has been sealed by {len(builders_sealed)} builders")
                    for sealed in builders_sealed:
                        logger.info(f"  - Sealed by: {sealed.get('pubkey')[:16]}... at {sealed.get('timestamp')}")
            else:
                logger.warning(f"No status result available for bundle {bundle_hash}")
            
            # Wait for the target block and check bundle inclusion
            logger.info(f"Waiting for target block {target_block} to check bundle inclusion")
            bundle_included = await self.check_bundle_status(bundle_hash, target_block, tx_hash)
            
            if bundle_included:
                logger.info(f"Bundle successfully included in block {target_block}")
                
                return True
            else:
                logger.warning(f"Bundle not included in target block {target_block}")
                
                return False
            
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _prepare_attack_transaction(self, target_block: int, is_high_priority: bool) -> Dict[str, Any]:
        """
        Prepare attack transaction.
        
        Args:
            target_block: Block number to target
            is_high_priority: Whether the account has high priority status
        
        Returns:
            Transaction dictionary
        """
        # Get latest block for base fee estimation
        latest = self.w3.eth.get_block("latest")
        base_fee = latest.get("baseFeePerGas", self.w3.eth.gas_price)
        
        # ABI for executing attack (simplified)
        attack_abi = {
            "inputs": [{"name": "targets", "type": "address[]"}],
            "name": "executeAttack",
            "type": "function"
        }
        
        # Expanded list of contract targets
        contract_targets = [
            Web3.to_checksum_address("0x1908D2bD020Ba25012eb41CF2e0eAd7abA1c48BC"),
            Web3.to_checksum_address("0xa102b6Eb23670B07110C8d316f4024a2370Be5dF"),
            Web3.to_checksum_address("0x84ab2d6789aE78854FbdbE60A9873605f4Fd038c"),
            Web3.to_checksum_address("0xfd96A06c832f5F2C0ddf4ba4292988Dc6864f3C5"),
            Web3.to_checksum_address("0xE233472882bf7bA6fd5E24624De7670013a079C1"),
            Web3.to_checksum_address("0xd3A3d92dbB569b6cd091c12fAc1cDfAEB8229582"),
            Web3.to_checksum_address("0xB95c8fB8a94E175F957B5044525F9129fbA0fE0C"),
            Web3.to_checksum_address("0x1CE8147357D2E68807a79664311aa2dF47c2E4bb"),
            Web3.to_checksum_address("0x557C810F3F47849699B4ac3D52cb1edcd528B4C0"),
            Web3.to_checksum_address("0x4AEF3B98F153f6d15339E75e1CF3e5a4513093ae"),
            Web3.to_checksum_address("0xaA6B611c840e45c7E883F6c535438bB70ce5cc1C"),
            Web3.to_checksum_address("0xf56a3084cC5EF73265fdf9034E53b07124A60018"),
        ]
        
        # Debug print addresses
        logger.info(f"Contract targets: {contract_targets}")
        logger.info(f"Number of targets: {len(contract_targets)}")
        
        # Encode the function call data using eth-abi
        encoded_data = encode(['address[]'], [contract_targets])
        
        # Debug print encoded data
        logger.info(f"Encoded data (hex): {encoded_data.hex()}")
        
        # Get function signature - ensure we get exactly 4 bytes
        function_selector = Web3.keccak(text="executeAttack(address[])").hex()[0:10]  # 0x + 8 chars (4 bytes)
        logger.info(f"Function selector: {function_selector}")
        
        # Full transaction data
        data = function_selector + encoded_data.hex()
        logger.info(f"Complete transaction data: {data[:64]}...")
        
        # Set much more competitive fees for Flashbots
        # Base fee plus a significant premium to ensure inclusion
        # Set higher priority fee if the account does NOT have high priority status
        # If we already have high priority status, we can use a more reasonable fee
        if is_high_priority:
            max_priority_fee = Web3.to_wei(5, 'gwei')  # Lower fee for high priority accounts
            max_fee_per_gas = base_fee + Web3.to_wei(10, 'gwei')
            logger.info("Using standard priority fee (high priority account)")
        else:
            max_priority_fee = Web3.to_wei(15, 'gwei')  # Much higher fee for non-high priority accounts
            max_fee_per_gas = base_fee + Web3.to_wei(20, 'gwei')  # Ensure max fee > priority fee
            logger.info("Using increased priority fee to compensate for standard priority status")
        
        logger.info(f"Using competitive fees - Max Fee: {Web3.from_wei(max_fee_per_gas, 'gwei')} gwei, " 
                   f"Priority Fee: {Web3.from_wei(max_priority_fee, 'gwei')} gwei")
        
        # Create transaction dictionary with all required fields
        tx = {
            'type': 2,  # EIP-1559 transaction
            'to': self.contract_address,
            'from': self.account.address,
            'gas': 500_000,
            'value': 0,  # Important to set explicitly
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'data': data,
            'chainId': self.w3.eth.chain_id,
        }
        
        logger.info(f"Transaction prepared: {tx}")
        return tx

async def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Check for fast mode flag
    fast_mode = "--fast" in sys.argv
    if fast_mode:
        logger.info("Fast mode enabled: will target block 2 blocks ahead")
    
    # Required environment variables
    ETH_RPC_URL = os.getenv('ETH_RPC_URL')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    FLASHBOTS_RELAY_URL = os.getenv('FLASHBOTS_RELAY_URL', 'https://relay.flashbots.net')
    CONTRACT_ADDRESS = os.getenv('ZKARNAGE_CONTRACT_ADDRESS', "0x55A942D18C0C57975e834Ee3afc8DEe01b674C43")
    
    # Validate required variables
    if not all([ETH_RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS]):
        logger.error("Missing required environment variables")
        return 1
    
    # Initialize Web3
    w3 = Web3(HTTPProvider(ETH_RPC_URL))
    
    # Validate connection
    if not w3.is_connected():
        logger.error("Failed to connect to Ethereum network")
        return 1
    
    # Create account
    account = Account.from_key(PRIVATE_KEY)
    
    # Initialize ZKarnage
    zkarnage = ZKarnage(
        w3=w3, 
        account=account, 
        relay_url=FLASHBOTS_RELAY_URL,
        contract_address=Web3.to_checksum_address(CONTRACT_ADDRESS)
    )
    
    # For fast mode, just run once
    if fast_mode:
        logger.info("Fast mode: Running single attack attempt")
        success = await zkarnage.execute_attack(target_hundred=True, fast_mode=True)
        return 0 if success else 1
    
    # For hundred-block mode, keep trying until success
    logger.info("Continuous mode: Will keep trying until a successful attack")
    attempt_number = 1
    
    while True:
        logger.info(f"=== Starting attack attempt #{attempt_number} ===")
        
        # Get current block to estimate time until next hundred-block
        current_block = w3.eth.block_number
        next_hundred = zkarnage.get_next_hundred_block(current_block)
        blocks_to_wait = next_hundred - current_block
        
        logger.info(f"Current block: {current_block}")
        logger.info(f"Next target block: {next_hundred} ({blocks_to_wait} blocks away)")
        
        # Run the attack
        success = await zkarnage.execute_attack(target_hundred=True, fast_mode=False)
        
        if success:
            logger.info(f"Attack succeeded on attempt #{attempt_number}!")
            return 0
        
        logger.warning(f"Attack attempt #{attempt_number} failed. Preparing for next attempt...")
        attempt_number += 1
        
        # Wait a bit before trying again to avoid hammering the API
        # Calculate approximately how long until the next hundred-block
        # Assuming ~12 second block times 
        estimated_wait = blocks_to_wait * 12 / 2 
        logger.info(f"Waiting {estimated_wait:.0f} seconds before next attempt...")
        await asyncio.sleep(estimated_wait)

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
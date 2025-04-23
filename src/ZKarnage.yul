// SPDX-License-Identifier: MIT
object "ZKarnage" {
  code {
    // Constructor
    datacopy(0, dataoffset("Runtime"), datasize("Runtime"))
    return(0, datasize("Runtime"))
  }
  object "Runtime" {
    code {
      // This contract is inspired by evm-stress.yul from the agglayer repository
      // https://github.com/agglayer/e2e/blob/jhilliard/evm-stress-readme/core/contracts/evm-stress/README.org
      // It exposes a single function that runs various EVM operations in a loop until a gas threshold is reached

      // Function selector is the first 4 bytes of the calldata
      let selector := shr(224, calldataload(0))
      switch selector
      // Function: f(uint256,uint256,uint256)
      case 0xbf06dbf1 {
        // Parse function arguments
        // First arg: op_code - The operation to execute
        let op_code := calldataload(4)
        // Second arg: limit - Gas threshold to stop the loop
        let limit := calldataload(36)
        // Third arg: extra - Optional additional parameters
        let extra := calldataload(68)

        // Store the result value (if any)
        let i := 0

        // *** DEBUG LOGGING START ***
        // Log the initial gas and limit values before entering the specific handler
        let initial_gas := gas()
        mstore(0, 0x494E49545F4741533A0000000000000000000000000000000000000000000000) // "INIT_GAS:"
        log1(0, 32, initial_gas)
        mstore(0, 0x494E49545F4C494D49543A000000000000000000000000000000000000000000) // "INIT_LIMIT:"
        log1(0, 32, limit)
        // *** DEBUG LOGGING END ***

        // Handle different operation types
        switch op_code
        
        // KECCAK256 Handler (0x0003)
        case 0x0003 {
          mstore(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          // *** DEBUG LOGGING START ***
          let pre_loop_gas_k := gas()
          mstore(0, 0x4B5F4741533A0000000000000000000000000000000000000000000000000000) // "K_GAS:"
          log1(0, 32, pre_loop_gas_k)
          mstore(0, 0x4B5F4C494D49543A000000000000000000000000000000000000000000000000) // "K_LIMIT:"
          log1(0, 32, limit)
          // *** DEBUG LOGGING END ***
          for {} gt(gas(), limit) {} {
            // Input is modified slightly each iteration to avoid optimizations
            mstore(0, not(mload(0)))
            i := keccak256(0, 32) 
          }
          // Store result of final operation
          mstore(0, i)
        }

        // SHA-256 Handler (0x0023)
        case 0x0023 {
          // Set up memory with test data
          mstore(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          mstore(32, 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)
          // *** DEBUG LOGGING START ***
          let pre_loop_gas_s := gas()
          mstore(0, 0x535F4741533A0000000000000000000000000000000000000000000000000000) // "S_GAS:"
          log1(0, 32, pre_loop_gas_s)
          mstore(0, 0x535F4C494D49543A000000000000000000000000000000000000000000000000) // "S_LIMIT:"
          log1(0, 32, limit)
          // *** DEBUG LOGGING END ***
          for {} gt(gas(), limit) {} {
            // Modify input data slightly each iteration
            mstore(0, not(mload(0)))
            // Call SHA-256 precompile (address 0x2)
            pop(staticcall(gas(), 0x2, 0, 64, 96, 32))
            i := mload(96)
          }
          // Store result
          mstore(0, i)
        }

        // ECRECOVER Handler (0x0021)
        case 0x0021 {
          // Data for a valid signature recovery
          mstore(0, 0x456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef3) // Hash
          mstore(32, 28) // v
          mstore(64, 0x9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608) // r
          mstore(96, 0x4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada) // s
          // *** DEBUG LOGGING START ***
          let pre_loop_gas_e := gas()
          mstore(0, 0x455F4741533A0000000000000000000000000000000000000000000000000000) // "E_GAS:"
          log1(0, 32, pre_loop_gas_e)
          mstore(0, 0x455F4C494D49543A000000000000000000000000000000000000000000000000) // "E_LIMIT:"
          log1(0, 32, limit)
          // *** DEBUG LOGGING END ***
          for {} gt(gas(), limit) {} {
            // Call ecrecover precompile (address 0x1)
            pop(staticcall(gas(), 0x1, 0, 128, 160, 32))
            i := mload(160)
          }
          // Store result
          mstore(0, i)
        }

        // MODEXP Handler (0x0027)
        case 0x0027 {
          // Set up inputs for modular exponentiation
          // Base length = 32 bytes
          mstore(0, 32)
          // Exponent length = 32 bytes
          mstore(32, 32)
          // Modulus length = 32 bytes
          mstore(64, 32)
          // Base = random large number
          mstore(96, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          // Exponent = random large number
          mstore(128, 0x8fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          // Modulus = random large prime-like number
          mstore(160, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff43)
           // *** DEBUG LOGGING START ***
          let pre_loop_gas_m := gas()
          mstore(0, 0x4D5F4741533A0000000000000000000000000000000000000000000000000000) // "M_GAS:"
          log1(0, 32, pre_loop_gas_m)
          mstore(0, 0x4D5F4C494D49543A000000000000000000000000000000000000000000000000) // "M_LIMIT:"
          log1(0, 32, limit)
          // *** DEBUG LOGGING END ***
          for {} gt(gas(), limit) {} {
            // Call ModExp precompile (address 0x5)
            pop(staticcall(gas(), 0x5, 0, 192, 192, 32))
            i := mload(192)
          }
          // Store result
          mstore(0, i)
        }

        default {
          // Unsupported operation
          mstore(0, 0x4641494c21)  // "FAIL!"
          revert(0, 0x20)
        }

        // Done, log and return the result
        // We use log0 here as a simple way to return the final result (i) stored at mem[0]
        // It will also appear in the logs which can be helpful.
        log0(0, 32)
        return(0, 32)
      }

      default {
        // Unknown function selector
        revert(0, 0)
      }
    }
  }
} 
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

        // Handle different operation types
        switch op_code
        
        // KECCAK256 Handler (0x0003)
        case 0x0003 {
          // Initialize memory with a constant value
          mstore(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          
          // Standard for loop but with minimal operations inside
          for { } gt(gas(), limit) { } {
            // Direct keccak256 computation with no other operations
            i := keccak256(0, 32)
          }
          
          // Direct return from the handler
          return(0, 32)
        }

        // SHA-256 Handler (0x0023)
        case 0x0023 {
          // Set up memory with test data
          mstore(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
          mstore(32, 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee)
          
          // Prepare output area
          let output_ptr := 96
          
          // Standard for loop but with minimal operations inside
          for { } gt(gas(), limit) { } {
            // Direct SHA-256 precompile call with no other operations
            pop(staticcall(gas(), 0x2, 0, 64, output_ptr, 32))
          }
          
          // Direct return from the handler
          return(0, 32)
        }

        // ECRECOVER Handler (0x0021)
        case 0x0021 {
          // Data for a valid signature recovery
          mstore(0, 0x456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef3) // Hash
          mstore(32, 28) // v
          mstore(64, 0x9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608) // r
          mstore(96, 0x4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada) // s
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
          for {} gt(gas(), limit) {} {
            // Call ModExp precompile (address 0x5)
            pop(staticcall(gas(), 0x5, 0, 192, 192, 32))
            i := mload(192)
          }
          // Store result
          mstore(0, i)
        }

        // BN_PAIRING Handler (0x0008) - Precompile at address 0x8
        case 0x0008 {
          // Minimal valid input for one pairing check: G1=(1, 2), G2=(complex point)
          // G1 point P = (1, 2)
          mstore(0, 1)  // P.x
          mstore(32, 2) // P.y
          // G2 point Q = (Qx, Qy) where Qx and Qy are Fq2 elements (re, im)
          // Q.x.re = 1155973203298638710799100402139228378363575190426317474150979597744772816670
          mstore(64, 0x1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed)
          // Q.x.im = 10857046999023057135941562093288740319954639648605465068009193076701047208282
          mstore(96, 0x17e7e1150fa774c08dce13bbe6d7534fddd3e561194d684fabfaada0e02d46a6)
          // Q.y.re = 8495653923123431417604973247469564034501869131102880983836177743231711808642
          mstore(128, 0x017c68d019582d32ca3a7da470d8cb50ac21586340781f6a10f78f89d3467882)
          // Q.y.im = 8714619439783156203944996167522676416109994784111812485956966958999386448433
          mstore(160, 0x0173f0ae878e748854e3b7958325aa47772398982071ea59101a036011a61011)

          // Output buffer (although we mostly discard the result)
          let output_ptr := 256

          for {} gt(gas(), limit) {} {
            // Call BN_PAIRING precompile (address 0x8)
            // Input data starts at memory 0 and is 192 bytes long (6 * 32 bytes)
            // Output is 32 bytes (0 or 1) written to output_ptr
            pop(staticcall(gas(), 0x8, 0, 192, output_ptr, 32))
            i := mload(output_ptr) // Keep track of the last result (0 or 1)
          }
          // Store the last result
          mstore(0, i)
        }

        default {
          // Unsupported operation
          mstore(0, 0x4641494c21)  // "FAIL!"
          revert(0, 0x20)
        }

        // Return the result
        return(0, 32)
      }

      default {
        // Unknown function selector
        revert(0, 0)
      }
    }
  }
} 
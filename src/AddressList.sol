// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AddressList
 * @dev This library contains all of the addresses that we'll target with our attack
 * These addresses have been curated to contain large contracts that will cause
 * significant overhead for ZK provers.
 */
library AddressList {
    function getTargetAddresses() internal pure returns (address[] memory) {
        // We'll allocate the array with exactly the right size for all addresses
        address[] memory targets = new address[](6);
        // Big contracts collected from bigquery
        targets[0] = 0x1908D2bD020Ba25012eb41CF2e0eAd7abA1c48BC;
        targets[1] = 0xa102b6Eb23670B07110C8d316f4024a2370Be5dF;
        targets[2] = 0x84ab2d6789aE78854FbdbE60A9873605f4Fd038c;
        targets[3] = 0xfd96A06c832f5F2C0ddf4ba4292988Dc6864f3C5;
        targets[4] = 0xE233472882bf7bA6fd5E24624De7670013a079C1;
        targets[5] = 0xd3A3d92dbB569b6cd091c12fAc1cDfAEB8229582;
        // targets[6] = 0xB95c8fB8a94E175F957B5044525F9129fbA0fE0C;
        // targets[7] = 0x1CE8147357D2E68807a79664311aa2dF47c2E4bb;
        // targets[8] = 0x557C810F3F47849699B4ac3D52cb1edcd528B4C0;
        // targets[9] = 0x4AEF3B98F153f6d15339E75e1CF3e5a4513093ae;
        // targets[10] = 0xaA6B611c840e45c7E883F6c535438bB70ce5cc1C;
        // targets[11] = 0xf56a3084cC5EF73265fdf9034E53b07124A60018;
        // targets[12] = 0x049Bcfc78720d662c27ca3f985E299e576cC113D;
        // targets[13] = 0x856Aa0d05f93599ADf9b6131853EC5f0557A9556;
        // targets[14] = 0x9964778500A1a15BbA8d11b958Ac3a1954c1738A;
        // targets[15] = 0x7DE6598b348f7e9A7EBFeB641f1F2d73A4aD30dA;
        // targets[16] = 0x2741D2aEa27a3463eC0ED1824b2147b5CA00D82F;
        // targets[17] = 0x8B319591D75B89A9594e9d570640Edd86CC6E554;
        // targets[18] = 0xA2BcD2bbACFB648014f542057a8378b621Fe86BA;
        // targets[19] = 0xe5aea18B24961d3717e049F36e65cb60d0aF6F76;
        // targets[20] = 0x38D7a126f4d978358313365F3f23Cf5620E2B6bB;
        // targets[21] = 0xa503eA1c72bD3B897703B229Ef75398a20E70439;
        // targets[22] = 0x692f9411301D9bcd9c652D72861692e48C162166;
        // targets[23] = 0xFB1519782165F58974e519C5574AD0FbdFf0f847;
        // targets[24] = 0xD331010e5df71DbA03De892cd3C14E436111aCAD;
        // targets[25] = 0x1a77842DB300E6804a360bE7463c571a6feBC806;
        // targets[26] = 0x0148063fbec76D41F1bA19Ec2efc2C0111452C9c;
        // targets[27] = 0x854b0faF9C3f8285c5855f9138619F879E53CA8B;
        // targets[28] = 0xdeFe69D19884d69e2D3bCE86696764736BE97657;
        // targets[29] = 0x6fb9bAf844dfc39023Ef30C1BAeda239C35000F7;
        // targets[30] = 0xd1c04db9bba40d59b397b2c1a050247fbbc49b68;
        // targets[31] = 0xcc77aa5e5599af505d339db0a0684a813b182cb9;
        // targets[32] = 0x11bdd0a3a481268dd9fa0ab6506bf7774972d7b9;
        // targets[33] = 0x4f19f84c022743c4efe10bca5b129147032e9bb3;
        // targets[34] = 0xd03f427b6211cf0fedf8dd2ee7658c4090c9cf67;
        // targets[35] = 0xe715c633289e2edf6d14376d9b1f8b9b0e96d68c;
        // targets[36] = 0x3609a560e9edc0530e815aba56732da436858e11;
        // targets[37] = 0x1c196d4f046efc444554c540c56cc2e6ee45d691;
        // targets[38] = 0x20074705094166207340d059da119a696c49bdad;
        // targets[39] = 0x31c79fc17c5528a6f81c51033a4a36a8e288f36a;
        // targets[40] = 0x9452e7b67c4c43e4efb80fb219748a31dbb6b553;
        // targets[41] = 0x72c6a0c5040c6eaa7828dd8b8613e07552b3d59b;
        // targets[42] = 0xd51367d70aeaf2447e5df1a7922a0ed3105f0d04;
        // targets[43] = 0xde731fb8bcb00955fa1b658210485c487547885e;
        // targets[44] = 0xcf3f7a5e0140d1d7c263f24d2c2d757102912c33;
        // targets[45] = 0x6471256e9fdb6c68caa8ae62c01b51b9e1a46bc9;
        // targets[46] = 0x8c7423b3db24a2c679a9f317550b3e793a10197d;
        // targets[47] = 0xde7ad7a2f133895624e7602517dd4b4b139d7bb9;
        // targets[48] = 0x4dcda6a15783b5e302349d738030079b6342e54a;
        // targets[49] = 0x48c3f03f77668da8c76486d5fcaab43c81ada32e;
        
        return targets;
    }
} 
require('@truffle/hdwallet-provider');
require('dotenv').config();

const HDWalletProvider = require('@truffle/hdwallet-provider'); // Esta línea debe estar presente

const { MNEMONIC, PROJECT_ID } = process.env;

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*",
    },
    sepolia: {
      provider: () => new HDWalletProvider(MNEMONIC, `https://sepolia.infura.io/v3/${PROJECT_ID}`),
      network_id: 11155111, // ID de la red Sepolia
      confirmations: 2,
      timeoutBlocks: 200,
      skipDryRun: true
    }
  },
  compilers: {
    solc: {
      version: "0.8.0",
    }
  }
};

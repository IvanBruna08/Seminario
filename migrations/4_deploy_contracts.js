// 2_deploy_pallet_registry.js
const PalletRegistry = artifacts.require("PalletRegistry");

module.exports = function (deployer) {
  deployer.deploy(PalletRegistry);
};

// 2_deploy_pallet_registry.js
const Transporte = artifacts.require("Transporte");

module.exports = function (deployer) {
  deployer.deploy(Transporte);
};

// 2_deploy_pallet_registry.js
const Distribuidor = artifacts.require("Distribuidor");

module.exports = function (deployer) {
  deployer.deploy(Distribuidor);
};
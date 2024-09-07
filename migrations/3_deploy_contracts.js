const TransportContract = artifacts.require("TransportContract");
const Cosecha = artifacts.require("Cosecha");

module.exports = async function (deployer) {
  // Despliega el contrato TransportContract y pasa la dirección del contrato Cosecha
  const cosechaInstance = await Cosecha.deployed(); // Obtén la instancia del contrato Cosecha desplegado

  await deployer.deploy(TransportContract, cosechaInstance.address);
}
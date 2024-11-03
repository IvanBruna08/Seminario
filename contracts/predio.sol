// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SupplyChain {
    struct Pallet {
        uint256 idPallet;
        uint256 idPredio;
        string producto;
        uint256 fecha;
        uint256 peso;
        bool existe;
    }

    struct DistribuidorPallet {
        uint256 idDistribuidorPallet;
        uint256 idPallet;
        uint256 idDistribuidor;
        uint256 pesoEnviado;
    }

    mapping(uint256 => Pallet) public pallets;
    mapping(uint256 => DistribuidorPallet) public distribuidorPallets;

    uint256 public palletCount;
    uint256 public distribuidorPalletCount;

    event PalletCreado(uint256 indexed idPallet, uint256 idPredio, string producto, uint256 fecha, uint256 peso);
    event DistribuidorAsignado(uint256 indexed idDistribuidorPallet, uint256 idPallet, uint256 idDistribuidor, uint256 pesoEnviado);

    // Función para crear un nuevo pallet
    function crearPallet(
        uint256 _idPredio,
        string memory _producto,
        uint256 _fecha,
        uint256 _peso
    ) public {
        palletCount++;
        pallets[palletCount] = Pallet(palletCount, _idPredio, _producto, _fecha, _peso, true);
        emit PalletCreado(palletCount, _idPredio, _producto, _fecha, _peso);
    }

    // Función para asignar un distribuidor a un pallet
    function asignarDistribuidor(uint256 _idDistribuidor, uint256 _idPallet, uint256 _pesoEnviado) public {
        distribuidorPalletCount++;
        distribuidorPallets[distribuidorPalletCount] = DistribuidorPallet(distribuidorPalletCount, _idPallet, _idDistribuidor, _pesoEnviado);
        emit DistribuidorAsignado(distribuidorPalletCount, _idPallet, _idDistribuidor, _pesoEnviado);
    }

    // Función para añadir o actualizar el peso enviado por un distribuidor
    function agregarDistribuidor(uint256 _idDistribuidorPallet, uint256 _pesoEnviado) public {
        distribuidorPallets[_idDistribuidorPallet].pesoEnviado = _pesoEnviado;
        emit DistribuidorAsignado(_idDistribuidorPallet, distribuidorPallets[_idDistribuidorPallet].idPallet, distribuidorPallets[_idDistribuidorPallet].idDistribuidor, _pesoEnviado);
    }

    // Función para actualizar los detalles de un pallet
    function actualizarPallet(
        uint256 _idPallet,
        string memory _producto,
        uint256 _fecha,
        uint256 _peso
    ) public {
        pallets[_idPallet].producto = _producto;
        pallets[_idPallet].fecha = _fecha;
        pallets[_idPallet].peso = _peso;
    }

    // Función para eliminar la asignación de un distribuidor a un pallet
    function eliminarDistribuidorPallet(uint256 _idDistribuidorPallet) public {
        delete distribuidorPallets[_idDistribuidorPallet];
    }
}

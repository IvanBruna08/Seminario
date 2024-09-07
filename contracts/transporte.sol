// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

import "./cosecha.sol";  // Importa el contrato de cosecha para acceder a sus datos

contract TransportContract {
    enum TransportStatus { EnCamino, Entregado, Retrasado } // Enum para los posibles estados

    struct Transport {
        uint256 id; // ID automático
        string date;
        string destination;
        string carrier;
        TransportStatus status; // Cambiado a enum para estados
        Cosecha.CosechaData harvestInfo;
    }

    Cosecha cosechaContract; // Instancia del contrato de cosecha para acceder a sus datos
    mapping(uint256 => Transport) public transports;  // Mapeo para almacenar transportes por ID
    uint256 public nextTransportId; // Contador para el ID automático

    // Constructor que establece la dirección del contrato de cosecha
    constructor(address _cosechaContractAddress) {
        cosechaContract = Cosecha(_cosechaContractAddress);
    }

    // Función para registrar un nuevo transporte usando el ID de la cosecha
    function registerTransport(
        uint256 _harvestId, // Cambiado a _harvestId para mayor claridad
        string memory _date, 
        string memory _destination, 
        string memory _carrier
    ) public {
        // Obtener los detalles de la cosecha desde el contrato de cosecha usando el ID de la cosecha
        Cosecha.CosechaData memory harvestDetails = cosechaContract.obtenerCosecha(_harvestId);

        // Registrar el transporte junto con los detalles de la cosecha
        transports[nextTransportId] = Transport(nextTransportId, _date, _destination, _carrier, TransportStatus.EnCamino, harvestDetails);
        nextTransportId++; // Incrementar el ID para el próximo transporte
    }

    // Función para actualizar el estado del transporte
    function actualizarEstadoTransporte(uint256 _id, TransportStatus _nuevoEstado) public {
        // Asegúrate de que solo los transportistas o entidades autorizadas puedan hacer esto
        Transport storage transporte = transports[_id];
        transporte.status = _nuevoEstado;
    }

    // Función para obtener los detalles de un transporte por ID
    function getTransportDetails(uint256 _id) public view returns (Transport memory) {
        return transports[_id];
    }
}


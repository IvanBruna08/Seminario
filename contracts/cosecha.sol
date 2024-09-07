// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

contract Cosecha {
    uint256 public cosechaCounter;
    mapping(uint256 => CosechaData) public cosechas;

    struct CosechaData {
        uint256 id;
        string producto;
        string fechaCosecha;
        string ubicacion;
        uint256 cantidadLote; // Cantidad del lote en unidades o peso
        uint256 cantidadAgua; // Cantidad de agua utilizada en litros
        string pesticidasFertilizantes; // Detalles sobre pesticidas y fertilizantes
        string practicasCultivo; // Prácticas agrícolas sostenibles
        bool transportado; // Para marcar si la cosecha ya ha sido transportada
    }

    // Evento para marcar una cosecha como transportada
    event TransportadoMarcado(uint256 id);

    function registrarCosecha(
        string memory _producto,
        string memory _fechaCosecha,
        string memory _ubicacion,
        uint256 _cantidadLote,
        uint256 _cantidadAgua,
        string memory _pesticidasFertilizantes,
        string memory _practicasCultivo
    ) public returns (uint256) {
        cosechaCounter++;
        cosechas[cosechaCounter] = CosechaData(
            cosechaCounter,
            _producto,
            _fechaCosecha,
            _ubicacion,
            _cantidadLote,
            _cantidadAgua,
            _pesticidasFertilizantes,
            _practicasCultivo,
            false
        );
        return cosechaCounter; // Devuelve el ID de la nueva cosecha
    }

    function marcarTransportado(uint256 _idCosecha) external {
        cosechas[_idCosecha].transportado = true;
        emit TransportadoMarcado(_idCosecha); // Emitir el evento
    }

    function obtenerCosecha(uint256 _id) public view returns (CosechaData memory) {
        return cosechas[_id];
    }
}

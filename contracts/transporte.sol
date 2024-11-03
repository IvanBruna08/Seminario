// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Transporte {
    // Estructura para el envío de cajas
    struct EnvioCaja {
        uint envioCajaId;         // ID del envío de la caja
        uint cajaId;              // ID de la caja
        string coordenadasTransporte; // Coordenadas de transporte en formato JSON
        uint fechaInicio;         // Fecha de inicio
        uint fechaLlegada;        // Fecha de llegada
        bool entregado;           // Estado de entrega
    }

    // Estructura para el envío de pallets
    struct EnvioPallet {
        uint envioPalletId;      // ID del envío de pallet
        uint palletId;            // ID del pallet
        string coordenadasTransporte; // Coordenadas de transporte en formato JSON
        uint fechaInicio;         // Fecha de inicio
        uint fechaLlegada;        // Fecha de llegada
    }

    // Mapeo para almacenar los envíos de cajas
    mapping(uint => EnvioCaja) public enviosCajas;
    // Mapeo para almacenar los envíos de pallets
    mapping(uint => EnvioPallet) public enviosPallets;

    // Eventos
    event EntregaIniciadaCaja(
        uint indexed envioCajaId,
        uint indexed cajaId,
        uint fechaInicio,
        string coordenadasTransporte
    );

    event EntregaFinalizadaCaja(
        uint indexed envioCajaId,
        uint fechaLlegada,
        string coordenadasTransporte
    );

    event EntregaIniciadaPallet(
        uint indexed envioPalletId,
        uint indexed palletId,
        uint fechaInicio,
        string coordenadasTransporte
    );

    event EntregaFinalizadaPallet(
        uint indexed envioPalletId,
        uint fechaLlegada,
        string coordenadasTransporte
    );

    // Función para iniciar la entrega de una caja
    function iniciarEntregaCaja(
        uint envioCajaId,
        uint cajaId,
        string memory coordenadasTransporte
    ) public {
        // Registrar la entrega en el mapeo
        enviosCajas[envioCajaId] = EnvioCaja({
            envioCajaId: envioCajaId,
            cajaId: cajaId,
            coordenadasTransporte: coordenadasTransporte,
            fechaInicio: block.timestamp,
            fechaLlegada: 0,
            entregado: false
        });

        // Emitir el evento
        emit EntregaIniciadaCaja(envioCajaId, cajaId, block.timestamp, coordenadasTransporte);
    }

    // Función para finalizar la entrega de una caja
    function finalizarEntregaCaja(
        uint envioCajaId,
        string memory coordenadasTransporte
    ) public {
        // Verificar que la entrega esté registrada
        require(enviosCajas[envioCajaId].cajaId != 0, "Entrega no iniciada.");
        require(!enviosCajas[envioCajaId].entregado, "La caja ya ha sido entregada.");

        // Actualizar datos de entrega
        enviosCajas[envioCajaId].fechaLlegada = block.timestamp;
        enviosCajas[envioCajaId].coordenadasTransporte = coordenadasTransporte; // Guardar coordenadas finales
        enviosCajas[envioCajaId].entregado = true;

        // Emitir el evento
        emit EntregaFinalizadaCaja(envioCajaId, block.timestamp, coordenadasTransporte);
    }

    // Función para iniciar la entrega de un pallet
    function iniciarEntregaPallet(
        uint envioPalletId,
        uint palletId,
        string memory coordenadasTransporte
    ) public {
        // Registrar la entrega en el mapeo
        enviosPallets[envioPalletId] = EnvioPallet({
            envioPalletId: envioPalletId,
            palletId: palletId,
            coordenadasTransporte: coordenadasTransporte,
            fechaInicio: block.timestamp,
            fechaLlegada: 0
        });

        // Emitir el evento
        emit EntregaIniciadaPallet(envioPalletId, palletId, block.timestamp, coordenadasTransporte);
    }

    // Función para finalizar la entrega de un pallet
    function finalizarEntregaPallet(
        uint envioPalletId,
        string memory coordenadasTransporte
    ) public {
        // Verificar que la entrega esté registrada
        require(enviosPallets[envioPalletId].palletId != 0, "Entrega no iniciada.");

        // Actualizar datos de entrega
        enviosPallets[envioPalletId].fechaLlegada = block.timestamp;
        enviosPallets[envioPalletId].coordenadasTransporte = coordenadasTransporte; // Guardar coordenadas finales

        // Emitir el evento
        emit EntregaFinalizadaPallet(envioPalletId, block.timestamp, coordenadasTransporte);
    }
}


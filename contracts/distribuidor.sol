// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Distribuidor {
    // Estructura para la recepción de un pallet
    struct RecepcionPallet {
        uint envioPalletId;     // ID del envío de pallet
        uint distribuidorId;     // ID del distribuidor
        uint fechaRecepcion;     // Fecha de recepción
        bool recibido;           // Estado de recepción
    }

    // Estructura para la caja
    struct Caja {
        uint recepcionId;        // ID de la recepción a la que pertenece
        uint clienteId;          // ID del cliente (opcional)
        uint fechaCreacion;      // Fecha de creación de la caja
    }

    // Mapeo para almacenar las recepciones de pallets
    mapping(uint => RecepcionPallet) public recepcionesPallets;

    // Mapeo para almacenar las cajas creadas
    mapping(uint => Caja) public cajas;

    // Contador para las cajas creadas
    uint public contadorCajas;

    // Eventos
    event PalletRecibido(
        uint indexed envioPalletId,
        uint indexed distribuidorId,
        uint fechaRecepcion
    );

    event CajaCreada(
        uint indexed cajaId,
        uint indexed recepcionId,
        uint clienteId,
        uint fechaCreacion
    );

    event ClienteAsignado(
        uint indexed cajaId,
        uint indexed clienteId
    );

    // Función para marcar la recepción de un pallet
    function marcarRecepcionPallet(
        uint envioPalletId,
        uint distribuidorId
    ) public {
        require(recepcionesPallets[envioPalletId].envioPalletId == 0 || !recepcionesPallets[envioPalletId].recibido, "Pallet ya recibido.");

        recepcionesPallets[envioPalletId] = RecepcionPallet({
            envioPalletId: envioPalletId,
            distribuidorId: distribuidorId,
            fechaRecepcion: block.timestamp,
            recibido: true
        });

        emit PalletRecibido(envioPalletId, distribuidorId, block.timestamp);
    }

    // Función para crear una caja
    function crearCaja(uint recepcionId) public {
        contadorCajas++;
        
        cajas[contadorCajas] = Caja({
            recepcionId: recepcionId,
            clienteId: 0, // Por defecto, no hay cliente asignado
            fechaCreacion: block.timestamp
        });

        emit CajaCreada(contadorCajas, recepcionId, 0, block.timestamp);
    }

    // Función para asignar un cliente a una caja
    function asignarCliente(uint cajaId, uint clienteId) public {
        require(cajas[cajaId].recepcionId != 0, "La caja no existe.");
        
        cajas[cajaId].clienteId = clienteId; // Asignar el cliente a la caja
        
        emit ClienteAsignado(cajaId, clienteId);
    }
}

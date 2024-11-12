// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Distribuidor {
    struct Recepcion {
        uint256 idRecepcion;         
        uint256 idEnvioPallet;      
        uint256 pesoEnvio;           
    }

    struct Caja {
        uint256 idCaja;              
        uint256 idRecepcion;         
        uint256 idCliente;           
        uint256 tipocaja;           
    }

    struct RecepcionCliente {
        uint256 idRecepcionCliente;  
        uint256 idCaja;              
        uint256 fecha;               
        int256 Latitude;             
        int256 Longitude;            
    }

    mapping(uint256 => Recepcion) public recepciones;  
    mapping(uint256 => Caja) public cajas;             
    mapping(uint256 => RecepcionCliente) public recepcionClientes;   
    uint256 public recepcionCount;    
    uint256 public cajaCount;         
    uint256 public recepcionClienteCount;  

    event RecepcionRegistered(uint256 idRecepcion, uint256 idEnvioPallet, uint256 pesoEnvio);
    event CajaRegistered(uint256 idCaja, uint256 idRecepcion, uint256 tipocaja);
    event ClienteAsignado(uint256 idCaja, uint256 idCliente);
    event RecepcionClienteRegistered(uint256 idRecepcionCliente, uint256 idCaja, uint256 fecha, int256 Latitude, int256 Longitude);

    // Función para registrar una nueva recepción
    function registerRecepcion(
        uint256 _idRecepcion,
        uint256 _idEnvioPallet,
        uint256 _pesoEnvio
    ) public {
        require(recepciones[_idRecepcion].idRecepcion == 0, "Recepcion ya registrada");

        // Crear y almacenar la nueva recepción
        recepciones[_idRecepcion] = Recepcion({
            idRecepcion: _idRecepcion,
            idEnvioPallet: _idEnvioPallet,
            pesoEnvio: _pesoEnvio
        });

        recepcionCount++;

        // Emitir el evento de registro
        emit RecepcionRegistered(_idRecepcion, _idEnvioPallet, _pesoEnvio);
    }

    // Función para registrar una nueva caja en una recepción específica
    function registerCaja(
        uint256 _idCaja,
        uint256 _idRecepcion,
        uint256 _tipocaja
    ) public {
        require(cajas[_idCaja].idCaja == 0, "Caja ya registrada");
        require(recepciones[_idRecepcion].idRecepcion != 0, "Recepcion no encontrada");

        // Crear y almacenar la nueva caja
        cajas[_idCaja] = Caja({
            idCaja: _idCaja,
            idRecepcion: _idRecepcion,
            idCliente: 0,   // Inicia sin cliente asignado
            tipocaja: _tipocaja
        });

        cajaCount++;

        // Emitir el evento de registro
        
        emit CajaRegistered(_idCaja, _idRecepcion, _tipocaja);
    }

    // Función para asignar un cliente a una caja específica
    function asignarClienteACaja(uint256 _idCaja, uint256 _idCliente) public {
        require(cajas[_idCaja].idCaja != 0, "Caja no encontrada");
        require(cajas[_idCaja].idCliente == 0, "Cliente ya asignado a esta caja");

        // Asignar el cliente a la caja
        cajas[_idCaja].idCliente = _idCliente;

        // Emitir el evento de asignación de cliente
        emit ClienteAsignado(_idCaja, _idCliente);
    }

    // Función para registrar la recepción de una caja por parte de un cliente
    function registerRecepcionCliente(
        uint256 _idRecepcionCliente,
        uint256 _idCaja,
        uint256 _fecha,
        int256 _Latitude,
        int256 _Longitude
    ) public {
        require(cajas[_idCaja].idCaja != 0, "Caja no encontrada");


        // Crear y almacenar la nueva recepción de cliente
        recepcionClientes[_idRecepcionCliente] = RecepcionCliente({
            idRecepcionCliente: _idRecepcionCliente,
            idCaja: _idCaja,
            fecha: _fecha,
            Latitude: _Latitude,
            Longitude: _Longitude
        });

        recepcionClienteCount++;

        // Emitir el evento de registro
        emit RecepcionClienteRegistered(_idRecepcionCliente, _idCaja, _fecha, _Latitude, _Longitude);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Transporte {

    struct EnvioPallet {
        uint256 palletId;
        uint256 transporteId;
        uint256 vehiculoId;
        uint256 fechaInicio;
        uint256 fechaLlegada;
        int256 rutaInicioLatitude;   
        int256 rutaInicioLongitude;
        int256 rutaFinalLatitude;
        int256 rutaFinalLongitude;
    }

    struct EnvioCaja {
        uint256 cajaId;
        uint256 transporteId;
        uint256 vehiculoId;
        uint256 fechaInicio;
        uint256 fechaLlegada;
        int256 rutaInicioLatitude;   
        int256 rutaInicioLongitude;
        int256 rutaFinalLatitude;
        int256 rutaFinalLongitude;
    }

    mapping(uint256 => EnvioPallet) public enviosPallet;
    mapping(uint256 => EnvioCaja) public enviosCaja;

    // Función pública para iniciar el envío de un pallet
    function iniciarEnvioPallet(
        uint256 palletId,
        uint256 transporteId,
        uint256 vehiculoId,
        int256 rutaInicioLatitude,
        int256 rutaInicioLongitude
    ) public {
        require(enviosPallet[palletId].fechaInicio == 0, "El envio del pallet ya ha sido iniciado");

        enviosPallet[palletId] = EnvioPallet({
            palletId: palletId,
            transporteId: transporteId,
            vehiculoId: vehiculoId,
            fechaInicio: block.timestamp,
            fechaLlegada: 0,
            rutaInicioLatitude: rutaInicioLatitude,
            rutaInicioLongitude: rutaInicioLongitude,
            rutaFinalLatitude: 0,
            rutaFinalLongitude: 0
        });
    }

    // Función pública para finalizar el envío de un pallet
    function finalizarEnvioPallet(
        uint256 palletId,
        int256 rutaFinalLatitude,
        int256 rutaFinalLongitude
    ) public {
        require(enviosPallet[palletId].fechaInicio != 0, "El envio del pallet no ha sido iniciado");
        require(enviosPallet[palletId].fechaLlegada == 0, "El envio del pallet ya ha sido finalizado");

        EnvioPallet storage envio = enviosPallet[palletId];
        envio.fechaLlegada = block.timestamp;
        envio.rutaFinalLatitude = rutaFinalLatitude;
        envio.rutaFinalLongitude = rutaFinalLongitude;
    }

    // Función pública para iniciar el envío de una caja
    function iniciarEnvioCaja(
        uint256 cajaId,
        uint256 transporteId,
        uint256 vehiculoId,
        int256 rutaInicioLatitude,
        int256 rutaInicioLongitude
    ) public {
        require(enviosCaja[cajaId].fechaInicio == 0, "El envio de la caja ya ha sido iniciado");

        enviosCaja[cajaId] = EnvioCaja({
            cajaId: cajaId,
            transporteId: transporteId,
            vehiculoId: vehiculoId,
            fechaInicio: block.timestamp,
            fechaLlegada: 0,
            rutaInicioLatitude: rutaInicioLatitude,
            rutaInicioLongitude: rutaInicioLongitude,
            rutaFinalLatitude: 0,
            rutaFinalLongitude: 0
        });
    }

    // Función pública para finalizar el envío de una caja
    function finalizarEnvioCaja(
        uint256 cajaId,
        int256 rutaFinalLatitude,
        int256 rutaFinalLongitude
    ) public {
        require(enviosCaja[cajaId].fechaInicio != 0, "El envio de la caja no ha sido iniciado");
        require(enviosCaja[cajaId].fechaLlegada == 0, "El envio de la caja ya ha sido finalizado");

        EnvioCaja storage envio = enviosCaja[cajaId];
        envio.fechaLlegada = block.timestamp;
        envio.rutaFinalLatitude = rutaFinalLatitude;
        envio.rutaFinalLongitude = rutaFinalLongitude;
    }
}

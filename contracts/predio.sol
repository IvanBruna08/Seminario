// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PalletRegistry {
    struct Pallet {
        uint256 idPallet;         
        uint256 idPredio;         
        string producto;          
        uint256 fechaCosecha;     
        uint256 pesoPallet;       
    }

    struct DistribuidorPallet {
        uint256 idDistribuidorPallet;  
        uint256 idPallet;              
        uint256 idDistribuidor;        
        uint256 pesoEnvio;             
    }

    mapping(uint256 => Pallet) public pallets;  
    mapping(uint256 => DistribuidorPallet[]) public distribuidorPallets;  
    uint256 public palletCount;                  
    
    event PalletRegistered(
        uint256 idPallet,
        uint256 idPredio,
        string producto,
        uint256 fechaCosecha,
        uint256 pesoPallet
    );

    event DistribuidorPalletRegistered(
        uint256 idDistribuidorPallet,
        uint256 idPallet,
        uint256 idDistribuidor,
        uint256 pesoEnvio
    );

    event PalletUpdated(uint256 idPallet);
    event DistribuidorPalletUpdated(uint256 idDistribuidorPallet);

    // Función para registrar un nuevo pallet
    function registerPallet(
        uint256 _idPallet,
        uint256 _idPredio,
        string memory _producto,
        uint256 _fechaCosecha,
        uint256 _pesoPallet
    ) public {
        // Asegurarse de que el pallet no se haya registrado previamente
        require(pallets[_idPallet].idPallet == 0, "Pallet ya registrado");

        // Crear y almacenar el nuevo pallet
        pallets[_idPallet] = Pallet({
            idPallet: _idPallet,
            idPredio: _idPredio,
            producto: _producto,
            fechaCosecha: _fechaCosecha,
            pesoPallet: _pesoPallet
        });

        palletCount++;

        // Emitir el evento de registro
        emit PalletRegistered(_idPallet, _idPredio, _producto, _fechaCosecha, _pesoPallet);
    }

    // Función para obtener la información de un pallet
    function getPallet(uint256 _idPallet) public view returns (Pallet memory) {
        return pallets[_idPallet];
    }

    // Función para registrar un nuevo DistribuidorPallet asociado a un pallet específico
    function registerDistribuidorPallet(
        uint256 _idDistribuidorPallet,
        uint256 _idPallet,
        uint256 _idDistribuidor,
        uint256 _pesoEnvio
    ) public {
        // Validar que el pallet existe antes de registrar un DistribuidorPallet
        require(pallets[_idPallet].idPallet != 0, "Pallet no encontrado");

        // Asegurarse de que el ID de DistribuidorPallet no esté en uso
        for (uint256 i = 0; i < distribuidorPallets[_idPallet].length; i++) {
            require(distribuidorPallets[_idPallet][i].idDistribuidorPallet != _idDistribuidorPallet, "ID de DistribuidorPallet ya existe");
        }

        // Crear y almacenar el nuevo DistribuidorPallet con el ID proporcionado
        distribuidorPallets[_idPallet].push(DistribuidorPallet({
            idDistribuidorPallet: _idDistribuidorPallet,
            idPallet: _idPallet,
            idDistribuidor: _idDistribuidor,
            pesoEnvio: _pesoEnvio
        }));

        // Emitir el evento de registro de DistribuidorPallet
        emit DistribuidorPalletRegistered(_idDistribuidorPallet, _idPallet, _idDistribuidor, _pesoEnvio);
    }

    // Función para actualizar un pallet existente
    function updatePallet(
        uint256 _idPallet,
        uint256 _idPredio,
        string memory _producto,
        uint256 _fechaCosecha,
        uint256 _pesoPallet
    ) public {
        // Validar que el pallet existe
        require(pallets[_idPallet].idPallet != 0, "Pallet no encontrado.");

        // Actualizar los datos del pallet
        pallets[_idPallet] = Pallet({
            idPallet: _idPallet,
            idPredio: _idPredio,
            producto: _producto,
            fechaCosecha: _fechaCosecha,
            pesoPallet: _pesoPallet
        });

        // Emitir el evento de actualización
        emit PalletUpdated(_idPallet);
    }

    // Función para actualizar un DistribuidorPallet existente
    function updateDistribuidorPallet(
        uint256 _idDistribuidorPallet,
        uint256 _idPallet,
        uint256 _idDistribuidor,
        uint256 _pesoEnvio
    ) public {
        // Validar que el DistribuidorPallet existe en la lista del pallet
        bool found = false;
        for (uint256 i = 0; i < distribuidorPallets[_idPallet].length; i++) {
            if (distribuidorPallets[_idPallet][i].idDistribuidorPallet == _idDistribuidorPallet) {
                // Asegurarse de que el distribuidor es el correcto
                require(distribuidorPallets[_idPallet][i].idDistribuidor == _idDistribuidor, "Distribuidor incorrecto para este pallet.");

                // Actualizar el peso de envío
                distribuidorPallets[_idPallet][i].pesoEnvio = _pesoEnvio;
                found = true;

                // Emitir el evento de actualización
                emit DistribuidorPalletUpdated(_idDistribuidorPallet);
                break;
            }
        }

        require(found, "DistribuidorPallet no encontrado.");
    }

    // Función para obtener todos los DistribuidorPallets asociados a un pallet
    function getDistribuidorPalletsByPallet(uint256 _idPallet) public view returns (DistribuidorPallet[] memory) {
        return distribuidorPallets[_idPallet];
    }

        event DistribuidorPalletEliminado(uint256 idDistribuidorPallet, uint256 idPallet);

    // Función para eliminar un DistribuidorPallet por idDistribuidorPallet y idPallet
    function eliminarDistribuidorPallet(uint256 _idPallet, uint256 _idDistribuidorPallet) public {
        // Encontrar el índice del distribuidor a eliminar
        bool found = false;
        uint256 index;

        for (uint256 i = 0; i < distribuidorPallets[_idPallet].length; i++) {
            if (distribuidorPallets[_idPallet][i].idDistribuidorPallet == _idDistribuidorPallet) {
                index = i;
                found = true;
                break;
            }
        }

        require(found, "DistribuidorPallet no encontrado.");

        // Intercambiar el elemento a eliminar con el último y luego hacer pop
        uint256 lastIndex = distribuidorPallets[_idPallet].length - 1;

        if (index != lastIndex) {
            distribuidorPallets[_idPallet][index] = distribuidorPallets[_idPallet][lastIndex];
        }
        
        distribuidorPallets[_idPallet].pop();

        // Emitir evento de eliminación
        emit DistribuidorPalletEliminado(_idDistribuidorPallet, _idPallet);
    }
}

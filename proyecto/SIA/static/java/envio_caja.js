// Función para manejar errores de geolocalización
function errorGeoLocation(error) {
    switch (error.code) {
        case error.PERMISSION_DENIED:
            alert("El usuario denegó la solicitud de geolocalización.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("La ubicación no está disponible.");
            break;
        case error.TIMEOUT:
            alert("La solicitud de geolocalización ha caducado.");
            break;
        case error.UNKNOWN_ERROR:
            alert("Se ha producido un error desconocido.");
            break;
    }
}

// Variable para almacenar las coordenadas de transporte
let coordenadasTransporte = [];
let transporteMarker = null;
let idcaja = null;
let enviocaja_id = null;

// Función para manejar el inicio de entrega y almacenar coordenadas iniciales
function iniciarEntrega() {
    const vehiculoId = $('#vehicleSelect').val();
    if (!vehiculoId) {
        alert('Por favor, selecciona un vehículo antes de iniciar la entrega.');
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const latitudTransporte = position.coords.latitude;
            const longitudTransporte = position.coords.longitude;

            // Enviar las coordenadas iniciales al servidor
            $.ajax({
                type: "POST",
                url: $('#startDeliveryForm').attr('action'),
                data: {
                    ruta_inicio_latitude: latitudTransporte,
                    ruta_inicio_longitude: longitudTransporte,
                    vehiculo_id: vehiculoId,
                    id_caja: $('#id_caja').val(),
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('Coordenadas iniciales enviadas:', response);
                    if (response.success) {
                        idCaja = response.caja_id;
                        enviocaja_id = response.enviocaja_id;
                        console.log(idCaja)
                        console.log(enviocaja_id)
                        document.getElementById('startDelivery').disabled = true;
                        // Acceder a los valores almacenados en localStorage para el log
                        // Inicia el seguimiento de ubicación
                        iniciarSeguimientoDeCoordenadas();
                    }
                }
            });
        }, errorGeoLocation);
    } else {
        alert('Geolocalización no soportada.');
    }
}

// Función para iniciar el seguimiento de coordenadas
function iniciarSeguimientoDeCoordenadas() {
    navigator.geolocation.watchPosition(function(position) {
        const latitud = position.coords.latitude;
        const longitud = position.coords.longitude;
        const tiempoActual = new Date().toISOString();

        // Actualiza el marcador y el mapa
        if (!transporteMarker) {
            transporteMarker = new mapboxgl.Marker({ color: 'blue' })
                .setLngLat([longitud, latitud])
                .setPopup(new mapboxgl.Popup().setText('Transporte'))
                .addTo(map);
        } else {
            transporteMarker.setLngLat([longitud, latitud]);
        }

        map.setCenter([longitud, latitud]);

        // Enviar la nueva coordenada al servidor
        $.ajax({
            type: "POST",
            url: '/actualizar-coordenadas-caja/',  // URL de la vista
            contentType: "application/json",
            data: JSON.stringify({
                enviocaja_id: enviocaja_id,  // Se usa idPallet como identificador del envío
                latitud: latitud,
                longitud: longitud,
                tiempo: tiempoActual
            }),
            success: function(response) {
                console.log('Coordenada enviada:', response);
            },
            error: function(error) {
                console.error('Error al enviar coordenada:', error);
            }
        });
    }, errorGeoLocation);
}


// Función para finalizar la entrega y enviar coordenadas adicionales
function finalizarEntrega() {
    console.log("Función finalizarEntrega llamada");

    // Acceder a los valores almacenados en localStorage para el log
    const idcaja = document.getElementById('id_caja').value;
    const enviocaja_id = document.getElementById('enviocaja_id').value;

    if (!idcaja || !enviocaja_id) {
        console.error('No se ha iniciado la entrega o falta algún identificador');
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const latitudFinal = position.coords.latitude;
            const longitudFinal = position.coords.longitude;
            const tiempoActual = new Date().toISOString(); 
            console.log("Datos a enviar:", {
                enviocaja_id: enviocaja_id,
                ruta_final_latitude: latitudFinal,
                ruta_final_longitude: longitudFinal,
                tiempo: tiempoActual,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            });
            // Enviar el formulario usando AJAX
            $.ajax({
                type: 'POST',
                url: $('#endDeliveryForm').attr('action'),
                data: {
                    enviocaja_id: enviocaja_id,
                    ruta_final_latitude: latitudFinal,
                    ruta_final_longitude: longitudFinal,
                    tiempo: tiempoActual,
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log("Formulario enviado con éxito");
                    enviarARecepcionCliente(); // Llama a esta función después del envío
                },
                error: function(xhr, status, error) {
                    console.error("Error enviando el formulario:", error);
                }
            });

        }, errorGeoLocation);
    } else {
        alert('Geolocalización no soportada.');
    }
}
// Asignar los eventos a los botones
document.getElementById('startDelivery').addEventListener('click', iniciarEntrega);
// Asignar los eventos a los botones
document.getElementById('endDelivery').addEventListener('click', finalizarEntrega);

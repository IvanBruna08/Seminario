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

// Variable para almacenar el ID de pallet y coordenadas de transporte
let idPallet = null;
let envio_id = null;
let transporteMarker = null;

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
                    id_pallet: $('#id_pallet').val(),
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('Coordenadas iniciales enviadas:', response);
                    if (response.success) {
                        idPallet = response.pallet_id;
                        envio_id= response.envio_id
                        document.getElementById('startDelivery').disabled = true;

                        // Inicia el seguimiento de ubicación
                        console.log("antes de llamar finalizar:",idPallet)
                        iniciarSeguimientoDeCoordenadas();
                    }
                }
            });
        }, errorGeoLocation);
    } else {
        alert('Geolocalización no soportada.');
    }
}

function iniciarSeguimientoDeCoordenadas() {
    navigator.geolocation.watchPosition(function(position) {
        const latitud = position.coords.latitude;
        const longitud = position.coords.longitude;
        const tiempoActual = new Date().toISOString();
        console.log("en iniciar seguimiento:",idPallet)
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
            url: '/actualizar-coordenadas/',  // URL de la vista
            contentType: "application/json",
            data: JSON.stringify({
                envio_id: envio_id,  // Se usa idPallet como identificador del envío
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
// Función para finalizar la entrega y obtener todas las coordenadas almacenadas en el servidor
function finalizarEntrega() {
    console.log("Función finalizarEntrega llamada");

    const idPallet = document.getElementById('id_pallet').value;
    const envio_id = document.getElementById('envio_id').value;

    if (!idPallet) {
        console.error('No se ha iniciado la entrega o falta el identificador del pallet');
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const latitudFinal = position.coords.latitude;
            const longitudFinal = position.coords.longitude;
            const tiempoActual = new Date().toISOString(); 

            console.log("Latitud:", latitudFinal, "Longitud:", longitudFinal);

            // Verificar si las coordenadas están disponibles antes de enviar
            if (!latitudFinal || !longitudFinal) {
                console.error('Las coordenadas de geolocalización no están disponibles.');
                return;
            }
                        // Asignar coordenadas a campos ocultos
            $('#ruta_final_latitude').val(latitudFinal);
            $('#ruta_final_longitude').val(longitudFinal);

            // Enviar coordenadas finales mediante AJAX
            $.ajax({
                type: "POST",
                url: $('#endDeliveryForm').attr('action'),
                data: {
                    envio_id: envio_id,
                    ruta_final_latitude: latitudFinal,
                    ruta_final_longitude: longitudFinal,
                    tiempo: tiempoActual,
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        console.log('Entrega finalizada exitosamente:', response.message);
                        window.location.href = '/login';  // Cambia esta URL si es necesario
                    } else {
                        console.error('Error:', response.message);
                    }
                },
                error: function(error) {
                    console.error('Error al finalizar entrega:', error);
                }
            });
        }, function(error) {
            console.error('Error de geolocalización:', error);
        });
    } else {
        alert('Geolocalización no soportada.');
    }
}


// Asignar el evento al botón de inicio de entrega
document.getElementById('startDelivery').addEventListener('click', iniciarEntrega);
document.getElementById('endDelivery').addEventListener('click', finalizarEntrega);

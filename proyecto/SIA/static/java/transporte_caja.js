// Definir la función para manejar errores de geolocalización
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

// Variable para almacenar el ID de pallet y las coordenadas de transporte
let coordenadasTransporte = []; // Este array almacenará todas las coordenadas
let idPallet = null;
var latitudTransporte = null;
var longitudTransporte = null;
var transporteMarker = null;

// Función para manejar el inicio de entrega y almacenar coordenadas iniciales
function iniciarEntrega() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const latitudTransporte = position.coords.latitude;
            const longitudTransporte = position.coords.longitude;

            // Enviar las coordenadas iniciales y el id_pallet al servidor
            $.ajax({
                type: "POST",
                url: $('#startDeliveryForm').attr('action'), // URL correcta del formulario
                data: {
                    ruta_inicio_latitude: latitudTransporte,
                    ruta_inicio_longitude: longitudTransporte,
                    id_pallet: $('#id_pallet').val(), // Asegúrate de tener este campo en tu formulario
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    console.log('Coordenadas iniciales enviadas:', response);
                    if (response.success) {
                        idPallet = response.pallet_id;
                        envioid = response.envio_id // Guarda el ID del pallet desde la respuesta
                        console.log('ID del pallet guardado:', idPallet);
                        localStorage.setItem('idPallet', idPallet); // Guarda el idPallet en el almacenamiento local
                        localStorage.setItem('envioid', envioid)
                        document.getElementById('startDelivery').disabled = true;

                        
                        // Inicializa el array de coordenadas y almacena en localStorage
                        let coordenadasTransporte = [];

                        // Variable para almacenar la última coordenada registrada
                        let ultimaCoordenada = null;

                        // Inicia el seguimiento de ubicación
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

                            if (!ultimaCoordenada || 
                                ultimaCoordenada.latitud !== latitud || 
                                ultimaCoordenada.longitud !== longitud) {
                                
                                // Almacena las nuevas coordenadas junto con la marca de tiempo
                                ultimaCoordenada = { latitud, longitud, tiempo: tiempoActual };
                                coordenadasTransporte.push(ultimaCoordenada);
                                localStorage.setItem('coordenadasTransporte', JSON.stringify(coordenadasTransporte));
                        
                                console.log('Coordenadas actualizadas:', latitud, longitud, 'a las', tiempoActual);
                            }

                            console.log('Coordenadas actualizadas:', latitud, longitud);
                        }, errorGeoLocation);
                    }
                }
            });
        }, errorGeoLocation);
    } else {
        alert('Geolocalización no soportada.');
    }
}

// Función para finalizar la entrega y enviar coordenadas adicionales
function finalizarEntrega() {
    console.log("Función finalizarEntrega llamada");
    const idPallet = localStorage.getItem('idPallet'); // Obtén el id del pallet desde el almacenamiento local
    const envioid = localStorage.getItem('envioid');
    console.log('ID del pallet al finalizar:', idPallet); // Depura el valor
    console.log('ID del envioPallet al finalizar:', envioid); // Depura el valor

    if (!idPallet) {
        console.error('No se ha iniciado la entrega');
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const latitudFinal = position.coords.latitude;
            const longitudFinal = position.coords.longitude;
            const tiempoActual = new Date().toISOString(); 

            // Recupera las coordenadas del localStorage
            const coordenadasTransporte = JSON.parse(localStorage.getItem('coordenadasTransporte')) || [];
            
            // Añade las coordenadas finales al array
            coordenadasTransporte.push({ latitud: latitudFinal, longitud: longitudFinal, tiempo : tiempoActual });

            // Enviar las coordenadas al servidor
            $.ajax({
                type: "POST",
                url: $('#endDeliveryForm').attr('action'), // URL correcta del formulario
                data: JSON.stringify({
                    latitude: latitudFinal,
                    longitude: longitudFinal,
                    coordenadasTransporte: coordenadasTransporte, // No es necesario convertir a JSON ya que lo hicimos antes
                    id_pallet: idPallet,// ID del pallet
                    envio_id: envioid
                }),
                contentType: "application/json", // Asegura que el contenido se envíe como JSON
                headers: {
                    'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() // Agrega el token CSRF de Django
                },
                success: function(response) {
                    console.log('Entrega finalizada:', response);
                    if (response.success) {
                        alert(response.message);
                        // Aquí puedes agregar lógica para redirigir o actualizar la página
                        localStorage.removeItem('coordenadasTransporte');
                    } else {
                        alert(response.message);
                    }
                },
                error: function(error) {
                    console.error('Error al finalizar entrega:', error);
                }
            });
        }, errorGeoLocation);
    } else {
        alert('Geolocalización no soportada.');
    }
}

// Asignar el evento al botón de inicio de entrega
document.getElementById('startDelivery').addEventListener('click', iniciarEntrega);
document.getElementById('endDelivery').addEventListener('click', finalizarEntrega);
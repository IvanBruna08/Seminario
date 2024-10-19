// Inicializar el mapa de Mapbox
mapboxgl.accessToken = 'pk.eyJ1IjoiaXZhYjk4IiwiYSI6ImNtMHlwdGR4bTBxemYyc3EzeWlweTB4b3UifQ.SqDs4IzkxrtKlWqrbDfNXw';
var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [-71.33679, -29.95223], // Centro inicial del mapa
    zoom: 13
});

// Agregar control de geolocalización al mapa
var geolocate = new mapboxgl.GeolocateControl({
    positionOptions: {
        enableHighAccuracy: true
    },
    trackUserLocation: true
});
map.addControl(geolocate);

// Definir las coordenadas de origen y destino usando las variables
var latitudOrigen = parseFloat("{{ predio.latitude }}".replace(',', '.'));
var longitudOrigen = parseFloat("{{ predio.longitude }}".replace(',', '.'));
var latitudDestino = parseFloat("{{ distribuidor.latitude }}".replace(',', '.'));
var longitudDestino = parseFloat("{{ distribuidor.longitude }}".replace(',', '.'));

// Marcadores para el origen y destino
var markerOrigen = new mapboxgl.Marker({ color: 'green' })
    .setLngLat([longitudOrigen, latitudOrigen])
    .setPopup(new mapboxgl.Popup().setText('Origen: Predio'))
    .addTo(map);

var markerDestino = new mapboxgl.Marker({ color: 'red' })
    .setLngLat([longitudDestino, latitudDestino])
    .setPopup(new mapboxgl.Popup().setText('Destino: Cliente'))
    .addTo(map);

// Dibuja la ruta desde el origen hasta el destino al cargar el mapa
map.on('load', function () {
    getRoute();
});

// Función para obtener la ruta
async function getRoute() {
    const response = await fetch(`https://api.mapbox.com/directions/v5/mapbox/driving/${longitudOrigen},${latitudOrigen};${longitudDestino},${latitudDestino}?geometries=geojson&access_token=${mapboxgl.accessToken}`);
    const data = await response.json();
    const route = data.routes[0].geometry.coordinates;

    map.addSource('route', {
        'type': 'geojson',
        'data': {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': route
            }
        }
    });

    map.addLayer({
        'id': 'route',
        'type': 'line',
        'source': 'route',
        'layout': {
            'line-join': 'round',
            'line-cap': 'round'
        },
        'paint': {
            'line-color': '#888',
            'line-width': 6
        }
    });
}

// Resto de tu código...

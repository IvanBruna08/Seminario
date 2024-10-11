document.addEventListener("DOMContentLoaded", function() {
  var mapId = document.querySelector('[id^="map-"]');

  if (mapId) {
    var mapElement = mapId;
    // Reemplazar ',' con '.' en las coordenadas
    var latitude = parseFloat(mapElement.getAttribute('data-latitude').replace(',', '.'));
    var longitude = parseFloat(mapElement.getAttribute('data-longitude').replace(',', '.'));

    // Depuración: imprimir las coordenadas en la consola
    console.log("Latitud:", latitude, "Longitud:", longitude);
    
    // Verificar si las coordenadas son válidas y crear el mapa
    if (!isNaN(latitude) && !isNaN(longitude)) {
      initMap(mapElement.id, latitude, longitude);
    } else {
      console.error("Las coordenadas no son válidas.");
    }
  }
});

function initMap(mapId, latitude, longitude) {
  mapboxgl.accessToken = 'pk.eyJ1IjoiaXZhYjk4IiwiYSI6ImNtMHlwdGR4bTBxemYyc3EzeWlweTB4b3UifQ.SqDs4IzkxrtKlWqrbDfNXw';

  // Crear el mapa
  var map = new mapboxgl.Map({
    container: mapId,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [longitude, latitude], // Asegúrate de que el orden sea [longitud, latitud]
    zoom: 13
  });

  // Crear el marcador
  new mapboxgl.Marker()
    .setLngLat([longitude, latitude]) // Asegúrate de que el orden sea [longitud, latitud]
    .addTo(map);
}

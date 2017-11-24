var map;
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
    zoom: 5,
    center: new google.maps.LatLng(39.7645187, -104.9951967),
    mapTypeId: 'terrain'
});

// Create a <script> tag and set the USGS URL as the source.
var script = document.createElement('script');
    // This example uses a local copy of the GeoJSON stored at
    // http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojsonp
    script.src = '/route';
    document.getElementsByTagName('head')[0].appendChild(script);
}

// Loop through the results array and place a marker for each
// set of coordinates.
window.eqfeed_callback = function(trails) {
    var route = trails.route;
    var other = trails.other;
    var flightPlanCoordinates = [];

    for (var i = 0; i < route.length; i++) {
        var latLng = new google.maps.LatLng(route[i].lat,route[i].lon);
        var marker = new google.maps.Marker({
            position: latLng,
            map: map,
            title: '(' + route[i].rating + ') ' + route[i].name,
            label: i.toString()
        });
        flightPlanCoordinates.push({lat: route[i].lat, lng: route[i].lon});
    }

    for (var i = 0; i < other.length; i++) {
        var latLng = new google.maps.LatLng(other[i].lat, other[i].lon);
        var marker = new google.maps.Marker({
            position: latLng,
            map: map,
            title: '(' + other[i].rating + ') ' + other[i].name,
            label: other[i].rating.toString()
        });
    }

    var flightPath = new google.maps.Polyline({
        path: flightPlanCoordinates,
        geodesic: true,
        strokeColor: '#FF0000',
        strokeOpacity: 1.0,
        strokeWeight: 2
    });

    flightPath.setMap(map);
}
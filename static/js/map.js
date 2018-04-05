var map;

Array.prototype.add = function(latLng, title, noCluster) {
    var marker = new google.maps.Marker({
        position: latLng,
        title: title,
        label: this.length.toString()
    });

    if(noCluster) {
        marker.setMap(map);
    }

    this.push(marker);
};

Array.prototype.clear = function(to) {
    to = to || 0;
    while(this.length > to) {
        this.pop().setMap(null);
    }
}

var markers = [];
var destinations = [];

function getRoute(stops, success) {
    var req = new XMLHttpRequest();
    // req.setRequestHeader('Content-Type', 'application/json');
    req.onreadystatechange = function() {
        if (req.readyState === XMLHttpRequest.DONE) {
            if(req.status == 200) {
                try {
                    obj = JSON.parse(req.responseText);
                    success(obj);
                }
                catch(e) {
                    alert('Parsing frigged up.')
                }
            }
            else {
                alert('Somthin frigged up.');
            }
        }
    };
    req.open('POST', '/route', true);
    req.send(JSON.stringify({ 'stops': stops }));
}


function clearMarkers() {
    markers.clear();
    destinations.clear();
    map.clusterer.clearMarkers();
}


function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 5,
        center: new google.maps.LatLng(39.7645187, -104.9951967),
        mapTypeId: 'terrain'
    });

    map.clusterer = new MarkerClusterer(map, [], {
        imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'
    });

    function refresh() {
        map.clusterer.clearMarkers();
        map.clusterer = new MarkerClusterer(map, markers, {
            imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'
        });
    }

    map.addListener('click', function(e) {
        console.log(e);
        destinations.add(e.latLng, destinations.length == 0 ? "Start" : "End", true);

        if(destinations.length >= 2) {
            stops = [];
            for(var i = destinations.length; i--;) {
                stop = { lat: destinations[i].position.lat(), lon: destinations[i].position.lng() };
                stops.push(stop)
            }

            function titleFromWaypoint(way)
            {
                var rating = '';
                for(var i = parseInt(way.rating); i--; rating += '⭐️');
                return way.name + ' ' + rating;
            }

            getRoute(stops, function(trip) {
                var route = trip.route;
                for(var i = route.length; i--;)
                {
                    waypoint = route[i];
                    markers.add(
                        new google.maps.LatLng(waypoint.lat, waypoint.lon),
                        titleFromWaypoint(waypoint)
                    );
                }
                refresh();
            });
        }

        refresh();
    });

    map.addListener('zoom_changed', function() {
        refresh();
    });


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

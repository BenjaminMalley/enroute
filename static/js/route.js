$(document).ready(function() {
	var position_watcher;
	var directionsDisplay;
	var map;
	var destination;
	var position;
	var marker;

	var flash_error = function(error) {
		alert(error); //TODO: make nice div
	};
	
	
	$('input[name="destination-bar"]').keypress( function(e) {
		if (e.which == 13) { // user has pressed enter
			e.preventDefault();
			destination = $(this).val();
			
			var directionsService = new google.maps.DirectionsService();
			directionsService.route({
				origin: position,
				destination: destination,
				travelMode: google.maps.TravelMode.DRIVING
			}, function(result, status) {
				if (status == google.maps.DirectionsStatus.OK) {
					directionsDisplay.setDirections(result);
				} else {
					flash_error('Bad response from Google');
				}
			});
		}
	});

	$('#begin-btn').on('click', function() {
		if(!($(this).hasClass('btn-disabled'))) {
			$.post('/tweet/', { 
				lat: position.lat(),
				lng: position.lng(),
				dest: destination,
				dur: result.routes[0].legs[0].duration.value
			});
		}
	});

	(function() { //init
		if (!!navigator.geolocation) { // geolocation supported
			navigator.geolocation.getCurrentPosition(function(p) {
				position = new google.maps.LatLng(p.coords.latitude, p.coords.longitude);
			});

			directionsDisplay = new google.maps.DirectionsRenderer();
				
			map = new google.maps.Map($('#map-canvas')[0], {
				center: position,
				zoom: 8,		
				mapTypeId: google.maps.MapTypeId.ROADMAP
			});
			directionsDisplay.setMap(map);
			
			marker = new google.maps.Marker({
				position: position,
				map: map,
				title: 'Here you are'
			});

			position_watcher = navigator.geolocation.watchPosition( function(p) {
				position = new google.maps.LatLng(p.coords.latitude, p.coords.longitude);
				marker.setPosition(position);
			}, function(e) {
				if (e.code == 1) {
					flash_error('You must allow location sharing.');
				} else {
					flash_error('Could not identify position.');
				}
			});
		} else { // geolocation not supported
			flash_error('Geolocation not supported by this browser');
		}
	})();

	//get_route(new google.maps.LatLng(p.coords.latitude, p.coords.longitude), destination); 

});


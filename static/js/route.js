$(document).ready(function() {
	var position_watcher;
	var directionsDisplay;
	var map;
	var map_initialized = false;

	var flash_error = function(error) {
		alert(error); // change this to update and animate a div
	};
	
	var initialize_map = function(position, z) {
		directionsDisplay = new google.maps.DirectionsRenderer();
		map = new google.maps.Map($('#map-canvas')[0], {
			center: position,
			zoom: z,
			mapTypeId: google.maps.MapTypeId.ROADMAP
		});
		directionsDisplay.setMap(map);
		map_initialized = true;
	};
	
	var get_route = function(pos, dest) {
		var directionsService = new google.maps.DirectionsService();
		directionsService.route({
			origin: pos,
			destination: dest,
			travelMode: google.maps.TravelMode.DRIVING
		}, function(result, status) {
			if (status == google.maps.DirectionsStatus.OK) {
				$.post('/tweet/', { // update the server
					lat: pos.lat(),
					lng: pos.lng(),
					dest: dest,
					dur: result.routes[0].legs[0].duration.value
				});
				if (!map_initialized) {
					initialize_map(pos, 8);
					directionsDisplay.setDirections(result);
				} else {
					var marker = new google.maps.Marker({
						position: pos,
						map: map,
						title: 'Here you are'
					});
				}
			} else {
				flash_error('Bad response from Google');
			}
		});
	};
	
	var update_location = function(destination) { // get geolocation and update map
		if (!!navigator.geolocation) { // geolocation supported
			position_watcher = navigator.geolocation.watchPosition( function(p) {
				get_route(new google.maps.LatLng(p.coords.latitude, p.coords.longitude), destination); 
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
	};
	
	$('input[name="destination-bar"]').keypress( function(e) {
		if (e.which == 13) { // user has pressed enter
			e.preventDefault();
			update_location($(this).val());
		}
	});

	
	var scale_fonts = function() {
		$('.search-bar').css('font-size', (350 * ($(window).height() / 704)) + '%');
	};
	
	$(window).resize(function() { scale_fonts(); });
	
	scale_fonts();
	
	$('.view-switcher').on('click', function() {
		$(this).hide();
		if($(this).attr('id')==='directions-button') {
			$('#map-button').show();
		} else {
			$('#directions-button').show();
		}
	});
});


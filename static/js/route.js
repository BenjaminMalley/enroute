$(document).ready(function() {
	var position_watcher;
	var directionsDisplay;
	var map;
	var destination;
	var position;
	var marker;
	var route;

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
					route = result.routes[0].legs[0];
					$("#begin-btn").removeClass("disabled");
					for (var i = 0; i < result.routes[0].legs[0].steps.length; i++) {
						$("<li/>", {
							html: result.routes[0].legs[0].steps[i].instructions
						}).appendTo($("#dirlist").children().first());
					}
				} else {
					flash_error("Bad response from Google");
				}
			});
		}
	});


	var update = function(p) {
		position = new google.maps.LatLng(p.coords.latitude, p.coords.longitude);
		marker.setPosition(position);
		$.post("/update/", { 
			lat: position.lat(),
			lng: position.lng(),
			dest: destination,
			dur: route.duration.value
		}, function(response) {
			if (response === "OK") {
			} else {
				flash_error("Trouble communicating with server. Try again in a few minutes.");	
			}
		});	
	};
		
	var begin = $("#begin-btn");
	begin.on('click', function() {
		if(!begin.hasClass('disabled')) {
			if(!begin.hasClass("btn-red")) {
				$.post("/begin/", { 
					lat: position.lat(),
					lng: position.lng(),
					dest: destination,
					dur: route.duration.value
				}, function(response) {
					if (response === "OK") {
						begin.text("End trip");
						begin.addClass("btn-red");
					} else {
						flash_error("Trouble communicating with server. Please try again in a few minutes.");			
					}
				});
			} else {
				$.post("/end/", {}, function(response) {
					begin.text("I'm on my way!");
					begin.removeClass("btn-red");
					begin.addClass("disabled");
				});
			}
		}
	});

	var showMap = $("#showmap");
	var showDir = $("#showdir");
	var mapCanvas = $("#map-canvas");
	var dirList = $("#dirlist");
	showMap.on("click", function() {
		showMap.parent().addClass("active");
		showDir.parent().removeClass("active");
		dirList.addClass("hidden");
		mapCanvas.removeClass("hidden");
	});
	showDir.on("click", function() {
		showDir.parent().addClass("active");
		showMap.parent().removeClass("active");
		mapCanvas.addClass("hidden");
		dirList.removeClass("hidden");
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
				update(p);
				//setInterval(update, 10000, p);
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
});


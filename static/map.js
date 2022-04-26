let map, infoWindow;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: -38.718258, lng: -62.261487 }, //Bahía Blanca
    zoom: 12,
    });
    infoWindow = new google.maps.InfoWindow();

    const myLatLng = { lat: -38.7092234, lng: -62.2756314 };
    

    const image =
    "https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png";

    new google.maps.Marker({
      position: myLatLng,
      map,
      title: "Hello World!",
      icon: image,
    });

    new google.maps.Marker({
      position: myLatLng1,
      map,
      title: "Hello World!",
    });
      

    // Geolocalización
    const locationButton = document.createElement("button");

    locationButton.textContent = "Ir a mi ubicación";
    locationButton.classList.add("custom-map-control-button");
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
    locationButton.addEventListener("click", () => {
      // Try HTML5 geolocation.
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const pos = {
              lat: position.coords.latitude,
              lng: position.coords.longitude,
            };

            infoWindow.setPosition(pos);
            infoWindow.setContent("Estás aquí.");
            infoWindow.open(map);
            map.setCenter(pos);
          },
          () => {
            handleLocationError(true, infoWindow, map.getCenter());
          }
        );
      } else {
        // Browser doesn't support Geolocation
        handleLocationError(false, infoWindow, map.getCenter());
      }
    });
  }

  function handleLocationError(browserHasGeolocation, infoWindow, pos) {
    infoWindow.setPosition(pos);
    infoWindow.setContent(
      browserHasGeolocation
        ? "Error: El servicio de geolocalización falló."
        : "Error: Tu navegador no soporta la geolocalización."
    );
    infoWindow.open(map);
  }


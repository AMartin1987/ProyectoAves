// Crear variables para usar después
let map, infoWindow;
var markers = [];
var especie = [];
var edad = [];
var foto = [];
var direccion, tiporef1, tiporef2;
var especies = [];
var InforObj = [];
var ID = [];

// Crear mapa
function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: -38.718258, lng: -62.261487 }, // Bahía Blanca
    zoom: 13,
    });

    // Generar markers
    for (let i = 0; i < ubic_len; i++) {
        let lat = ubic_dict[i].Latitud;
        let lng = ubic_dict[i].Longitud;

        // Generar ID de cada marker
        for (let m = 0; m < aves_len; m++) { // Chequea todas las aves posibles para esta ubicación
            if (ubic_dict[i].Id == aves_dict[m].Id_UBICACIONES) {
                for (let o = 0; o < espe_len; o ++) { // Chequea todas las especies contra este ave
                    if (aves_dict[m].Id_ESPECIES == espe_dict[o].Id ) {
                        n = espe_dict[o].Categoria; // Agrega esta especie al array ID
                    }
                }
            }
        }
        for (let m = 0; m < refug_len; m++) {
            if (ubic_dict[i].Id == refug_dict[m].Id_UBICACIONES) {
                n = 'refugio';
            }
        }
        ID.push(n);

        // Agregar ID y localización a cada marcador
        myLocation = new google.maps.LatLng(lat, lng);
        const marker = new google.maps.Marker({
            position: myLocation,
            map,
            id: ID[i],
            icon: 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
        });
        // Almacenar cada marcador en array "markers"
        markers.push(marker);
    
        // Generar infowindow para cada marker de ave
        for (let j = 0; j < aves_len; j++) {
            if (ubic_dict[i].Id == aves_dict[j].Id_UBICACIONES) {
            especie.push(aves_dict[j].Especie);
            edad.push(aves_dict[j].Edad);
            img = String(aves_dict[j].Foto.replace(/"/g,''));
            foto.push(img);
            direccion = ubic_dict[i].Direccion.split(',');
            direccion = direccion[0];

            const info = new google.maps.InfoWindow({
            content: '<div style=line-height:2;text-align: left><span style="font-size:1.2em;font-weight: bold;">' +
            especie[j] +
            '</span><br><class="edad"><span style="text-decoration: underline;">Edad:</span> ' +
            edad[j] + '<img src="static/upload/' + foto[j] + '"><span style="text-decoration:underline;">Dirección:</span> ' + direccion + '<br><div id="datos_aves"> <a href="">Contacto y más información</a></div></div>',
            maxWidth: 200,
            });

            // Modal al hacer click en infowindows de aves
            google.maps.event.addListener(info, 'domready', function() {
            document.getElementById("datos_aves").addEventListener("click", function() {
                var myModal = new bootstrap.Modal(document.getElementById('modal_aves'))
                myModal.show();
                event.preventDefault();
                document.getElementById('especie').innerHTML = aves_dict[j].Especie;
                document.getElementById('edad').innerHTML = aves_dict[j].Edad;
                document.getElementById('estsalud').innerHTML = aves_dict[j].EstSalud;
                document.getElementById('requer').innerHTML = aves_dict[j].Requer;
                document.getElementById('ubicacion-a').innerHTML = direccion;
                
                for (t=0;t <= telef_len;t++) {
                    if (telef_dict[t].Id == aves_dict[j].Id_TELEFONOS) {
                        telefono = telef_dict[t].Telefono;
                        break;
                    }
                }; 
                document.getElementById('telefono').innerHTML = telefono;
                
                for (t=0;t < tiporef_len;t++) {  
                    if (tiporef_dict[t].Id == aves_dict[j].Id_TIPOREFUGIO) {
                        if (aves_dict[j].Id_TIPOREFUGIO == '1') {
                            tiporef = 'Hogar (permanente)';
                        }
                        else if (aves_dict[j].Id_TIPOREFUGIO == '2') {
                            tiporef = 'Tránsito (temporal)';
                        }
                    }
                };
                document.getElementById('tiporef').innerHTML = tiporef;
                document.getElementById('foto').innerHTML = '<img src="static/upload/' + aves_dict[j].Foto + '">';            
            });
            });
              
            // Añadir infowindow a cada marker, abrirlo onclick, cerrar infowindow anterior
            marker.addListener('click', function () { 
          closeOtherInfo();
          info.open(marker.get('map'), marker);
          InforObj[0] = info;
        });
            }

        }; // Cierra generar markers de ave

        // Generar infowindow para cada marker de refugio
        for (let k = 0; k < refug_len; k++) {
        if (ubic_dict[i].Id == refug_dict[k].Id_UBICACIONES) {
            if (refug_dict[k].Id_TIPOREFUGIO1 == '1') {
                tiporef1 = 'Hogar (permanente)';
            }
            else if (refug_dict[k].Id_TIPOREFUGIO1 == '2') {
                tiporef1 = 'Tránsito (temporal)';
            }
            if (refug_dict[k].Id_TIPOREFUGIO2 == '1') {
                tiporef2 = '<br> Hogar (permanente)';
            }
            else if (refug_dict[k].Id_TIPOREFUGIO2 == '2') {
                tiporef2 = '<br> Tránsito (temporal)';
            }
            else if (refug_dict[k].Id_TIPOREFUGIO2 == 'NULL') {
                tiporef2 = '';
            }
            direccion = ubic_dict[i].Direccion.split(',');
            direccion = direccion[0];
            especies.push(refug_dict[k].Id_ESPECIES1);
            if (refug_dict[k].Id_ESPECIES2 !== 'NULL'){
                especies.push(refug_dict[k].Id_ESPECIES2);
            }       
            if (refug_dict[k].Id_ESPECIES3 !== 'NULL'){
                especies.push(refug_dict[k].Id_ESPECIES3);
            }
            if (refug_dict[k].Id_ESPECIES4 !== 'NULL'){
                especies.push(refug_dict[k].Id_ESPECIES4);
            }

            function replace_strings (esp) {
              for (var n = 0; n < esp.length; n++) {              
                 if (esp[n] == 1) {
                    esp[n] = "palomas";
                 }
                 else if (esp[n] == 2) {
                    esp[n] = "pequeñas aves silvestres";
                 }
                 else if (esp[n] == 3) {
                    esp[n] = "aves silvestres de tamaño medio";
                 }
                 else if (esp[n] == 4) {
                  esp[n] = "aves de corral";
                 }
              }
              return esp;
            }

            replace_strings(especies);

            const info2 = new google.maps.InfoWindow({
              content: '<div style=line-height:2;text-align: left><span style="font-size:1.2em;font-weight: bold;">Refugio para: </span><br>' +
                tiporef1 + tiporef2 + '<br><span style="text-decoration:underline;">Se reciben:</span> ' + especies + '<span>.</span><br><span style="text-decoration:underline;">Dirección:</span> ' +
                direccion + '<br><div id="datos_refugios"><a href="">Contacto y más información</a></div></div>'
            });
            especies = [];

            // Modal al hacer click en infowindows de refugios
            google.maps.event.addListener(info2, 'domready', function() {
            document.getElementById("datos_refugios").addEventListener("click", function() {
                var myModal = new bootstrap.Modal(document.getElementById('modal_refugios'))
                myModal.show();
                event.preventDefault();
                direccion = ubic_dict[i].Direccion.split(',');
                direccion = direccion[0];            
                document.getElementById('ubicacion-r').innerHTML = direccion;

                especies.push(refug_dict[k].Id_ESPECIES1);
                if (refug_dict[k].Id_ESPECIES2 !== 'NULL'){
                    especies.push(refug_dict[k].Id_ESPECIES2);
                }       
                if (refug_dict[k].Id_ESPECIES3 =! 'NULL'){
                    especies.push(refug_dict[k].Id_ESPECIES3);
                }
                if (refug_dict[k].Id_ESPECIES4 =! 'NULL'){
                    especies.push(refug_dict[k].Id_ESPECIES4);
                }
                
                replace_strings(especies);
                
                document.getElementById('especies').innerHTML = especies;
                especies = [];  
                if (refug_dict[k].Id_TIPOREFUGIO1 == '1') {
                    tiporef1 = 'Hogar (permanente)';
                }
                else if (refug_dict[k].Id_TIPOREFUGIO1 == '2') {
                    tiporef1 = 'Tránsito (temporal)';
                }
                if (refug_dict[k].Id_TIPOREFUGIO2 == '1') {
                    tiporef2 = '<br> Hogar (permanente)';
                }
                else if (refug_dict[k].Id_TIPOREFUGIO2 == '2') {
                    tiporef2 = '<br> Tránsito (temporal)';
                }
                else if (refug_dict[k].Id_TIPOREFUGIO2 == 'NULL') {
                    tiporef2 = '';
                }
                document.getElementById('tiporef1').innerHTML = tiporef1;                
                document.getElementById('tiporef2').innerHTML = tiporef2;

                for (t=0;t <= telef_len;t++) {
                    if (telef_dict[t].Id == refug_dict[k].Id_TELEFONOS) {
                        telefono = telef_dict[t].Telefono;
                        break;
                    }
                };

                document.getElementById('telefono-r').innerHTML = telefono;
             });
            });


            // Añadir infowindow a cada marker, abrirlo onclick, cerrar infowindow anterior
            marker.addListener('click', function () { 
                closeOtherInfo();
                info2.open(marker.get('map'), marker);
                InforObj[0] = info2;
            });
        }
        }    
    };

    //Función para cerrar infowindow anterior
    function closeOtherInfo() { 
        if (InforObj.length > 0) {
            InforObj[0].set("marker", null);
            InforObj[0].close();
            InforObj.length = 0;
        }
   }

 // Geolocalización
 infoWindow = new google.maps.InfoWindow(); 
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
      // Mensajes de error de geolocalización
      handleLocationError(false, infoWindow, map.getCenter());
    }
  });

  function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? "Error: El servicio de geolocalización falló."
      : "Error: Tu navegador no soporta la geolocalización."
  );
  infoWindow.open(map);
  }

  //Ocultar/mostrar markers
  const checkboxes = document.getElementsByClassName('form-check-input');
  mar_len = markers.length;
  for (var i = 0; i < checkboxes.length; i++) {
    checkboxes[i].addEventListener('change', function() {
      //Mostrar/ocultar refugios
      if (document.getElementById("idRefugios").checked) {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'refugio'){
            markers[i].setVisible(true);
          }
        }
      }  
      else {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'refugio'){
            markers[i].setVisible(false);
          }
        }
      }
      //Mostrar/ocultar palomas
      if (document.getElementById("idPalomas").checked) {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'paloma'){
            markers[i].setVisible(true);
          }
        }
      }  
      else {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'paloma'){
            markers[i].setVisible(false);
          }
        }
      }
      //Mostrar/ocultar pequeñas aves silvestres
      if (document.getElementById("idPeqsil").checked) {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'peqsil'){
            markers[i].setVisible(true);
          }
        }
      }  
      else {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'peqsil'){
            markers[i].setVisible(false);
          }
        }
      }
      //Mostrar/ocultar aves silvestres medianas
      if (document.getElementById("idMedsil").checked) {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'medsil'){
            markers[i].setVisible(true);
          }
        }
      }  
      else {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'medsil'){
            markers[i].setVisible(false);
          }
        }
      }  
      //Mostrar/ocultar aves de corral
      if (document.getElementById("idCorral").checked) {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'corral'){
            markers[i].setVisible(true);
          }
        }
      }  
      else {
        for (i = 0; i < mar_len; i++) {
          if (markers[i].id == 'corral'){
            markers[i].setVisible(false);
          }
        }
      }        
  })   
 }

}  //Cierra initMap 

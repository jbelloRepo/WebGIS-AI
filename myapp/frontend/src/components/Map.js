import React from 'react'; // Make sure React is imported in each component file
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; // This import is fine here if this component is the only one using Leaflet

function Map() {
  return (
    <div className="map-container">
      
      <MapContainer 
        center={[51.505, -0.09]}
        zoom={13}
        style={{ height: "500px", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
      </MapContainer>
    </div>
  );
}

export default Map;

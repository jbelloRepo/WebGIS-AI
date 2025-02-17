import React from 'react';
import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

import ExtraIconsControl from './ExtraIconsControl'; // Import our custom 3-icon control
import './Map.css';

function Map() {
  const kitchenerCoordinates = [43.4516, -80.4925];

  return (
    <div className="map-container">
      <MapContainer
        center={kitchenerCoordinates}
        zoom={9}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains='abcd'
          maxZoom={19}
        />

        {/* 
          Leaflet's built-in ZoomControl, pinned to bottom-left.
          We remove the default text (so no "+" / "−") but the buttons remain functional.
        */}
        <ZoomControl
          position="bottomleft"
          zoomInText=""       
          zoomInTitle="Zoom in"
          zoomOutText=""
          zoomOutTitle="Zoom out"
        />

        {/* Our custom 3-icon control pinned to top-left */}
        <ExtraIconsControl />
      </MapContainer>
    </div>
  );
}

export default Map;

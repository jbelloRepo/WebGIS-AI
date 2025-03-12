import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, ZoomControl, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { fetchWaterMainGeometries, fetchWaterMainById } from '../api/api';
import ExtraIconsControl from './ExtraIconsControl';
import ChatWindow from './ChatWindow';
import './Map.css';

function Map() {
  const kitchenerCoordinates = [43.4516, -80.4925];
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [waterMains, setWaterMains] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWaterMain, setSelectedWaterMain] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const geometries = await fetchWaterMainGeometries();
        
        // Convert WKT to GeoJSON
        const geoJsonData = geometries.map(item => {
          return {
            type: "Feature",
            id: item.object_id,
            properties: {
              object_id: item.object_id
            },
            geometry: wktToGeoJSON(item.geometry)
          };
        });
        
        setWaterMains(geoJsonData);
        setIsLoading(false);
      } catch (err) {
        console.error("Error fetching water mains:", err);
        setError("Failed to load water mains data");
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Function to convert WKT to GeoJSON
  const wktToGeoJSON = (wkt) => {
    if (!wkt) return null;
    
    // Basic WKT LINESTRING parser
    // Example: "LINESTRING(-80.123 43.123, -80.124 43.124)"
    try {
      const match = wkt.match(/LINESTRING\s*\((.*)\)/i);
      if (!match) return null;
      
      const coordinates = match[1].split(',').map(coord => {
        const [lng, lat] = coord.trim().split(' ').map(parseFloat);
        return [lng, lat];
      });
      
      return {
        type: "LineString",
        coordinates: coordinates
      };
    } catch (e) {
      console.error("Failed to parse WKT:", e);
      return null;
    }
  };

  const handleAiChatClick = () => {
    setIsChatOpen((prev) => !prev);
  };

  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      // Create a basic popup initially
      const popup = L.popup();
      
      // When a water main is clicked, fetch detailed information
      layer.on('click', async (e) => {
        try {
          // Show loading message in popup
          popup.setContent('<div class="popup-loading">Loading details...</div>');
          popup.setLatLng(e.latlng).openOn(layer._map);
          
          // Fetch detailed water main data
          const details = await fetchWaterMainById(feature.properties.object_id);
          setSelectedWaterMain(details);
          
          // Create detailed popup content with the fetched data
          const popupContent = `
            <div class="popup-container">
              <h3>WaterMain Details</h3>
              <table class="popup-table">
                <tr>
                  <td><strong>ID:</strong></td>
                  <td>${details.object_id}</td>
                </tr>
                <tr>
                  <td><strong>Status:</strong></td>
                  <td>${details.status || 'N/A'}</td>
                </tr>
                <tr>
                  <td><strong>Material:</strong></td>
                  <td>${details.material || 'N/A'}</td>
                </tr>
                <tr>
                  <td><strong>Pressure Zone:</strong></td>
                  <td>${details.pressure_zone || 'N/A'}</td>
                </tr>
                <tr>
                  <td><strong>Condition:</strong></td>
                  <td>${details.condition_score > 0 ? details.condition_score : 'N/A'}</td>
                </tr>
                <tr>
                  <td><strong>Length:</strong></td>
                  <td>${details.shape_length ? `${details.shape_length.toFixed(2)} m` : 'N/A'}</td>
                </tr>
              </table>
            </div>
          `;
          
          // Update the popup with detailed content
          popup.setContent(popupContent);
          popup.update();
        } catch (err) {
          console.error(`Error fetching details for water main ${feature.properties.object_id}:`, err);
          popup.setContent(`<div class="popup-error">Error loading details</div>`);
          popup.update();
        }
      });
    }
  };

  const waterMainStyle = {
    color: '#3388ff',
    weight: 3,
    opacity: 0.7
  };

  return (
    <div className="map-container">
      {isLoading && <div className="loading-overlay">Loading water mains data...</div>}
      {error && <div className="error-message">{error}</div>}
      
      <MapContainer
        center={kitchenerCoordinates}
        zoom={9}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={19}
        />

        {/* Render water mains data as GeoJSON */}
        {waterMains.length > 0 && waterMains.map(feature => (
          feature.geometry && (
            <GeoJSON
              key={feature.id}
              data={feature}
              style={waterMainStyle}
              onEachFeature={onEachFeature}
            />
          )
        ))}

        {/* Leaflet ZoomControl pinned at bottom-left */}
        <ZoomControl
          position="bottomleft"
          zoomInText=""
          zoomInTitle="Zoom in"
          zoomOutText=""
          zoomOutTitle="Zoom out"
        />

        {/* Our 3-icon custom control pinned to top-left */}
        <ExtraIconsControl onAiChatClick={handleAiChatClick} />
      </MapContainer>

      {/* The ChatWindow overlay (slides in from the right) */}
      <ChatWindow
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}

export default Map;
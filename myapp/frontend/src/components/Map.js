import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, ZoomControl, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { fetchWaterMainGeometries, fetchWaterMainById, fetchWaterMainGeometriesByIds, createFilterToken, fetchWaterMainsByToken } from '../api/api';
import ExtraIconsControl from './ExtraIconsControl';
import ChatWindow from './ChatWindow';
import LayerControl from './LayerControl';
import './Map.css';

// Component to handle zoom to bounds
function ZoomToFeatures({ bounds }) {
  const map = useMap();
  
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  
  return null;
}

function Map() {
  const kitchenerCoordinates = [43.4516, -80.4925];
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isLayerControlOpen, setIsLayerControlOpen] = useState(false);
  const [waterMains, setWaterMains] = useState([]);
  const [filteredWaterMains, setFilteredWaterMains] = useState([]);
  const [isFiltered, setIsFiltered] = useState(false);
  const [filterCount, setFilterCount] = useState(0);
  const [featureBounds, setFeatureBounds] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWaterMain, setSelectedWaterMain] = useState(null);
  
  // State for layer visibility
  const [layers, setLayers] = useState([
    { id: 'baseMap', name: 'Base Map', visible: true },
    { id: 'waterMains', name: 'Water Mains', visible: true },
  ]);

  // Reference to the map instance
  const mapRef = useRef(null);
  const filteredLayerRef = useRef(null);

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
    // Close layer control when opening chat
    if (!isChatOpen) {
      setIsLayerControlOpen(false);
    }
  };

  const handleLayersClick = () => {
    setIsLayerControlOpen((prev) => !prev);
    // Close chat when opening layer control
    if (!isLayerControlOpen) {
      setIsChatOpen(false);
    }
  };

  const handleToggleLayer = (layerId) => {
    setLayers(prevLayers => 
      prevLayers.map(layer => 
        layer.id === layerId 
          ? { ...layer, visible: !layer.visible } 
          : layer
      )
    );
  };

  // Find layer by ID
  const getLayerVisibility = (layerId) => {
    const layer = layers.find(l => l.id === layerId);
    return layer ? layer.visible : false;
  };

  // Function to handle map filtering based on IDs
  const handleFilterMap = async (objectIds, count) => {
    try {
      console.log(`Starting to filter map with ${objectIds.length} IDs`);
      setIsLoading(true);
      
      // Get a token instead of passing all IDs directly
      const tokenResponse = await createFilterToken(objectIds);
      const token = tokenResponse.token;
      
      // Fetch the geometries using the token
      const filteredGeometries = await fetchWaterMainsByToken(token);
      console.log(`Received ${filteredGeometries.length} geometries, converting to GeoJSON...`);
      
      // Convert to GeoJSON
      const filteredGeoJson = filteredGeometries.map(item => {
        return {
          type: "Feature",
          id: item.object_id,
          properties: {
            object_id: item.object_id
          },
          geometry: wktToGeoJSON(item.geometry)
        };
      });
      
      console.log(`Created ${filteredGeoJson.length} GeoJSON features`);
      setFilteredWaterMains(filteredGeoJson);
      setIsFiltered(true);
      setFilterCount(count);
      
      // Calculate bounds for the filtered features
      if (filteredGeoJson.length > 0) {
        const bounds = calculateBounds(filteredGeoJson);
        setFeatureBounds(bounds);
        console.log(`Set feature bounds: ${JSON.stringify(bounds)}`);
      }
      
      setIsLoading(false);
    } catch (err) {
      console.error("Error filtering water mains:", err);
      setError("Failed to filter water mains data");
      setIsLoading(false);
    }
  };

  // Calculate bounds for a set of features
  const calculateBounds = (features) => {
    let minLat = 90;
    let maxLat = -90;
    let minLng = 180;
    let maxLng = -180;

    features.forEach(feature => {
      if (feature.geometry && feature.geometry.coordinates) {
        feature.geometry.coordinates.forEach(coord => {
          const lng = coord[0];
          const lat = coord[1];
          
          minLat = Math.min(minLat, lat);
          maxLat = Math.max(maxLat, lat);
          minLng = Math.min(minLng, lng);
          maxLng = Math.max(maxLng, lng);
        });
      }
    });

    // Return Leaflet bounds
    return [[minLat, minLng], [maxLat, maxLng]];
  };

  // Clear the filter and show all water mains
  const clearFilter = () => {
    // Remove the filtered layer from the map if it exists
    if (filteredLayerRef.current && mapRef.current) {
      filteredLayerRef.current.clearLayers();
      mapRef.current.removeLayer(filteredLayerRef.current);
      filteredLayerRef.current = null;
    }
    
    setIsFiltered(false);
    setFilteredWaterMains([]);
    setFilterCount(0);
    setFeatureBounds(null);
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
    weight: 2,
    opacity: 0.7
  };

  useEffect(() => {
    if (isFiltered && filteredWaterMains.length > 0 && mapRef.current) {
      console.log(`Rendering ${filteredWaterMains.length} filtered water mains on map`);
      
      // Clear any existing filtered layer
      if (filteredLayerRef.current) {
        filteredLayerRef.current.clearLayers();
        mapRef.current.removeLayer(filteredLayerRef.current);
      }
      
      // Create a new filtered layer
      filteredLayerRef.current = L.geoJSON(filteredWaterMains, {
        style: {
          color: '#FF4500',
          weight: 3,
          opacity: 0.8
        },
        onEachFeature: onEachFeature
      }).addTo(mapRef.current);
      
      // If we have bounds, fit to them
      if (featureBounds) {
        mapRef.current.fitBounds(featureBounds);
      }
    }
  }, [isFiltered, filteredWaterMains, featureBounds]);

  // // Add this effect to scroll when messages change
  // useEffect(() => {
  //   const messagesContainer = document.querySelector('.chat-messages'); // Use your actual class name
  //   if (messagesContainer) {
  //     messagesContainer.scrollTop = messagesContainer.scrollHeight;
  //   }
  // }, [messages]); // Trigger when messages change

  return (
    <div className="map-container">
      {isLoading && <div className="loading-overlay">Loading water mains data...</div>}
      {error && <div className="error-message">{error}</div>}
      
      <MapContainer
        center={kitchenerCoordinates}
        zoom={9}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        ref={mapRef}
      >
        {/* Base Map Layer - only show if visible */}
        {getLayerVisibility('baseMap') && (
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
            subdomains="abcd"
            maxZoom={19}
          />
        )}

        {/* Render all water mains if not filtered and the layer is visible */}
        {!isFiltered && getLayerVisibility('waterMains') && waterMains.length > 0 && waterMains.map(feature => (
          feature.geometry && (
            <GeoJSON
              key={feature.id}
              data={feature}
              style={waterMainStyle}
              onEachFeature={onEachFeature}
            />
          )
        ))}

        {/* Render filtered water mains if filter is active and the layer is visible */}
        {isFiltered && getLayerVisibility('waterMains') && filteredWaterMains.length > 0 && filteredWaterMains.map(feature => (
          feature.geometry && (
            <GeoJSON
              key={feature.id}
              data={feature}
              style={{
                ...waterMainStyle,
                color: '#ff4500',  // Highlight filtered features
                weight: 3
              }}
              onEachFeature={onEachFeature}
            />
          )
        ))}

        {/* ZoomToFeatures component will zoom to bounds when they change */}
        {featureBounds && <ZoomToFeatures bounds={featureBounds} />}

        {/* Leaflet ZoomControl pinned at bottom-left */}
        <ZoomControl
          position="bottomleft"
          zoomInText=""
          zoomInTitle="Zoom in"
          zoomOutText=""
          zoomOutTitle="Zoom out"
        />

        {/* Our 3-icon custom control pinned to top-left */}
        <ExtraIconsControl 
          onAiChatClick={handleAiChatClick}
          onLayersClick={handleLayersClick} 
        />
      </MapContainer>

      {/* Layer Control */}
      <LayerControl
        isOpen={isLayerControlOpen}
        onClose={() => setIsLayerControlOpen(false)}
        layers={layers}
        onToggleLayer={handleToggleLayer}
      />

      {/* Filter indicator */}
      {isFiltered && (
        <div style={{
          position: 'absolute',
          bottom: '30px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#f0f8ff',
          padding: '10px 20px',
          borderRadius: '8px',
          border: '2px solid #3388ff',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          minWidth: '180px',
          fontWeight: 'bold',
          fontSize: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ 
              color: '#3388ff', 
              fontSize: '18px', 
              fontWeight: 'bold',
              marginRight: '4px'
            }}>
              {filterCount}
            </span> 
            <span>features filtered</span>
          </div>
          <button 
            onClick={clearFilter}
            style={{
              background: '#ff4500',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '14px',
              marginLeft: '10px'
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* The ChatWindow overlay (slides in from the right) */}
      <ChatWindow
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onFilterMap={handleFilterMap}
      />
    </div>
  );
}

export default Map;
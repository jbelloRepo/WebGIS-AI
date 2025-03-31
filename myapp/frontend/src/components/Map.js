import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, ZoomControl, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  fetchWaterMainGeometries,
  fetchWaterMainById,
  fetchWaterMainGeometriesByIds,
  createFilterToken,
  fetchWaterMainsByToken,
  // NEW:
  fetchAllDatasets,
  fetchDatasetData
} from '../api/api';
import ExtraIconsControl from './ExtraIconsControl';
import ChatWindow from './ChatWindow';
import LayerControl from './LayerControl';
import AddDatasetDialog from './AddDatasetDialog';
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
  const [isAddDatasetOpen, setIsAddDatasetOpen] = useState(false);
  const [waterMains, setWaterMains] = useState([]);
  const [filteredWaterMains, setFilteredWaterMains] = useState([]);
  const [isFiltered, setIsFiltered] = useState(false);
  const [filterCount, setFilterCount] = useState(0);
  const [featureBounds, setFeatureBounds] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWaterMain, setSelectedWaterMain] = useState(null);

  // NEW: store dataset configs and features
  const [datasets, setDatasets] = useState([]); // an array of {id, name, table_name, ...}
  const [datasetFeatures, setDatasetFeatures] = useState({}); // {table_name: [Feature, ...]}

  // State for layer visibility
  const [layers, setLayers] = useState([
    { id: 'baseMap', name: 'Base Map', visible: true },
    { id: 'waterMains', name: 'Water Mains', visible: true },
    // We could dynamically add new datasets here, see below
  ]);

  // Reference to the map instance
  const mapRef = useRef(null);
  const filteredLayerRef = useRef(null);

  useEffect(() => {
    // Existing code to fetch water mains
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

  // NEW: fetch dataset list and their records
  useEffect(() => {
    async function loadDatasetsAndData() {
      try {
        // 1) get the list of all datasets
        const all = await fetchAllDatasets(); 
        setDatasets(all);

        // 2) for each dataset, load its actual records
        const featsByTable = {};
        for (const ds of all) {
          const records = await fetchDatasetData(ds.table_name);
          // Convert each record's WKT geometry to a GeoJSON Feature
          const featuresForThisDs = records.map((rec) => {
            return {
              type: "Feature",
              properties: { ...rec }, // store entire row in 'properties'
              geometry: wktToGeoJSON(rec.geometry)
            };
          });
          featsByTable[ds.table_name] = featuresForThisDs;
        }

        setDatasetFeatures(featsByTable);

        // Optionally, automatically add these new datasets to your layer control:
        // If you want each dataset to be toggled on/off separately:
        const newLayers = all.map(ds => ({
          id: ds.table_name,
          name: ds.name || ds.table_name,
          visible: true,
        }));
        setLayers(prev => [...prev, ...newLayers]);

      } catch (err) {
        console.error("Error loading datasets or data:", err);
      }
    }

    loadDatasetsAndData();
  }, []);

  // Function to convert WKT to GeoJSON
  const wktToGeoJSON = (wkt) => {
    if (!wkt) return null;
    
    // Basic WKT LINESTRING parser
    // Example: "LINESTRING(-80.123 43.123, -80.124 43.124)"
    try {
      // You can expand this to handle POLYGON, POINT, etc. 
      // For demonstration, we handle LINESTRING only
      // (But for your real code, handle the geometry type carefully)
      const lineMatch = wkt.match(/LINESTRING\s*\((.*)\)/i);
      if (lineMatch) {
        const coordinates = lineMatch[1].split(',').map(coord => {
          const [lng, lat] = coord.trim().split(' ').map(parseFloat);
          return [lng, lat];
        });
        return {
          type: "LineString",
          coordinates: coordinates
        };
      }

      // If you have polygons, points, etc. handle them here
      const pointMatch = wkt.match(/POINT\s*\((.*)\)/i);
      if (pointMatch) {
        const [lng, lat] = pointMatch[1].trim().split(' ').map(parseFloat);
        return {
          type: "Point",
          coordinates: [lng, lat]
        };
      }

      // Example polygon pattern: POLYGON((x1 y1, x2 y2, ...))
      const polygonMatch = wkt.match(/POLYGON\s*\(\((.*)\)\)/i);
      if (polygonMatch) {
        const coords = polygonMatch[1].split(',').map(coord => {
          const [lng, lat] = coord.trim().split(' ').map(parseFloat);
          return [lng, lat];
        });
        return {
          type: "Polygon",
          coordinates: [coords]
        };
      }

      // If none matched, fallback
      console.error("No recognized geometry in WKT:", wkt);
      return null;

    } catch (e) {
      console.error("Failed to parse WKT:", e, wkt);
      return null;
    }
  };

  const handleAiChatClick = () => {
    setIsChatOpen((prev) => !prev);
    if (!isChatOpen) {
      setIsLayerControlOpen(false);
    }
  };

  const handleLayersClick = () => {
    setIsLayerControlOpen((prev) => !prev);
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

  // Function to handle map filtering based on IDs (existing code)
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
        // For a LineString or Polygon, feature.geometry.coordinates 
        // could be an array of [lng, lat] or array of arrays
        // This example assumes a simple array of [lng, lat] for lines:
        if (feature.geometry.type === 'LineString') {
          feature.geometry.coordinates.forEach(coord => {
            const [lng, lat] = coord;
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
            minLng = Math.min(minLng, lng);
            maxLng = Math.max(maxLng, lng);
          });
        } else if (feature.geometry.type === 'Polygon') {
          // For polygon, geometry.coordinates is [ [ [lng, lat], [lng, lat] ... ] ]
          feature.geometry.coordinates[0].forEach(coord => {
            const [lng, lat] = coord;
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
            minLng = Math.min(minLng, lng);
            maxLng = Math.max(maxLng, lng);
          });
        } else if (feature.geometry.type === 'Point') {
          const [lng, lat] = feature.geometry.coordinates;
          minLat = Math.min(minLat, lat);
          maxLat = Math.max(maxLat, lat);
          minLng = Math.min(minLng, lng);
          maxLng = Math.max(maxLng, lng);
        }
      }
    });

    return [[minLat, minLng], [maxLat, maxLng]];
  };

  // Clear the filter and show all water mains
  const clearFilter = () => {
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

  // For Water Mains ONLY
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const popup = L.popup();
      
      layer.on('click', async (e) => {
        try {
          popup.setContent('<div class="popup-loading">Loading details...</div>');
          popup.setLatLng(e.latlng).openOn(layer._map);
          
          // This fetch is for Water Mains only
          const details = await fetchWaterMainById(feature.properties.object_id);
          setSelectedWaterMain(details);
          
          const popupContent = `
            <div class="popup-container">
              <h3>WaterMain Details</h3>
              <table class="popup-table">
                <tr><td><strong>ID:</strong></td><td>${details.object_id}</td></tr>
                <tr><td><strong>Status:</strong></td><td>${details.status || 'N/A'}</td></tr>
                <tr><td><strong>Material:</strong></td><td>${details.material || 'N/A'}</td></tr>
                <tr><td><strong>Pressure Zone:</strong></td><td>${details.pressure_zone || 'N/A'}</td></tr>
                <tr><td><strong>Condition:</strong></td><td>${details.condition_score > 0 ? details.condition_score : 'N/A'}</td></tr>
                <tr><td><strong>Length:</strong></td><td>${details.shape_length ? `${details.shape_length.toFixed(2)} m` : 'N/A'}</td></tr>
              </table>
            </div>
          `;
          
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
      
      if (filteredLayerRef.current) {
        filteredLayerRef.current.clearLayers();
        mapRef.current.removeLayer(filteredLayerRef.current);
      }
      
      filteredLayerRef.current = L.geoJSON(filteredWaterMains, {
        style: {
          color: '#FF4500',
          weight: 3,
          opacity: 0.8
        },
        onEachFeature: onEachFeature
      }).addTo(mapRef.current);
      
      if (featureBounds) {
        mapRef.current.fitBounds(featureBounds);
      }
    }
  }, [isFiltered, filteredWaterMains, featureBounds]);

  const handleAddDatasetClick = () => {
    setIsAddDatasetOpen(true);
    setIsChatOpen(false);
    setIsLayerControlOpen(false);
  };

  // UPDATED: Re-fetch data after a new dataset is added
  const handleDatasetAdded = async () => {
    console.log('Dataset added successfully');
    // Just re-run the loadDatasetsAndData function from above:
    // Easiest is to repeat the logic or factor it out into a helper:
    try {
      const all = await fetchAllDatasets(); 
      setDatasets(all);

      const featsByTable = {};
      for (const ds of all) {
        const records = await fetchDatasetData(ds.table_name);
        const featuresForThisDs = records.map((rec) => ({
          type: "Feature",
          properties: { ...rec },
          geometry: wktToGeoJSON(rec.geometry)
        }));
        featsByTable[ds.table_name] = featuresForThisDs;
      }
      setDatasetFeatures(featsByTable);

      // Optionally re-build the layers array for layer control
      // (Might want to first remove old dynamic layers or check for duplicates)
      const newLayers = all.map(ds => ({
        id: ds.table_name,
        name: ds.name || ds.table_name,
        visible: true,
      }));
      // Overwrite or merge
      setLayers([
        { id: 'baseMap', name: 'Base Map', visible: true },
        { id: 'waterMains', name: 'Water Mains', visible: true },
        ...newLayers
      ]);
    } catch (e) {
      console.error("Error re-loading datasets after add:", e);
    }
  };


  function onEachDatasetFeature(feature, layer) {
    layer.on('click', (e) => {
      const props = feature.properties || {};
  
      // 1) Convert to array of [key, value].
      // 2) Filter out the geometry field.
      // 3) Limit to the first 10.
      const allEntries = Object.entries(props).filter(([k, _]) => k !== "geometry");
      const firstTen = allEntries.slice(0, 10);
  
      // Build a small table in HTML
      let popupContent = `
        <div style="font-size: 14px; line-height: 1.4;">
          <strong>Attributes (showing up to 10)</strong><br/>
          <table>
      `;
  
      for (const [key, value] of firstTen) {
        popupContent += `<tr><td>${key}</td><td>${value}</td></tr>`;
      }
  
      // If there are more than 10, let the user know
      if (allEntries.length > 10) {
        popupContent += `
          <tr style="color: #888;">
            <td colspan="2">
              ... plus ${allEntries.length - 10} more
            </td>
          </tr>
        `;
      }
  
      popupContent += `</table></div>`;
  
      // Bind and open the popup
      layer.bindPopup(popupContent).openPopup(e.latlng);
    });
  }
  
  


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
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> : Contains information licensed under the Open Government Licence - The Corporation of the City of Kitchener.'
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
                color: '#ff4500',  // highlight filtered features
                weight: 3
              }}
              onEachFeature={onEachFeature}
            />
          )
        ))}

        {/* Render new datasets from datasetFeatures */}
        {datasets.map(ds => {
          if (!getLayerVisibility(ds.table_name)) {
            return null; 
          }
          const feats = datasetFeatures[ds.table_name] || [];
          return feats.map((feature, idx) => {
            if (!feature.geometry) return null;
            return (
              <GeoJSON
                key={`${ds.table_name}-${idx}`}
                data={feature}
                // You can define a style or onEachFeature if needed
                style={{
                  color: '#008000', // just a default color for demonstration
                  weight: 2
                }}
                onEachFeature={onEachDatasetFeature}
              />
            );
          });
        })}

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
          onAddDatasetClick={handleAddDatasetClick}
        />
      </MapContainer>

      {/* Layer Control */}
      <LayerControl
        isOpen={isLayerControlOpen}
        onClose={() => setIsLayerControlOpen(false)}
        layers={layers}
        onToggleLayer={handleToggleLayer}
      />

      {/* Add Dataset Dialog */}
      <AddDatasetDialog
        open={isAddDatasetOpen}
        onClose={() => setIsAddDatasetOpen(false)}
        onSuccess={handleDatasetAdded}
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

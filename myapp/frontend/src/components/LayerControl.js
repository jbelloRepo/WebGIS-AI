import React from 'react';
import './LayerControl.css';

function LayerControl({ isOpen, onClose, layers, onToggleLayer }) {
  if (!isOpen) return null;

  return (
    <div className="layer-control">
      <div className="layer-control-header">
        <h3>Map Layers</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      <div className="layer-list">
        {layers.map((layer) => (
          <div key={layer.id} className="layer-item">
            <label className="layer-checkbox">
              <input 
                type="checkbox" 
                checked={layer.visible} 
                onChange={() => onToggleLayer(layer.id)}
              />
              <span className="checkmark"></span>
            </label>
            <span className="layer-name">{layer.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LayerControl; 
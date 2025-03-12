// ExtraIconsControl.jsx
import { useMap } from 'react-leaflet';
import { useEffect } from 'react';
import L from 'leaflet';

function ExtraIconsControl({ onAiChatClick }) {
  const map = useMap();

  useEffect(() => {
    // Create a new Leaflet Control
    const MyControl = L.Control.extend({
      // Put this control in the top-left corner
      options: { position: 'topleft' },

      onAdd: function (_map) {
        // Create container <div> with Leaflet's "leaflet-bar" class
        const container = L.DomUtil.create('div', 'leaflet-bar my-extra-icons');

        // ========== 1. HOME ICON ==========
        const homeBtn = L.DomUtil.create('a', '', container);
        homeBtn.href = '#';
        homeBtn.title = 'Go to Home';
        homeBtn.innerHTML = `
          <span class="material-symbols-outlined">
            home
          </span>
        `;
        L.DomEvent.on(homeBtn, 'click', (e) => {
          L.DomEvent.stop(e);
          console.log('Home clicked!');
          map.setView([43.4516, -80.4925], 9);
        });

        // ========== 2. ANALYTICS ICON ==========
        const analyticsBtn = L.DomUtil.create('a', '', container);
        analyticsBtn.href = '#';
        analyticsBtn.title = 'View Analytics';
        analyticsBtn.innerHTML = `
          <span class="material-symbols-outlined">
            bar_chart_4_bars
          </span>
        `;
        L.DomEvent.on(analyticsBtn, 'click', (e) => {
          L.DomEvent.stop(e);
          console.log('Analytics clicked!');
        });

        // ========== 3. AI CHAT ICON ==========
        const aiChatBtn = L.DomUtil.create('a', '', container);
        aiChatBtn.href = '#';
        aiChatBtn.title = 'Open AI Chat';
        aiChatBtn.innerHTML = `
          <span class="material-symbols-outlined">
            smart_toy
          </span>
        `;
        L.DomEvent.on(aiChatBtn, 'click', (e) => {
          L.DomEvent.stop(e);
          console.log('AI Chat clicked!');
          // The callback we got from props
          onAiChatClick();
        });

        return container;
      },
    });

    // Instantiate the control and add it to the map
    const myControlInstance = new MyControl();
    map.addControl(myControlInstance);

    // Cleanup when unmounted
    return () => {
      map.removeControl(myControlInstance);
    };
  }, [map, onAiChatClick]);

  return null;
}

export default ExtraIconsControl;

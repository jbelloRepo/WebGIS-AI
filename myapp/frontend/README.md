# WebGIS-AI Frontend

This directory contains the frontend web application for the WebGIS-AI project, built with React and Leaflet for interactive mapping capabilities.

## Directory Structure

```
frontend/
├── public/         # Static files and HTML template
├── src/            # Source code
│   ├── api/        # API client and service integrations
│   │   ├── Map.js            # Main map component with GIS functionality
│   │   ├── ChatWindow.js     # AI chat interface
│   │   ├── LayerControl.js   # Map layer management
│   │   └── ...               # Other UI components
│   ├── App.js      # Main application component
│   └── index.js    # Application entry point
├── .env            # Environment variables
├── nginx.conf      # Nginx configuration for production
├── dockerfile      # Docker container definition
└── package.json    # Dependencies and scripts
```

## Technology Stack

- **React**: Frontend framework for building the user interface
- **Leaflet**: Interactive mapping library
- **ESRI Leaflet**: Extensions for integrating ESRI services with Leaflet
- **Material-UI**: React component library for UI design
- **Axios**: HTTP client for API requests
- **Nginx**: Web server for serving the production build

## Features

### Interactive Map

- **Base Maps**: Multiple base layers including satellite imagery and topographic maps
- **Vector Layers**: Display of GIS data as vector overlays
- **Zoom/Pan Controls**: Standard map navigation capabilities
- **Home Extent**: Quick return to initial map view
- **Feature Selection**: Interactive selection of map features
- **Attribute Display**: View detailed information about selected features

### AI-Powered Chat Interface

- **Natural Language Queries**: Use plain English to perform spatial analysis
- **Dynamic SQL Generation**: Backend translates natural language to spatial SQL
- **Result Visualization**: Automatic visualization of query results on the map
- **Chat History**: Persistent conversation history
- **Context-Aware Responses**: Maintains context throughout the conversation

### Data Management

- **Layer Controls**: Toggle visibility of different data layers
- **Data Import**: Upload and integrate new GIS datasets
- **Symbology Control**: Change the appearance of map features
- **Data Export**: Download analysis results in various formats

## Setup and Development

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Docker (for production builds)

### Local Development

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Configure environment variables:
   ```
   # Create a .env file with the following variables
   REACT_APP_API_URL=http://localhost:8000
   ```

3. Start the development server:
   ```
   npm start
   ```

4. Open your browser to `http://localhost:3000`

### Building for Production

1. Create an optimized production build:
   ```
   npm run build
   ```

2. The build artifacts will be in the `build/` directory

3. Using Docker:
   ```
   docker build -t webgis-ai-frontend .
   docker run -p 80:80 webgis-ai-frontend
   ```

## Component Overview

### Map Component

The core map component (`Map.js`) provides:
- Integration with Leaflet and ESRI Leaflet
- Layer management
- Event handling for user interactions
- Coordinate system management
- Dynamic styling of geographic features

### ChatWindow Component

The AI chat interface (`ChatWindow.js`) provides:
- User input handling
- Communication with backend AI services
- Message rendering
- Context management for continuing conversations
- Integration with map for query results visualization

### Layer Controls

Layer management components allow users to:
- Toggle layer visibility
- Adjust layer opacity
- Change rendering order
- Access metadata about layers

## Testing

Run the test suite:

```
npm test
```

The project uses Jest and React Testing Library for unit and integration tests.

## Browser Compatibility

The application is optimized for:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Edge (latest 2 versions)
- Safari (latest 2 versions)

## Performance Considerations

- Map rendering is optimized for large datasets using clustering and simplification
- Images and assets are optimized for web delivery
- Code-splitting is used to minimize initial load time
- React component memoization is used where appropriate

## Contributing

When working on the frontend:

1. Follow established React patterns and project structure
2. Use functional components with hooks
3. Document components with JSDoc comments
4. Write tests for new components and features
5. Use the existing styling approach for consistency
6. Ensure responsive design for all screen sizes

## Troubleshooting

### Common Issues

1. **Map not displaying**
   - Check browser console for errors
   - Verify that Leaflet CSS is properly loaded
   - Ensure map container has a defined height

2. **API connection errors**
   - Verify backend is running
   - Check CORS configuration
   - Confirm API URL in environment variables

3. **Layer visibility issues**
   - Check layer z-index settings
   - Verify data is properly loaded
   - Test map bounds to ensure data is in view

## Additional Resources

- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [Leaflet Documentation](https://leafletjs.com/reference.html)
- [Material-UI Documentation](https://mui.com/getting-started/usage/)
- [PostGIS Documentation](https://postgis.net/docs/) (helpful for understanding spatial data)

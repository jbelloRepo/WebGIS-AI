# WebGIS-AI Application

This directory contains the application code for the WebGIS-AI project, a platform that integrates Geographic Information Systems (GIS) with AI capabilities.

## Directory Structure

```
myapp/
├── frontend/           # React-based UI
├── backend/            # Server-side components
│   ├── database/       # PostgreSQL/PostGIS database setup
│   ├── server/         # FastAPI backend service
│   ├── scrapper/       # Data collection and processing
│   └── qgis/           # QGIS integration service
```

## Components Overview

### Frontend

The frontend is built with React and provides an interactive map interface with:

- Interactive map viewer with standard GIS controls
- Layer management interface
- AI-powered chat interface for natural language queries
- Feature attribute display
- Responsive design for various device sizes

### Backend

The backend consists of several microservices:

1. **Database Service**
   - PostgreSQL with PostGIS extension
   - Stores spatial data, user queries, and application state
   - Handles complex spatial queries and operations

2. **API Server**
   - FastAPI-based REST API
   - Handles authentication, request validation, and business logic
   - Communicates with AI services and the database
   - Manages caching via Redis

3. **Data Scraper**
   - Collects and processes geospatial data from various sources
   - Updates the database with new and modified data
   - Handles data validation and transformation

4. **QGIS Service**
   - Performs advanced geospatial processing
   - Generates maps and visualizations
   - Executes complex spatial analysis

## Local Development

### Prerequisites

- Docker and Docker Compose
- Node.js (for frontend development)
- Python 3.9+ (for backend development)
- OpenAI API key

### Starting the Application

1. Set up environment variables:
   ```
   # In the root directory
   cp .env.example .env
   # Add your OpenAI API key to the .env file
   ```

2. Start all services using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Frontend Development

For active frontend development:

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. The frontend will be available at http://localhost:3000 with hot reloading enabled.

### Backend Development

For active backend development:

1. Set up a Python virtual environment:
   ```
   cd backend/server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Run the FastAPI server with auto-reload:
   ```
   uvicorn main:app --reload
   ```

3. The API will be available at http://localhost:8000.

## Testing

### Frontend Tests

```
cd frontend
npm test
```

### Backend Tests

```
cd backend/server
pytest
```

## Deployment

The application is designed to be deployed using Docker Compose in production environments. For production deployment:

1. Update environment variables in .env for production settings
2. Build and deploy the containers:
   ```
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Ensure PostgreSQL container is running: `docker ps`
   - Check logs: `docker logs postgis-db-service`

2. **API errors**
   - Verify API is running: `curl http://localhost:8000/health`
   - Check logs: `docker logs fastapi-service`

3. **Frontend not displaying**
   - Ensure Nginx is running: `docker ps`
   - Check logs: `docker logs react-frontend-service`

4. **QGIS processing errors**
   - Check QGIS service logs: `docker logs qgis-service`

## Contributing

Please refer to the main project README for contribution guidelines. For application-specific development:

1. Create feature branches from the development branch
2. Follow the established code style and patterns
3. Write tests for new functionality
4. Document your changes

## Related Resources

- [Main Project Documentation](../README.md)
- [Frontend Documentation](./frontend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [PostGIS Documentation](https://postgis.net/workshops/postgis-intro/index.html)

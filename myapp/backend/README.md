# WebGIS-AI Backend

This directory contains the server-side components of the WebGIS-AI project, implementing the microservices architecture that powers the application.

## Directory Structure

```
backend/
├── database/       # PostgreSQL/PostGIS database setup
│   ├── init/       # Database initialization scripts
│   └── Dockerfile  # Database container definition
│
├── server/         # FastAPI backend service
│   ├── api/        # API endpoints
│   ├── models/     # Data models
│   ├── services/   # Business logic
│   ├── utils/      # Helper functions
│   └── Dockerfile  # API container definition
│
├── scrapper/       # Data collection and processing
│   ├── scripts/    # Data collection scripts
│   ├── processors/ # Data transformation logic
│   └── Dockerfile  # Scraper container definition
│
└── qgis/           # QGIS integration service
    ├── scripts/    # QGIS processing scripts
    ├── templates/  # Map templates
    └── Dockerfile  # QGIS container definition
```

## Services Overview

### Database Service (PostgreSQL/PostGIS)

The database service is responsible for storing and managing all spatial data and application state.

**Key Features:**
- PostGIS extension for spatial data storage and queries
- Spatial indexing for efficient query performance
- Database schemas for organizing data
- SQL functions for complex spatial operations

**Development Notes:**
- Database schema migrations are managed through initialization scripts
- Connection settings are configured via environment variables
- Persistent storage is managed through Docker volumes

### API Server (FastAPI)

The API server handles HTTP requests, business logic, and communication with other services.

**Key Features:**
- RESTful API endpoints for all application functions
- WebSocket support for real-time updates
- Integration with OpenAI API for natural language processing
- Authentication and authorization
- Request validation and error handling
- Redis integration for caching

**Development Notes:**
- API is built with FastAPI for performance and type safety
- AsyncIO is used for handling concurrent requests
- Automatic API documentation is available at `/docs` endpoint

### Data Scraper

The data scraper service collects, validates, and processes geospatial data from various sources.

**Key Features:**
- Automated data collection from public GIS APIs
- Data validation and cleaning
- Coordinate system transformations
- Scheduled data updates
- Error handling and reporting

**Development Notes:**
- Python-based ETL (Extract, Transform, Load) processes
- Configurable data sources through environment variables
- Logging and monitoring for data processing activities

### QGIS Service

The QGIS service provides advanced geospatial processing capabilities.

**Key Features:**
- Map generation and styling
- Complex spatial analysis
- Custom visualization generation
- Export capabilities for different formats (PDF, PNG, SVG)

**Development Notes:**
- Uses PyQGIS for programmatic access to QGIS functionality
- Headless operation for server environments
- Integration with database for spatial data access

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL client (for direct database access)
- OpenAI API key

### Local Development

1. Set up environment variables:
   ```
   # In the root directory
   cp .env.example .env
   # Add your OpenAI API key and other configuration
   ```

2. Start the backend services:
   ```
   docker-compose up -d postgis redis api scraper qgis
   ```

3. Monitor logs:
   ```
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f api
   ```

### Working with Individual Services

#### Database Development

1. Access the PostgreSQL shell:
   ```
   docker exec -it postgis-db-service psql -U gis_user -d gis_data
   ```

2. Apply schema changes:
   ```
   # Create a new migration script
   touch backend/database/init/05-my-migration.sql
   
   # Edit the script
   nano backend/database/init/05-my-migration.sql
   
   # Restart the database to apply changes
   docker-compose restart postgis
   ```

#### API Development

1. Local development with hot reload:
   ```
   cd backend/server
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Start the API with auto-reload
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Test an endpoint:
   ```
   curl http://localhost:8000/health
   ```

3. Access the documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

#### Scraper Development

1. Run scraper manually:
   ```
   docker exec -it python-scrapper-service python /app/run_scraper.py
   ```

2. Check scraper logs:
   ```
   docker logs python-scrapper-service
   ```

#### QGIS Service Development

1. Execute a QGIS processing script:
   ```
   docker exec -it qgis-service python /app/scripts/generate_map.py
   ```

2. Check output files:
   ```
   ls -la backend/qgis/output/
   ```

## Testing

Run backend tests:

```
# API tests
cd backend/server
pytest

# Database tests
cd backend/database/tests
python -m pytest

# Integration tests
cd backend/tests
python -m pytest
```

## Deployment

The backend services are designed to be deployed as Docker containers. For production:

1. Update environment variables for production in the .env file
2. Build and deploy using Docker Compose:
   ```
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## Performance Tuning

### Database Optimization

- Configure `postgresql.conf` settings in the database container
- Implement proper indexing for frequently queried columns
- Use connection pooling for improved performance

### API Optimization

- Enable response compression
- Implement appropriate caching strategies
- Use asynchronous handlers for I/O-bound operations

## Security Considerations

- All services run in isolated containers
- Database credentials are passed via environment variables
- API endpoints are protected with authentication where needed
- Input validation is performed on all API endpoints
- CORS is configured to allow only specific origins

## Troubleshooting

### Common Issues

1. **Database connection issues**
   - Check PostgreSQL logs: `docker logs postgis-db-service`
   - Verify environment variables are set correctly
   - Ensure database port is accessible

2. **API not responding**
   - Check API logs: `docker logs fastapi-service`
   - Verify API dependencies are available
   - Check for Python exceptions in the logs

3. **Scraper failures**
   - Check scraper logs: `docker logs python-scrapper-service`
   - Verify data source availability
   - Check for rate limiting or authentication issues with external APIs

4. **QGIS processing errors**
   - Check QGIS logs: `docker logs qgis-service`
   - Verify QGIS dependencies are installed
   - Check file permissions for output directories

## Contributing

When contributing to the backend:

1. Follow the established code style (PEP 8 for Python)
2. Document all API endpoints with docstrings
3. Write unit tests for new functionality
4. Update documentation for any changes
5. Use meaningful commit messages

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [QGIS Python API](https://qgis.org/pyqgis/)

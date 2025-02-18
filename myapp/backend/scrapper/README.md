# GIS Data Scrapper

A Python service that scrapes GIS data from REST APIs and stores it in a PostgreSQL database.

## Description

This service is designed to automatically collect and process Geographic Information System (GIS) data from various REST API endpoints. It handles data extraction, transformation, and loading into a PostgreSQL database for further analysis and usage.

## Features

- Automated GIS data collection from REST APIs
- Support for multiple data sources and formats
- Data transformation and standardization
- PostgreSQL database integration
- Configurable scheduling for periodic updates
- Error handling and logging
- Pagination support for large datasets
- Docker containerization

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Docker (optional)

## Configuration

### Database Configuration
Create a `.env` file in the root directory with the following variables:

```bash
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432

```

### GIS REST API Configuration
Configure your data sources in `scripts/gis_rest_config.json`:

```json
{
    "CityName": {
        "DatasetType": "REST_API_URL"
    }
}
```

## Installation

### Using Docker
1. Build the container:

```bash
docker build -t gis-scrapper .
```

2. Run the container:

```bash
docker run -d gis-scrapper
```

### Manual Installation
1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:

```bash
python scripts/scrape.py
```

The script will:
1. Load configurations from JSON files
2. Connect to the specified REST APIs
3. Fetch GIS data with pagination support
4. Transform and store data in PostgreSQL
5. Generate detailed logs in the `logs` directory

## Project Structure

```
scrapper/
├── scripts/
│   ├── scrape.py           # Main script
│   ├── db_operations.py    # Database operations
│   ├── rest_2_db_adapter.py # REST API adapter
│   └── db_conn_config.py   # Database configuration
├── Dockerfile
├── requirements.txt
└── .env
```

## Logging

Logs are stored in the `logs` directory with detailed information including:
- Timestamp
- System information
- Operation details
- Error traces (if any)

## Error Handling

The service includes comprehensive error handling for:
- Database connection issues
- API request failures
- Data transformation errors
- Configuration problems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
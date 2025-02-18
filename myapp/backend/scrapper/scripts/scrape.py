"""
GIS Data Scraper Script

This script is responsible for fetching GIS data from configured REST APIs and storing it in a database.
It processes multiple cities and dataset types as defined in the configuration file.

The script:
1. Loads dataset configurations from a JSON file
2. Iterates through each city and dataset type
3. Fetches data from the corresponding REST API endpoints
4. Stores the retrieved data in the database

Configuration is expected to be in the format:
{
    "CityName": {
        "DatasetType": "REST_API_URL",
        ...
    },
    ...
}
"""

from rest_2_db_adapter import load_dataset_config, fetch_gis_data
from db_operations import update_water_mains_data
import logging
from datetime import datetime
import os
import sys
import platform

def setup_logging() -> logging.Logger:
    """Configure and return a logger instance with detailed formatting."""
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger('gis_scraper')
    logger.setLevel(logging.INFO)
    
    # Create detailed formatter
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d]\n'
        'System: %(system_info)s\n'
        'Message: %(message)s\n'
    )
    
    # Add system info to all log records
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.system_info = f"{platform.system()} {platform.release()} - Python {sys.version.split()[0]}"
        return record
    logging.setLogRecordFactory(record_factory)
    
    # File handler with detailed logs
    file_handler = logging.FileHandler(
        f'logs/scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler with simpler format for readability
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def run_scraper() -> None:
    """Main function to run the GIS data scraping process."""
    logger = setup_logging()
    
    try:
        start_time = datetime.now()
        logger.info(f"Initializing GIS data scraping process at {start_time}")
        
        # Load the dataset configuration
        logger.info("Attempting to load dataset configuration from JSON file...")
        dataset_config = load_dataset_config()
        logger.info(f"Successfully loaded configuration for {len(dataset_config)} cities")
        
        # Iterate through each city and dataset
        for city, datasets in dataset_config.items():
            city_start_time = datetime.now()
            logger.info(f"Beginning data collection for {city} | Available datasets: {list(datasets.keys())}")
            
            for dataset_type in datasets.keys():
                try:
                    logger.info(
                        f"Processing {dataset_type} for {city}\n"
                        f"API Endpoint: {datasets[dataset_type]}"
                    )
                    
                    logger.info(f"Fetching paginated data for {dataset_type}...")
                    data = fetch_gis_data(city, dataset_type, dataset_config)
                    
                    if data and 'features' in data:
                        feature_count = len(data['features'])
                        logger.info(
                            f"Complete data retrieval successful for {city} {dataset_type}\n"
                            f"Total records retrieved: {feature_count}\n"
                            f"Fields available: {list(data['features'][0]['attributes'].keys()) if feature_count > 0 else 'None'}"
                        )
                        
                        # Add this block to store the data
                        try:
                            logger.info(f"Storing {feature_count} records in database...")
                            update_water_mains_data(city, dataset_type, data)
                            logger.info("Database update completed successfully")
                        except Exception as e:
                            logger.error(f"Failed to store data in database: {str(e)}")
                            sys.exit(1)
                    else:
                        logger.warning(
                            f"No features found for {city} {dataset_type}\n"
                            f"Response structure: {list(data.keys()) if data else 'Empty response'}"
                        )
                        
                except Exception as e:
                    logger.error(
                        f"Error processing {dataset_type} for {city}\n"
                        f"Error type: {type(e).__name__}\n"
                        f"Error details: {str(e)}"
                    )
                    continue
            
            logger.info(
                f"Completed processing {city}\n"
                f"Time taken: {datetime.now() - city_start_time}"
            )
        
        logger.info(
            f"Scraping process completed\n"
            f"Total execution time: {datetime.now() - start_time}\n"
            f"End time: {datetime.now()}"
        )
            
    except Exception as e:
        logger.error(
            f"Fatal error in scraper\n"
            f"Error type: {type(e).__name__}\n"
            f"Error details: {str(e)}\n"
            f"Stack trace:", exc_info=True
        )
        raise

if __name__ == "__main__":
    run_scraper()

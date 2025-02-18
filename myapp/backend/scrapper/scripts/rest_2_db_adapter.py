from typing import Dict, Optional, Any
import requests
import json
import os

def load_dataset_config(config_file: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """
    Load GIS dataset configuration from a JSON file.

    Args:
        config_file (Optional[str]): Path to the configuration file. 
            If None, uses default 'dataset_config.json' in script directory.

    Returns:
        Dict[str, Dict[str, str]]: Nested dictionary containing city and dataset configurations.
            Format: {
                'city_name': {
                    'dataset_type': 'url',
                    ...
                },
                ...
            }
    """
    config_file = os.path.join(os.path.dirname(__file__), "GIS_REST_config.json")
    with open(config_file, "r") as file:
        return json.load(file)

def fetch_gis_data(city: str, dataset_type: str, config: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    Fetch GIS data for a specific city and dataset type using the provided configuration.
    Handles pagination using resultOffset parameter.
    """
    if city not in config or dataset_type not in config[city]:
        print(f"Dataset for {city} ({dataset_type}) not found in configuration.")
        return None

    all_features = []
    offset = 0
    batch_size = 2000  # Match the resultRecordCount in the URL

    while True:
        url = config[city][dataset_type]
        # Add offset parameter to URL
        paginated_url = f"{url}&resultOffset={offset}"
        
        try:
            response = requests.get(paginated_url)
            response.raise_for_status()
            data = response.json()
            
            # Check if we got features
            features = data.get('features', [])
            if not features:
                break
                
            all_features.extend(features)
            
            # Check if we've received less than batch_size records
            # This indicates we've reached the end
            if len(features) < batch_size:
                break
                
            offset += batch_size
            
        except requests.RequestException as e:
            print(f"Error fetching data from {city} ({dataset_type}): {e}")
            return None

    # Return the data with all features combined
    return {"features": all_features} if all_features else None

# # Fetch GIS data for all datasets of a specific city
# def fetch_all_city_datasets(city):
#     if city not in DATASET_CONFIG:
#         print(f"City '{city}' not found in configuration.")
#         return None

#     all_data = {}
#     for dataset_type, url in DATASET_CONFIG[city].items():
#         print(f"Fetching data for {city} - {dataset_type}...")
#         data = fetch_gis_data(city, dataset_type)
#         if data:
#             all_data[dataset_type] = data

#     return all_data

# # Fetch GIS data for all datasets across all cities
# def fetch_all_datasets():
#     all_city_data = {}
#     for city in DATASET_CONFIG:
#         print(f"Fetching all datasets for {city}...")
#         city_data = fetch_all_city_datasets(city)
#         if city_data:
#             all_city_data[city] = city_data

#     return all_city_data

# Example usage:
if __name__ == "__main__":
    # Load dataset configuration from JSON file
    dataset_config = load_dataset_config()
    # print(dataset_config)

    # Example: Fetch water mains data for Kitchener
    kitchener_water_mains = fetch_gis_data("Kitchener", "WaterMains", dataset_config)
    # print(kitchener_water_mains)

    # if kitchener_water_mains:
    #     store_kitchener_watermains_data_in_db("Kitchener", "WaterMains", kitchener_water_mains)

import psycopg2
import json
import os

def load_db_config():
    """Load database configuration from JSON file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "db_conn_config.json")
        with open(config_path, "r") as file:
            config = json.load(file)
        print("Database configuration loaded successfully")
        return config["database"]
    except FileNotFoundError:
        print("Error: db_conn_config.json file not found")
        raise
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in db_conn_config.json")
        raise
    except KeyError:
        print("Error: 'database' key not found in config file")
        raise

def get_db_connection():
    """Create and return a database connection using configuration from JSON."""
    try:
        db_settings = load_db_config()
        conn = psycopg2.connect(**db_settings)
        print("Successfully connected to the database")
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()
        print(f"PostgreSQL database version: {db_version[0]}")
        cursor.close()
        
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        raise
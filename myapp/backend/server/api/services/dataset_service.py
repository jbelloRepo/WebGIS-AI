import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geometry
import requests

# If you need OpenAI
from openai import OpenAI
import re

# Configure OpenAI using environment variable
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WATERMAINS_SCHEMA_TEMPLATE = """
-- Create water_mains table
CREATE TABLE IF NOT EXISTS water_mains (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,               -- City name
    dataset_type VARCHAR(100) NOT NULL,       -- Type of dataset
    object_id INTEGER UNIQUE NOT NULL,        -- Unique object ID
    watmain_id INTEGER,                       -- Water main ID
    status VARCHAR(50) DEFAULT 'UNKNOWN',     -- Status (e.g., ACTIVE, ABANDONED)
    pressure_zone VARCHAR(50) DEFAULT 'UNKNOWN', -- Pressure zone
    roadsegment_id INTEGER,                   -- Related road segment ID
    map_label VARCHAR(255),                   -- Descriptive label
    category VARCHAR(50) DEFAULT 'TREATED',   -- Treated/Untreated category
    pipe_size NUMERIC DEFAULT 0,              -- Pipe size in mm
    material VARCHAR(100) DEFAULT 'UNKNOWN',  -- Pipe material
    lined VARCHAR(20) DEFAULT 'NO',           -- Lined or not
    lined_date TIMESTAMP,                     -- Date lining was done
    lined_material VARCHAR(50) DEFAULT 'NONE', -- Material for lining
    installation_date TIMESTAMP,              -- Installation date
    acquisition VARCHAR(50),                  -- Acquisition type
    consultant VARCHAR(250),                  -- Consultant name
    ownership VARCHAR(100) DEFAULT 'UNKNOWN', -- Ownership details
    bridge_main VARCHAR(1) DEFAULT 'N',       -- Bridge main indicator
    bridge_details VARCHAR(250),              -- Details about the bridge
    criticality INTEGER DEFAULT -1,           -- Criticality level
    rel_cleaning_area VARCHAR(10) DEFAULT '0', -- Cleaning area
    rel_cleaning_subarea VARCHAR(10) DEFAULT '0', -- Cleaning subarea
    undersized VARCHAR(1) DEFAULT 'N',        -- Undersized indicator
    shallow_main VARCHAR(1) DEFAULT 'N',      -- Shallow pipe indicator
    condition_score NUMERIC DEFAULT -1,       -- Condition score
    oversized VARCHAR(1) DEFAULT 'N',         -- Oversized pipe indicator
    cleaned VARCHAR(1) DEFAULT 'N',           -- Cleaned or not
    shape_length NUMERIC,                     -- Length of the geometry
    geometry GEOMETRY(LineString, 4326),      -- Spatial geometry in WGS84
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Update timestamp
);
"""

def _extract_indexes(sql_schema: str) -> list:
    """
    Extract index definitions from SQL schema (example helper function).
    """
    logger.debug("Extracting indexes from SQL schema.")
    return [
        line.strip()
        for line in sql_schema.split('\n')
        if line.strip().startswith('CREATE INDEX')
    ]

def generate_schema_with_ai(server_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use AI to generate a PostgreSQL schema based on the server metadata.
    """
    logger.info("Generating schema with AI for server metadata: %s", server_metadata)
    try:
        # Prepare the prompt
        prompt = f"""
        I have a template schema for a water mains dataset:
        {WATERMAINS_SCHEMA_TEMPLATE}

        I need to create a similar schema for a new dataset with these fields from an ArcGIS REST server:
        {json.dumps(server_metadata['fields'], indent=2)}

        The geometry type is: {server_metadata['geometryType']}

        Please generate a PostgreSQL schema that:
        1. Follows the same pattern as the water_mains table
        2. Includes appropriate columns for all fields from the REST server
        3. Uses appropriate PostgreSQL data types
        4. Includes the same metadata columns (id, created_at, updated_at)
        5. Only return the CREATE TABLE SQL statement, no other text.
        6. for polyline geometry type use geometry GEOMETRY(LineString, 4326) do not do geometry GEOMETRY(MultiLineString, 4326) or geometry GEOMETRY(Polyline, 4326), 
        7. for the field names use the field names from the REST server, do not change them. eg. objectid, to_street, etc.
        
        Never produce code fences, such as triple backticks (```)
        Never produce code blocks, such as ```sql
        Return only valid SQL (without any markdown fences or triple backticks).
        Return ONLY the SQL schema, no explanations.
        
        """

        # Make a synchronous call to the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a database expert who creates PostgreSQL schemas."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the SQL
        sql_schema = response.choices[0].message.content.strip()
        
        logger.info("Successfully generated schema with AI.")
        return {
            'sql_schema': sql_schema,
            'fields': server_metadata['fields'],
            'geometry_type': server_metadata['geometryType'],
            'indexes': _extract_indexes(sql_schema)
        }

    except Exception as e:
        logger.error("Failed to generate schema with AI: %s", str(e))
        raise Exception(f"Failed to generate schema with AI: {str(e)}")


async def fetch_server_metadata(base_url: str) -> Dict[str, Any]:
    """
    Fetch complete server metadata from ArcGIS REST endpoint (async style).
    """
    logger.info("Fetching server metadata from URL: %s", base_url)
    try:
        response = requests.get(f"{base_url}?f=pjson")
        metadata = response.json()
        
        required_fields = ['name', 'geometryType', 'fields']
        if not all(field in metadata for field in required_fields):
            raise Exception("Invalid server metadata: missing required fields")
            
        logger.info("Successfully fetched server metadata.")
        return metadata
        
    except Exception as e:
        logger.error("Failed to fetch server metadata: %s", str(e))
        raise Exception(f"Failed to fetch server metadata: {str(e)}")


async def create_dynamic_table(db: AsyncSession, table_name: str, schema: Dict[str, Any]) -> None:
    """
    Create a dynamic table based on the AI-generated schema.
    """
    logger.info("Creating dynamic table: %s", table_name)
    try:
        # Execute the SQL schema
        await db.execute(text(schema['sql_schema']))
        await db.commit()
        
        logger.info("Successfully created table: %s", table_name)
    except Exception as e:
        logger.error("Failed to create table: %s", str(e))
        await db.rollback()
        raise Exception(f"Failed to create table: {str(e)}")



def unify_table_name(sql_schema: str, table_name: str) -> str:
    """
    Search for the first occurrence of: 
        CREATE TABLE IF NOT EXISTS <SOMENAME> (
    and replace <SOMENAME> with `table_name`.
    Returns the updated SQL schema.
    """
    # Regex explanation:
    # (CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+)  -> captures the leading keywords
    # ([^\s(]+)                                -> captures the table name (no spaces or parentheses)
    # (\s*\()                                  -> captures the '(' plus optional whitespace
    pattern = re.compile(r'(CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+)([^\s(]+)(\s*\()',
                         flags=re.IGNORECASE)

    # Do the substitution, injecting your new table name
    # \1 is the 'CREATE TABLE IF NOT EXISTS '
    # \3 is the ' ('
    # We replace only the middle group with your `table_name`
    new_schema = pattern.sub(rf"\1{table_name}\3", sql_schema, count=1)
    return new_schema


async def register_dataset(
    db: AsyncSession,
    name: str,
    base_url: str,
    table_name: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Register a new dataset and create its table.
    Returns a dictionary that includes all fields needed by DatasetResponse.
    """
    
    logger.info("Registering dataset: %s", name)
    try:
        # 1) Fetch server metadata
        server_metadata = await fetch_server_metadata(base_url)
        
        # 2) Generate schema via AI
        generated_schema = generate_schema_with_ai(server_metadata)
        
        # 2a) Unify the AI's table name with our user-supplied table_name
        fixed_sql = unify_table_name(generated_schema["sql_schema"], table_name)
        generated_schema["sql_schema"] = fixed_sql

        
        # 3) Insert config row in dataset_configs (returning the new id)
        insert_sql = text("""
            INSERT INTO dataset_configs 
            (name, base_url, geometry_type, table_name, server_metadata, 
             generated_schema, display_field, description, min_scale, 
             max_scale, max_record_count)
            VALUES (:name, :base_url, :geometry_type, :table_name, :server_metadata, 
                    :generated_schema, :display_field, :description, :min_scale,
                    :max_scale, :max_record_count)
            RETURNING id
        """)

        result = await db.execute(
            insert_sql,
            {
                'name': name,
                'base_url': base_url,
                'geometry_type': server_metadata['geometryType'],
                'table_name': table_name,
                'server_metadata': json.dumps(server_metadata),
                'generated_schema': json.dumps(generated_schema),
                'display_field': server_metadata.get('displayField'),
                'description': server_metadata.get('description'),
                'min_scale': server_metadata.get('minScale'),
                'max_scale': server_metadata.get('maxScale'),
                'max_record_count': server_metadata.get('maxRecordCount', 2000)
            }
        )
        inserted_row = result.fetchone()
        await db.commit()
        if not inserted_row:
            raise Exception("Insertion returned no ID from dataset_configs")

        # The newly generated primary key
        dataset_id = inserted_row[0]

        # 4) Create the actual table in Postgres
        await create_dynamic_table(db, table_name, generated_schema)

        # Construct the dictionary that meets your DatasetResponse fields
        return_config = {
            "id": dataset_id,
            "name": name,
            "base_url": base_url,
            "table_name": table_name,
            "geometry_type": server_metadata["geometryType"],
            "display_field": server_metadata.get("displayField"),
            "description": server_metadata.get("description"),
            # "schema" is where we store generated_schema in the final response
            "schema": generated_schema,
            "max_record_count": server_metadata.get("maxRecordCount", 2000)
        }

        # After successfully registering the dataset, create a notification message
        notification_message = await create_dataset_notification_message(return_config)
        
        # Import here to avoid circular imports
        from ..services.chat_service import create_chat_message
        from ..schemas.chat import ChatMessageCreate
        
        # Store the notification in the current user's chat history
        system_message = ChatMessageCreate(
            session_id=session_id,
            message_type="system",
            content=notification_message
        )
        logger.info("Session ID in register_dataset: %s", session_id)
        
        
        logger.info("Creating system message: %s", system_message)
        
        await create_chat_message(db, system_message)
        
        logger.info("Successfully registered dataset: %s", name)
        return return_config
        
    except Exception as e:
        logger.error("Failed to register dataset: %s", str(e))
        await db.rollback()
        raise Exception(f"Failed to register dataset: {str(e)}")


async def get_dataset_config(db: AsyncSession, table_name: str) -> Optional[Dict[str, Any]]:
    """
    Get dataset configuration by table name from dataset_configs.
    """
    logger.info("Fetching dataset configuration for table: %s", table_name)
    result = await db.execute(
        text("SELECT * FROM dataset_configs WHERE table_name = :table_name"),
        {'table_name': table_name}
    )
    row = result.first()
    if row:
        logger.info("Found dataset configuration for table: %s", table_name)
        # return dict(row)
        return dict(row._mapping)
    else:
        logger.warning("No dataset configuration found for table: %s", table_name)
        return None


async def create_dataset_notification_message(dataset_config: Dict[str, Any]) -> str:
    """
    Create a notification message about a newly added dataset that can be stored in chat history.
    
    Args:
        dataset_config: The dataset configuration with schema information
        
    Returns:
        A formatted message describing the dataset and its schema
    """
    # Extract the relevant information from the dataset config
    name = dataset_config.get("name", "Unknown dataset")
    table_name = dataset_config.get("table_name", "unknown_table")
    
    # Get the schema information - this is the AI-generated schema stored in dataset_configs
    schema = dataset_config.get("schema", {})
    schema_sql = schema.get("sql_schema", "No schema available")
    
    # Create a formatted message with the dataset information
    message = f"""
            SYSTEM: A new dataset has been added: "{name}" (table: {table_name})

            Below is the schema for this dataset:
            ```sql
            {schema_sql}
            ```

            Please consider this dataset when generating SQL queries. You can:
            - Join with other tables on spatial relationships using ST_Intersects
            - Include this dataset in analysis when relevant to the user's question
            - Reference this table as "{table_name}" in your SQL queries
            
            Example:
            The user could ask: "What is the longest road in each street?"
            You could respond with:
            SELECT street_name, MAX(shape__length) AS longest_road_length
            FROM road_data
            GROUP BY street_name;

            
            """
    
    return message

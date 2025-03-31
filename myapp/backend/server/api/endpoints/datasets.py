from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import requests
import logging

from ..db.session import get_db
from ..services.dataset_service import register_dataset, get_dataset_config
from ..db.redis_connection import redis_client
from ..services.chat_service import create_chat_session, get_chat_session
from ..schemas.chat import ChatSessionCreate


# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()


#
# Pydantic models for request/response
#
class DatasetRegistration(BaseModel):
    name: str
    base_url: str
    table_name: str
    session_id: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    base_url: str | None = None
    table_name: str | None = None
    geometry_type: str | None = None
    display_field: str | None = None
    description: str | None = None
    schema: Dict[str, Any] | None = None

# class DatasetResponse(BaseModel):
#     id: int
#     name: str
#     base_url: str
#     table_name: str
#     geometry_type: str
#     display_field: str | None
#     description: str | None
#     schema: Dict[str, Any]


from datetime import datetime

def convert_timestamp(value):
    # Check if the value is an integer that looks like a Unix timestamp in milliseconds.
    if isinstance(value, int) and value > 1e9:
        return datetime.fromtimestamp(value / 1000)
    return value

#
# Background ingestion function (async)
#
async def fetch_and_store_data(db: AsyncSession, config: Dict[str, Any], offset: int = 0) -> None:
    """
    Fetch and store data from ArcGIS REST endpoint in the background.
    Paginates, upserts into Postgres, and caches in Redis.
    """
    logger.info("[1] Starting data fetch and store. Table: %s, Offset: %d", config['table_name'], offset)
    logger.debug("[2] Config details: %s", json.dumps(config, indent=2))
    
    try:
        # Build request params for ArcGIS
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': '4326',
            'f': 'json',
            'resultOffset': offset,
            'resultRecordCount': config['max_record_count']  # ensure you have 'max_record_count' in config
        }
        url = f"{config['base_url']}/query"
        
        logger.info("[4] Making request to URL: %s", url)
        response = requests.get(url, params=params)
        logger.info("[5] Response status code: %d", response.status_code)
        
        data = response.json()
        features_list = data.get('features', [])
        
        if not features_list:
            logger.info("[7] No features found for table: %s at offset: %d", config['table_name'], offset)
            return
        
        logger.info("[8] Processing %d features", len(features_list))
        features = []

        # Determine ArcGIS geometry type (Polyline, Point, Polygon, etc.)
        arcgis_geom_type = config['geometry_type'].replace('esriGeometry', '').lower()

        for idx, feature in enumerate(features_list, 1):
            geom = feature.get('geometry', {})
            attrs = feature.get('attributes', {})

            # Convert ArcGIS geometry to WKT
            wkt = None
            if arcgis_geom_type == 'polyline' and 'paths' in geom:
                # For simplicity, just use the first path
                path = geom['paths'][0]
                # Build a standard WKT LINESTRING
                coords = ", ".join(f"{p[0]} {p[1]}" for p in path)
                wkt = f"LINESTRING({coords})"

            elif arcgis_geom_type == 'point' and 'x' in geom and 'y' in geom:
                wkt = f"POINT({geom['x']} {geom['y']})"

            elif arcgis_geom_type == 'polygon' and 'rings' in geom:
                # For simplicity, use the first ring
                ring = geom['rings'][0]
                coords = ", ".join(f"{p[0]} {p[1]}" for p in ring)
                wkt = f"POLYGON(({coords}))"

            else:
                logger.warning("Unsupported geometry type for feature: %s", feature)
                continue

            # Build a dict of columns => values
            feature_data = {
                "objectid": attrs.get("OBJECTID") or attrs.get("objectid"),
                # "dataset_type": config["name"],  # or whatever you like
                "geometry": wkt,  # We'll pass the raw WKT string
            }
            
            # Copy over all other attributes, lowercasing keys
            # but skip the geometry columns to avoid collisions
            for field_name, value in attrs.items():
                lname = field_name.lower()
                if lname not in ("objectid", "shape"):  
                    if lname.endswith("date"):
                        value = convert_timestamp(value)
                    # store everything else
                    feature_data[lname] = value

            features.append(feature_data)

        if not features:
            logger.info("[10] After filtering, no valid features remain.")
            return

        # Build the INSERT statement with named placeholders
        columns = list(features[0].keys())  # all the keys from the first dict
        # We'll build something like: INSERT INTO roads_data (col1, col2, geometry, ...)
        # VALUES (:col1, :col2, ST_GeomFromText(:geometry, 4326), ...)
        # ON CONFLICT (object_id) DO UPDATE ...

        insert_cols = []
        insert_vals = []
        update_cols = []

        for col in columns:
            if col == "geometry":
                # We'll handle geometry via ST_GeomFromText
                insert_cols.append("geometry")
                insert_vals.append("ST_GeomFromText(:geometry, 4326)")
                # geometry is updated with "EXCLUDED.geometry"
                update_cols.append(f"{col} = EXCLUDED.{col}")
            else:
                insert_cols.append(col)
                insert_vals.append(f":{col}")
                if col != "objectid":  # don't update the primary key
                    update_cols.append(f"{col} = EXCLUDED.{col}")

        insert_sql = f"""
        INSERT INTO {config['table_name']} ({", ".join(insert_cols)})
        VALUES ({", ".join(insert_vals)})
        """

        logger.info("[12] Preparing to insert %d features", len(features))
        logger.debug("[13] Using SQL:\n%s", insert_sql)
        
        # Insert all features in one executemany call
        logger.info("[14] Executing database insert")
        await db.execute(text(insert_sql), features)
        await db.commit()
        logger.info("[15] Database commit successful")
        
        
        
        

        # OPTIONAL: If you're caching in Redis, you can do that here
        for feat in features:
            redis_client.hset(
                f"{config['table_name']}:all",
                str(feat['objectid']),
                json.dumps(feat, default=str)

            )
        logger.info("[17] Redis caching complete")

        # If exactly max_record_count were returned, there's likely more to fetch
        if len(features_list) == config['max_record_count']:
            next_offset = offset + config['max_record_count']
            logger.info("[18] More features available, fetching next batch at offset: %d", next_offset)
            await fetch_and_store_data(db, config, next_offset)
            
        else:
            logger.info("<==fetch_and_store_data [19]==> No more features available from ArcGIS endpoint")
            
            # No more data, ingestion is complete
            redis_client.set(f"{config['table_name']}:ingestion_status", "complete")
            redis_client.set(f"{config['table_name']}:ingestion_progress", "100")
            
            logger.info("<==fetch_and_store_data [20]==> Redis: Ingestion complete")
            
            
    except Exception as e:
        logger.error("[19] Error in fetch_and_store_data: %s", str(e), exc_info=True)
        raise Exception(f"Failed to fetch and store data: {str(e)}")

#
# 1) POST /datasets/register -> Register new dataset, start ingestion
#
@router.post("/register", response_model=DatasetResponse)
async def register_new_dataset(
    dataset: DatasetRegistration,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    logger.info("\n ==>THE SESSION PASSED FROM FRONTEND<==: %s", dataset.session_id)
    """
    Register a new dataset (table + schema) and start ingestion in the background.
    """
    logger.info("[20] Starting dataset registration. Name: %s, URL: %s", dataset.name, dataset.base_url)
    try:
        # Use the session ID from the request, falling back to global if not provided
        session_id = dataset.session_id
        logger.info("[20a] Session ID: %s", session_id)
        
        # Get or create a session_id if none is provided
        if not session_id:
            # Create a new session as a last resort
            session = await create_chat_session(db, ChatSessionCreate())
            session_id = session.session_id
            logger.info("[21c] Created new session: %s", session_id)
        else:
            # Verify the session exists
            session = await get_chat_session(db, session_id)
            if not session:
                # If the session doesn't exist, create a new one
                session = await create_chat_session(db, ChatSessionCreate())
                session_id = session.session_id
                logger.info("[21b] Created new session: %s", session_id)
            
        # 1) Actually register the dataset with the session_id
        config = await register_dataset(
            db, 
            dataset.name, 
            dataset.base_url, 
            dataset.table_name,
            session_id  # Pass along the session_id
        )
        
        # 2) Start the background ingestion job
        background_tasks.add_task(fetch_and_store_data, db, config)

        # 3) Return the final data needed by DatasetResponse
        return DatasetResponse(**config)
        
    except Exception as e:
        logger.error("[25] Failed to register dataset: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

#
# 2) GET /datasets -> list all
#
@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """List all registered datasets."""
    logger.info("Listing all datasets")
    try:
        result = await db.execute(text("SELECT * FROM dataset_configs"))
        rows = result.fetchall()
        logger.info("<==ENDPOINT: list_datasets [256]==> Fetched %d datasets", len(rows))

        datasets = []
        for ds in rows:
            ds_dict = dict(ds._mapping)

            # if generated_schema is a string, parse it; if it's already a dict, use it directly
            raw_schema = ds_dict.get('generated_schema')
            if isinstance(raw_schema, str):
                gen_schema = json.loads(raw_schema)
            elif isinstance(raw_schema, dict):
                gen_schema = raw_schema
            else:
                gen_schema = {}

            datasets.append(DatasetResponse(
                id=ds_dict['id'],
                name=ds_dict['name'],
                base_url=ds_dict['base_url'],
                table_name=ds_dict['table_name'],
                geometry_type=ds_dict['geometry_type'],
                display_field=ds_dict['display_field'],
                description=ds_dict['description'],
                schema=gen_schema
            ))

        logger.info("<==ENDPOINT: list_datasets [260]==> datasets: %s", datasets)
        return datasets
    except Exception as e:
        logger.error("Failed to list datasets: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

#
# 3) GET /datasets/{table_name}/data -> read dataset data
#
@router.get("/{table_name}/data")
async def get_dataset_data(table_name: str, db: AsyncSession = Depends(get_db)):
    """Get data for a specific dataset."""
    logger.info("[26] Fetching data for dataset: %s", table_name)
    try:
        config = await get_dataset_config(db, table_name)
        if not config:
            logger.error("[28] Dataset not found: %s", table_name)
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Attempt to read from Redis cache first
        cached_data = redis_client.hgetall(f"{table_name}:all")
        if cached_data:
            logger.info("[30] Returning %d cached records", len(cached_data))
            return [json.loads(val) for val in cached_data.values()]

        # If no cache, read from database
        result = await db.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()

        # Also store them in Redis
        for row in rows:
            row_dict = dict(row)
            redis_client.hset(f"{table_name}:all", str(row_dict['objectid']), json.dumps(row_dict))

        return rows
        
    except Exception as e:
        logger.error("[35] Error fetching dataset data: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/{table_name}/status", response_model=Dict[str, Any])
async def get_dataset_status(table_name: str, db: AsyncSession = Depends(get_db)):
    """Get status information for a specific dataset including record count and last update time."""
    logger.info("<==ENDPOINT: get_dataset_status [36]==> Fetching status for dataset: %s", table_name)
    try:
        # Get dataset configuration
        config = await get_dataset_config(db, table_name)
        if not config:
            logger.error("[37] Dataset not found: %s", table_name)
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get record count from database
        count_result = await db.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
        record_count = count_result.scalar()
        logger.info("<==ENDPOINT: get_dataset_status [39]==> Record count: %d", record_count)
        
        
        ingestion_status = redis_client.get(f"{table_name}:ingestion_status") or b"unknown"
        progress = redis_client.get(f"{table_name}:ingestion_progress") or b"0"
        
        # Get last update time from Redis (if available)
        last_update = redis_client.get(f"{table_name}:last_update")
        
        # Get ingestion status from Redis
        ingestion_status = redis_client.get(f"{table_name}:ingestion_status")
        
        # Get any error messages if ingestion failed
        error_message = redis_client.get(f"{table_name}:ingestion_error")
        
        status_info = {
            "status": ingestion_status if ingestion_status else "unknown",
            "progress":  float(progress) if progress else 0,
            "table_name": table_name,
            "record_count": record_count,
            "last_update": last_update if last_update else None,
            "ingestion_status": ingestion_status if ingestion_status else "unknown",
            "error_message": error_message if error_message else None,
            "geometry_type": config.get("geometry_type"),
            "display_field": config.get("display_field"),
            "description": config.get("description")
        }
        logger.info("<==ENDPOINT: get_dataset_status [40]==> Status info: %s", status_info)
        
        return status_info
        
    except Exception as e:
        logger.error("[38] Error fetching dataset status: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


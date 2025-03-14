from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..schemas.chat import ChatRequest, ChatResponse
from ..db.session import get_db
from ..utils.openai_helper import generate_sql_from_query, generate_response
from ..services.sql_executor import execute_sql_query

router = APIRouter()
logger = logging.getLogger(__name__)

# Simplified schema description for OpenAI
DB_SCHEMA = """
Table: water_mains
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
installation_date TIMESTAMP,             -- Installation date
acquisition VARCHAR(50),                 -- Acquisition type
consultant VARCHAR(250),                 -- Consultant name
ownership VARCHAR(100) DEFAULT 'UNKNOWN', -- Ownership details
bridge_main VARCHAR(1) DEFAULT 'N',       -- Bridge main indicator
bridge_details VARCHAR(250),             -- Details about the bridge
criticality INTEGER DEFAULT -1,          -- Criticality level
rel_cleaning_area VARCHAR(10) DEFAULT '0', -- Cleaning area
rel_cleaning_subarea VARCHAR(10) DEFAULT '0', -- Cleaning subarea
undersized VARCHAR(1) DEFAULT 'N',       -- Undersized indicator
shallow_main VARCHAR(1) DEFAULT 'N',     -- Shallow pipe indicator
condition_score NUMERIC DEFAULT -1,      -- Condition score
oversized VARCHAR(1) DEFAULT 'N',        -- Oversized pipe indicator
cleaned VARCHAR(1) DEFAULT 'N',          -- Cleaned or not
shape_length NUMERIC,                    -- Length of the geometry
geometry GEOMETRY(LineString, 4326),     -- Spatial geometry in WGS84
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Creation timestamp
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Update timestamp
"""

@router.post("/query", response_model=ChatResponse)
async def process_chat_query(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a natural language query, convert to SQL, execute, and return a friendly response.
    """
    try:
        user_query = request.message
        logger.info(f"Received chat query: {user_query}")
        
        # Generate SQL from natural language
        sql_query = generate_sql_from_query(user_query, DB_SCHEMA)
        if not sql_query:
            raise HTTPException(status_code=400, detail="Failed to generate SQL query")
        
        # Execute the SQL query
        query_result = await execute_sql_query(db, sql_query)
        
        # Generate natural language response
        response_text = generate_response(query_result, user_query)
        
        return ChatResponse(
            response=response_text,
            data=query_result
        )
    
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
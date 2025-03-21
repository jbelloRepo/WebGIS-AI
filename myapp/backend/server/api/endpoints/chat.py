from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import re
import json

from ..schemas.chat import (
    ChatRequest, ChatResponse, ChatSessionCreate, 
    ChatSessionResponse, ChatMessageCreate, ChatHistoryResponse
)
from ..db.session import get_db
from ..utils.openai_helper import (
    generate_sql_from_query,
    generate_response,
    generate_map_update_response
)
from ..services.sql_executor import execute_sql_query
from ..services.chat_service import (
    create_chat_session, get_chat_session, create_chat_message, 
    get_chat_history, prepare_chat_history_for_context, extract_metadata_from_response
)

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

@router.post("/session", response_model=ChatSessionResponse)
async def create_new_chat_session(
    session_data: ChatSessionCreate = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session"""
    if session_data is None:
        session_data = ChatSessionCreate()
    
    try:
        session = await create_chat_session(db, session_data)
        return ChatSessionResponse(
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_session_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a session"""
    try:
        session = await get_chat_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        messages = await get_chat_history(db, session_id)
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages
        )
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=ChatResponse)
async def process_chat_query(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user_query = request.message
        session_id = request.session_id
        logger.info(f"Received chat query: {user_query}")
        
        # Create or get chat session
        if not session_id:
            session = await create_chat_session(db, ChatSessionCreate())
            session_id = session.session_id
        else:
            session = await get_chat_session(db, session_id)
            if not session:
                # Create a new session if the provided ID doesn't exist
                session = await create_chat_session(db, ChatSessionCreate())
                session_id = session.session_id
        
        # Get chat history for context
        chat_messages = await get_chat_history(db, session_id)
        chat_history = prepare_chat_history_for_context(chat_messages)
        
        # Save user message
        user_message = ChatMessageCreate(
            session_id=session_id,
            message_type="user",
            content=user_query
        )
        await create_chat_message(db, user_message)
        
        # Check if this is a "show" query for map filtering
        is_show_query = re.search(r'\b(show|display|highlight)\b', user_query.lower()) is not None
        
        # Generate SQL from natural language with chat history context
        sql_query = generate_sql_from_query(user_query, DB_SCHEMA, chat_history)
        if not sql_query:
            raise HTTPException(status_code=400, detail="Failed to generate SQL query")
        
        # Execute the SQL query
        query_result = await execute_sql_query(db, sql_query)
        logger.info(f"Query result type: {type(query_result)}")
        logger.info(f"Query result: {query_result}")
        
        # For show queries, extract object_ids but generate a simpler response
        filter_ids = None
        if is_show_query and "result" in query_result and isinstance(query_result["result"], list):
            # If we have results and the SQL was for a show query, extract IDs for filtering
            result_list = query_result["result"]
            if result_list and isinstance(result_list, list) and len(result_list) > 0:
                if "object_id" in result_list[0]:
                    # Get IDs for filtering map
                    filter_ids = [item["object_id"] for item in result_list if "object_id" in item]
                    
                    # For show queries, we want a simpler response that's tailored to the map view
                    response_text = generate_map_update_response(len(filter_ids), user_query, chat_history)
                else:
                    # Handle case where object_id is not in the results
                    response_text = "I couldn't find any water mains matching your criteria."
            else:
                # Empty result case
                response_text = "I couldn't find any water mains matching your criteria."
        else:
            # For analytical queries, generate a more detailed response from the results
            if "error" in query_result:
                response_text = f"I encountered an error: {query_result['error']}"
            elif "result" in query_result:
                result = query_result["result"]
                if result == "No data found":
                    response_text = "I couldn't find any data matching your criteria."
                else:
                    # Generate a natural language response based on the data
                    response_text = generate_response(query_result, user_query, chat_history)
            else:
                response_text = "I couldn't process your query."

        # Extract and limit the data for the frontend
        data_for_frontend = {}
        if "result" in query_result and isinstance(query_result["result"], list):
            full_result_list = query_result["result"]
            # Limit to first 100 items to avoid overwhelming the frontend
            limited_results = full_result_list[:100]
            data_for_frontend = {
                "results": limited_results,
                "total_count": len(full_result_list)
            }
        
        # Create response object
        response = ChatResponse(
            response=response_text,
            data=data_for_frontend,
            filter_ids=filter_ids,
            is_show_query=is_show_query,
            session_id=session_id
        )
        
        # Save AI message with metadata
        ai_message = ChatMessageCreate(
            session_id=session_id,
            message_type="ai",
            content=response_text,
            message_metadata=extract_metadata_from_response({
                "filter_ids": filter_ids,
                "is_show_query": is_show_query
            })
        )
        await create_chat_message(db, ai_message)
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

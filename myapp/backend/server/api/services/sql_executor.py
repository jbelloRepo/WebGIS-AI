from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def execute_sql_query(db: AsyncSession, sql_query: str) -> Dict[str, Any]:
    """
    Executes a SQL query and returns the results
    
    Args:
        db: The database session
        sql_query: The SQL query to execute
        
    Returns:
        A dictionary with the query results
    """
    try:
        # For safety, we can add a basic SQL injection check here
        forbidden_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER"]
        for keyword in forbidden_keywords:
            if keyword in sql_query.upper():
                logger.warning(f"Potentially harmful SQL detected: {sql_query}")
                return {"error": "This query type is not allowed"}
        
        # Execute the query
        result = await db.execute(text(sql_query))
        rows = result.fetchall()
        
        # Convert to dict format
        if not rows:
            return {"result": "No data found"}
        
        # Get column names
        columns = result.keys()
        
        # Convert to list of dicts
        data = [dict(zip(columns, row)) for row in rows]
        logger.info(f"================================================")
        logger.info(f"Query results:\n{data}")
        logger.info(f"================================================")
        return {"result": data}
    
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        return {"error": str(e)}
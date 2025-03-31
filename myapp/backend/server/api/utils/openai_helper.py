import os
import openai
from openai import OpenAI
from openai import BadRequestError, RateLimitError, APIError, APITimeoutError
from typing import Dict, Any, Optional, List
import logging
import re

logger = logging.getLogger(__name__)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

def generate_sql_from_query(user_query: str, db_schema: str, chat_history: Optional[str] = None) -> str:
    """
    Uses OpenAI to convert a natural language query to SQL
    
    Args:
        user_query: The natural language query from the user
        db_schema: Description of the database schema
        chat_history: Optional string containing previous conversation history
        
    Returns:
        A SQL query string (read-only). If an error or disallowed query, returns an empty string.
    """
    # Check if this is a "show" query for map filtering
    is_show_query = re.search(r'\b(show|display|highlight)\b', user_query.lower()) is not None
    
    # System-level constraints to guide the LLM
    system_prompt = (
        "You are a helpful assistant that converts natural language questions to SQL queries.\n"
        "Constraints:\n"
        "1) Never produce code fences, such as triple backticks (```).\n"
        "2) Never generate destructive SQL queries (e.g., DROP, DELETE, UPDATE, TRUNCATE, ALTER).\n"
        "3) Only return a single valid SQL query. Do not provide explanations or commentary.\n"
        "4) The SQL should be read-only (SELECT statements or similar).\n"
        "5) If Shape__Length is present in the ArcGIS metadata, include it as a DOUBLE PRECISION column in the final schema.\n"
        "6) If Shape__Length exists, always reference it as shape__length (double underscores) — never shape_length.\n"
        "7) Pay attention to SYSTEM messages in the chat history, especially when they describe new datasets.\n"
    )

    # Add chat history to the prompt if available
    history_context = ""
    if chat_history and chat_history.strip():
        history_context = f"""
        Previous conversation history:
        {chat_history}
        
        Take this conversation history into account when generating SQL.
        For example, if the user refers to "those water mains" or similar references, 
        use the context from previous messages to infer what they mean.
        """

    logger.info(f"==History context==: {history_context}")
    # Add system messages to the prompt if available
    # For show queries, modify prompt to only return object_ids
    if is_show_query:
        user_prompt = f"""
        Given the following database schema:
        {db_schema}
        
        {history_context}

        The user wants to visually filter water mains with: "{user_query}"
        Convert this to a SQL query that ONLY returns the object_id column.
        The query must filter the water_mains table based on the request.

        Example: For "show me cast iron pipe", return:
        SELECT object_id FROM water_mains WHERE material = 'CAST IRON'

        Return ONLY the SQL query without any explanation or formatting.
        """
    else:
        # Regular query processing with history
        user_prompt = f"""
        Given the following database schema:
        {db_schema}
        
        {history_context}

        Convert this question to a SQL query: "{user_query}"

        Return ONLY the SQL query without any explanation.
        Return ONLY the SQL without any triple backticks or markdown formatting.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" if GPT-4 is unavailable
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=5000
        )

        # Extract the raw SQL from the response
        raw_sql = response.choices[0].message.content.strip()
        logger.info(f"OpenAI raw response:\n{raw_sql}")

        # Remove any lingering code fences or markdown
        # (Sometimes the model may ignore instructions, so we sanitize here.)
        sanitized_sql = raw_sql.replace("```sql", "").replace("```", "").strip()

        # Optionally, remove line breaks if the model inserts extra whitespace:
        # sanitized_sql = " ".join(sanitized_sql.split())

        # Minimal check for disallowed keywords (further checks can be added)
        disallowed_keywords = ["DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER"]
        if any(keyword in sanitized_sql.upper() for keyword in disallowed_keywords):
            logger.warning("Potentially destructive SQL detected; returning empty string.")
            return ""

        logger.info(f"================================================")
        logger.info(f"Generated SQL query:\n{sanitized_sql}")
        logger.info(f"================================================")
        return sanitized_sql

    except RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded: {str(e)}")
        return ""

    except (APIError, APITimeoutError) as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return ""

    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}")
        return ""


def generate_response(query_result: Dict[str, Any], user_query: str, chat_history: Optional[str] = None) -> str:
    """
    Generates a natural language response based on query results
    
    Args:
        query_result: The result of the SQL query (already executed)
        user_query: The original user query
        chat_history: Optional string containing previous conversation history

    Returns:
        A natural language response explaining the data or any errors.
    """
    try:
        result_str = str(query_result)
        
        # Add chat history context if available
        history_context = ""
        if chat_history and chat_history.strip():
            history_context = f"""
            Previous conversation history:
            {chat_history}
            
            Use this conversation history for context when generating your response.
            If the user is referring to previous questions or topics, maintain that context.
            """

        prompt = f"""
        Given this query result: {result_str}

        And the original question: "{user_query}"
        
        {history_context}

        Generate a friendly and informative response that answers the question.
        Note: If there is a list of any kind, make sure that each item in the list is on a new line.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4 if desired/available
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains data in a friendly way. Do not include any special characters like asterisks (**) in your responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=5000
        )

        friendly_response = response.choices[0].message.content.strip()
        logger.info(f"================================================")
        logger.info(f"\nFriendly response:\n{friendly_response}")
        logger.info(f"================================================")
        return friendly_response

    except RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded during response generation: {str(e)}")
        return "I'm sorry, but I'm currently experiencing heavy load. Please try again."

    except (APIError, APITimeoutError) as e:
        logger.error(f"OpenAI API error during response generation: {str(e)}")
        return "I'm sorry, but I couldn't retrieve the data at this time."

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"I found this result: {query_result}"


def generate_map_update_response(count: int, user_query: str, chat_history: Optional[str] = None) -> str:
    """
    Generates a simpler response for 'show' queries without sending the full list of IDs
    
    Args:
        count: The number of features found
        user_query: The original user query
        chat_history: Optional string containing previous conversation history

    Returns:
        A natural language response about the map update
    """
    try:
        # Add chat history context if available
        history_context = ""
        if chat_history and chat_history.strip():
            history_context = f"""
            Previous conversation history:
            {chat_history}
            
            Use this conversation history for context when generating your response.
            """
            
        prompt = f"""
        The user asked: "{user_query}"
        
        {history_context}
        
        This was a request to filter and display water mains on the map.
        I found {count} water mains matching these criteria.
        
        Create a friendly response that:
        1. Acknowledges the request to show certain water mains
        2. Mentions that {count} features are now being displayed on the map
        3. Suggests the user can click on individual water mains for more details
        4. Keep it concise but friendly
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a GIS application."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150  # Short response is sufficient
        )

        friendly_response = response.choices[0].message.content.strip()
        logger.info(f"Map update response:\n{friendly_response}")
        return friendly_response

    except Exception as e:
        logger.error(f"Error generating map update response: {str(e)}")
        # Fallback response if API call fails
        return f"I've updated the map to show {count} water mains matching your criteria. You can click on any highlighted feature for more details."



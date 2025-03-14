import os
import openai
from openai import OpenAI
from openai import BadRequestError, RateLimitError, APIError, APITimeoutError
from typing import Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

def generate_sql_from_query(user_query: str, db_schema: str) -> str:
    """
    Uses OpenAI to convert a natural language query to SQL
    
    Args:
        user_query: The natural language query from the user
        db_schema: Description of the database schema
        
    Returns:
        A SQL query string (read-only). If an error or disallowed query, returns an empty string.
    """
    # System-level constraints to guide the LLM
    system_prompt = (
        "You are a helpful assistant that converts natural language questions to SQL queries.\n"
        "Constraints:\n"
        "1) Never produce code fences, such as triple backticks (```).\n"
        "2) Never generate destructive SQL queries (e.g., DROP, DELETE, UPDATE, TRUNCATE, ALTER).\n"
        "3) Only return a single valid SQL query. Do not provide explanations or commentary.\n"
        "4) The SQL should be read-only (SELECT statements or similar).\n"
    )

    # User-level prompt: includes the database schema and the user's question
    user_prompt = f"""
    Given the following database schema:
    {db_schema}

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


def generate_response(query_result: Dict[str, Any], user_query: str) -> str:
    """
    Generates a natural language response based on query results
    
    Args:
        query_result: The result of the SQL query (already executed)
        user_query: The original user query

    Returns:
        A natural language response explaining the data or any errors.
    """
    try:
        result_str = str(query_result)

        prompt = f"""
        Given this query result: {result_str}

        And the original question: "{user_query}"

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

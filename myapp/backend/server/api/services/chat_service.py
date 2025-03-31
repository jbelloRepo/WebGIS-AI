from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import json
import logging
from typing import List, Optional, Dict, Any

from ..db.models import ChatSession, ChatMessage
from ..schemas.chat import ChatMessageCreate, ChatSessionCreate

logger = logging.getLogger(__name__)

async def create_chat_session(db: AsyncSession, session_data: ChatSessionCreate) -> ChatSession:
    """Create a new chat session."""
    try:
        new_session = ChatSession(
            user_id=session_data.user_id if session_data.user_id else None
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        await db.rollback()
        raise

async def get_chat_session(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
    """Get a chat session by ID."""
    try:
        result = await db.execute(
            select(ChatSession).filter(ChatSession.session_id == session_id)
        )
        return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        raise

async def create_chat_message(db: AsyncSession, message_data: ChatMessageCreate) -> ChatMessage:
    """Create a new chat message."""
    try:
        new_message = ChatMessage(
            session_id=message_data.session_id,
            message_type=message_data.message_type,
            content=message_data.content,
            message_metadata=message_data.message_metadata
        )
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)
        return new_message
    except Exception as e:
        logger.error(f"Error creating chat message: {str(e)}")
        await db.rollback()
        raise

async def get_chat_history(db: AsyncSession, session_id: str, limit: int = 50) -> List[ChatMessage]:
    """Get chat history for a session."""
    try:
        result = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise

async def get_all_chat_history(db: AsyncSession, limit: int = 500000) -> List[ChatMessage]:
    """Get chat history across all sessions."""
    try:
        result = await db.execute(
            select(ChatMessage)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting all chat history: {str(e)}")
        raise

def prepare_chat_history_for_context(messages: List[ChatMessage]) -> str:
    """
    Format chat messages into a string to provide context for OpenAI.
    Now includes system messages in the context.
    """
    formatted_history = ""
    
    for msg in messages:
        if msg.message_type == "user":
            formatted_history += f"User: {msg.content}\n\n"
        elif msg.message_type == "ai":
            formatted_history += f"Assistant: {msg.content}\n\n"
        elif msg.message_type == "system":
            # Include system messages in the context
            formatted_history += f"{msg.content}\n\n"
    
    logger.info(f"\n [prepare_chat_history_for_context] ==||Formatted chat history ||==: {formatted_history}\n")
    
    return formatted_history

def extract_metadata_from_response(response_data: Dict[str, Any]) -> str:
    """
    Extract and format metadata from the response for storage.
    
    Args:
        response_data: Response data dictionary
        
    Returns:
        JSON string of metadata
    """
    metadata = {
        "filter_ids": response_data.get("filter_ids"),
        "is_show_query": response_data.get("is_show_query", False)
    }
        
    return json.dumps(metadata) 

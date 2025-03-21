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

def prepare_chat_history_for_context(messages: List[ChatMessage]) -> str:
    """
    Format chat history as a string for use in AI context.
    
    Example:
    User: How many water mains are there?
    AI: There are 1,203 water mains in the database.
    """
    if not messages:
        return ""
    
    history = []
    for msg in messages:
        role = "User" if msg.message_type == "user" else "AI"
        history.append(f"{role}: {msg.content}")
    
    return "\n".join(history)

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
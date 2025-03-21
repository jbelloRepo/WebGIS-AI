from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    filter_ids: Optional[List[int]] = None  # For "show" queries
    is_show_query: Optional[bool] = False   # Flag to indicate map filtering
    session_id: Optional[str] = None

class ChatSessionCreate(BaseModel):
    user_id: Optional[str] = None

class ChatSessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime

class ChatMessageBase(BaseModel):
    message_type: str
    content: str
    message_metadata: Optional[str] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: str

class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    session_id: str

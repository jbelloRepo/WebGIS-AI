from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None

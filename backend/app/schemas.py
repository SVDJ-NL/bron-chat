from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    formatted_content: Optional[str] = None
    
    
class ChatDocument(BaseModel):
    id: str
    score: float
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, ChatDocument):
            return False
        return self.id == other.id
        
        
class ChatRequest(BaseModel):
    content: str
    
    
class SessionBase(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    documents: List[ChatDocument] = []
    
    
class SessionBase(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    documents: List[ChatDocument] = []


class SessionCreate(SessionBase):
    pass


class SessionUpdate(SessionBase):
    pass


class Session(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackModel(BaseModel):
    question: str
    name: Optional[str] = None
    email: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        from_attributes = True
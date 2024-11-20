from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "none"

    
class ChatDocument(BaseModel):
    id: str
    score: float
    content: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    feedback_type: Optional[FeedbackType] = None
    feedback_notes: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, ChatDocument):
            return False
        return self.id == other.id
       
       
class ChatMessage(BaseModel):
    role: str
    content: str
    formatted_content: Optional[str] = None
    documents: Optional[List[ChatDocument]] = []
    feedback_type: Optional[FeedbackType] = None
    feedback_notes: Optional[str] = None
     
        
class ChatRequest(BaseModel):
    content: str
    
    
class SessionBase(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    
    
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


class FeedbackBase(BaseModel):
    question: str
    name: Optional[str] = None
    email: Optional[str] = None
    session_id: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackModel(FeedbackBase):
    id: str
    created_at: datetime
    session: Optional[Session] = None

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    feedback_type: FeedbackType
    notes: Optional[str] = None
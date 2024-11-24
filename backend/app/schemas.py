from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"


class DocumentFeedbackBase(BaseModel):
    document_id: int
    feedback_type: Optional[FeedbackType] = None
    notes: Optional[str] = None


class DocumentFeedback(DocumentFeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    
class DocumentBase(BaseModel):
    chunk_id: str
    content: str
    meta: Optional[Dict] = None
    score: float
    title: Optional[str] = None
    url: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatDocument(BaseModel):
    id: Optional[int] = None
    chunk_id: str
    score: float
    content: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    feedback: Optional[DocumentFeedback] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, ChatDocument):
            return False
        return self.id == other.id
    

class MessageFeedbackBase(BaseModel):
    message_id: int
    feedback_type: Optional[FeedbackType] = None
    notes: Optional[str] = None

    
class MessageFeedback(MessageFeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageFeedbackCreate(MessageFeedbackBase):
    pass


class MessageFeedbackUpdate(MessageFeedbackBase):
    pass

       
class ChatMessage(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    formatted_content: Optional[str] = None
    feedback: Optional[MessageFeedback] = None
    documents: Optional[List[ChatDocument]] = []
     
        
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
    id: int
    created_at: datetime
    session: Optional[Session] = None
    question: str
    name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True
        
        
class SessionFeedbackCreateRequest(BaseModel):
    question: str
    name: Optional[str] = None
    email: Optional[str] = None

        
class FeedbackCreate(BaseModel):
    session_id: str
    question: str
    name: Optional[str] = None
    email: Optional[str] = None


class MessageFeedbackTypeRequest(BaseModel):
    feedback_type: FeedbackType


class MessageFeedbackNotesRequest(BaseModel):
    notes: str


class DocumentFeedbackTypeRequest(BaseModel):
    feedback_type: FeedbackType


class DocumentFeedbackNotesRequest(BaseModel):
    notes: str


class DocumentFeedbackCreate(DocumentFeedbackBase):
    pass


class DocumentFeedbackUpdate(DocumentFeedbackBase):
    pass

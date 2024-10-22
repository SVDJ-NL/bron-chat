from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatMessage(BaseModel):
    role: str
    content: str
    
    def to_json(self):
        return self.dict()

class ChatDocument(BaseModel):
    id: str
    score: float
    
    def to_json(self):
        return self.dict()
    
class ChatRequest(BaseModel):
    content: str
    
    def to_json(self):
        return self.dict()

class SessionCreate(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    documents: List[ChatDocument] = []
    
    def to_json(self):
        return self.dict()

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    documents: List[ChatDocument] = []
    
    def to_json(self):
        return self.dict()

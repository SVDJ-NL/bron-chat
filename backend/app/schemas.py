from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    content: str

class SessionCreate(BaseModel):
    name: Optional[str] = None
    messages: List[ChatMessage] = []
    documents: List[Dict] = []

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    documents: Optional[List[Dict]] = None

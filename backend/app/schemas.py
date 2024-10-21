from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    content: str

class SessionCreate(BaseModel):
    name: Optional[str] = None
    messages: List[Dict] = []
    documents: List[Dict] = []

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    messages: Optional[List[Dict]] = None
    documents: Optional[List[Dict]] = None

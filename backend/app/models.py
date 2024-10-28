from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.sql import func
from typing import List
from .database import Base
from .schemas import ChatMessage, ChatDocument


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    messages = Column(JSON)
    documents = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def get_messages(self):
        return [ChatMessage(**msg) for msg in self.messages]
    
    def get_documents(self):
        return [ChatDocument(**doc) for doc in self.documents]

    def set_messages(self, messages: List[ChatMessage]):
        self.messages = [msg.dict() for msg in messages]

    def set_documents(self, documents: List[ChatDocument]):        
        self.documents = [doc.dict() for doc in deduplicate_documents(documents)]

def deduplicate_documents(documents: List[ChatDocument]):
    seen_ids = set()
    unique_documents = []
    
    for doc in documents:
        if doc.id not in seen_ids:
            seen_ids.add(doc.id)
            unique_documents.append(doc)
            
    return unique_documents

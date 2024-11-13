from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from typing import List
from .database import Base
from .schemas import ChatMessage, ChatDocument
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=True)
    question = Column(String(2048))
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="feedback")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    messages = Column(JSON)
    documents = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    feedback = relationship("Feedback", back_populates="session")

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

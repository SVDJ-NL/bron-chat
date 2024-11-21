from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer, Text, Enum, Float, UUID
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class MessageFeedback(Base):
    __tablename__ = "messages_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(100), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    feedback_type = Column(String(10), nullable=True, default=None)
    notes = Column(String(2048), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    message = relationship("Message", back_populates="feedback")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=True)
    question = Column(String(2048))
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="feedback", uselist=False)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    messages = relationship("Message", back_populates="session", order_by="Message.sequence")
    feedback = relationship("Feedback", back_populates="session")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'))
    sequence = Column(Integer)
    role = Column(String(50))
    content = Column(Text)
    formatted_content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")
    documents = relationship(
        "Document",
        secondary="message_documents",
        back_populates="messages",
        overlaps="documents,messages"
    )
    feedback = relationship("MessageFeedback", back_populates="message", uselist=False)
    
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    content = Column(Text)
    meta = Column(JSON)
    score = Column(Float)
    title = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    feedback_type = Column(String(10), nullable=True, default=None)
    feedback_notes = Column(Text, nullable=True)

    messages = relationship(
        "Message", 
        secondary="message_documents",
        back_populates="documents",
        overlaps="documents,messages"
    )

class MessageDocument(Base):
    __tablename__ = "message_documents"

    message_id = Column(String(36), ForeignKey('messages.id'), primary_key=True)
    document_id = Column(String(36), ForeignKey('documents.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

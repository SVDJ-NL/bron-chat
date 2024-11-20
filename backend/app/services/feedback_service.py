from .database_service import DatabaseService
from ..models import Message, Document, FeedbackType
from fastapi import HTTPException
from typing import Optional

class FeedbackService(DatabaseService):
    def __init__(self, db):
        super().__init__(db)

    def set_message_feedback(
        self, 
        message_id: str, 
        feedback_type: FeedbackType, 
        notes: Optional[str] = None
    ):
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message.feedback_type = feedback_type
        message.feedback_notes = notes
        self.db.commit()
        return message

    def set_document_feedback(
        self, 
        document_id: str, 
        feedback_type: FeedbackType, 
        notes: Optional[str] = None
    ):
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document.feedback_type = feedback_type
        document.feedback_notes = notes
        self.db.commit()
        return document
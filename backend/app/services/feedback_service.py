from uuid import UUID
from typing import Optional
from sqlalchemy import select, update, insert
from app.models import MessageFeedback, Feedback
from app.schemas import MessageFeedbackCreate, MessageFeedbackUpdate, FeedbackCreate
from .database_service import DatabaseService
from fastapi import HTTPException


class FeedbackService(DatabaseService):
    def __init__(self, db):
        super().__init__(db)

    def create_message_feedback(self, feedback: MessageFeedbackCreate) -> dict:
        new_message_feedback = MessageFeedback(
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type
        )
        
        self.db.add(new_message_feedback)        
        self.db.commit()        
        self.db.refresh(new_message_feedback)
        
        return new_message_feedback

    def update_message_feedback(
        self,
        feedback: MessageFeedbackUpdate
    ) -> dict:
        db_message_feedback = self.get_message_feedback(feedback.message_id)
        
        if db_message_feedback is None:
            raise HTTPException(status_code=404, detail="Message feedback not found")

        if feedback.feedback_type is not None:
            db_message_feedback.feedback_type = feedback.feedback_type
            
        if feedback.notes is not None:
            db_message_feedback.notes = feedback.notes

        self.db.commit()
        self.db.refresh(db_message_feedback)
        
        return db_message_feedback
    
    def get_message_feedback(self, message_id: UUID) -> dict:        
        return self.db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()

    def get_session_feedback(self, session_id: UUID) -> dict:
        return self.db.query(Feedback).filter(Feedback.session_id == session_id).first()
    
    def create_session_feedback(self, feedback: FeedbackCreate) -> dict:
        session = self.get_session_feedback(feedback.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        new_session_feedback = Feedback(
            session_id=session.id,
            question=feedback.question,
            name=feedback.name,
            email=feedback.email
        )
        
        self.db.add(new_session_feedback)        
        self.db.commit()        
        self.db.refresh(new_session_feedback)
        
        return new_session_feedback

from sqlalchemy.orm import Session, joinedload
from ..models import Feedback, Session
from ..schemas import FeedbackModel
from app.models.feedback import MessageFeedback, FeedbackType
import logging

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(self, feedback: FeedbackModel):
        try:
            db_feedback = Feedback(
                question=feedback.question,
                name=feedback.name,
                email=feedback.email,
                session_id=feedback.session_id,
            )
            
            self.db.add(db_feedback)
            self.db.commit()
            self.db.refresh(db_feedback)
            
            return db_feedback
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            self.db.rollback()
            raise 

    def get_all_feedback(self):
        """
        Retrieve all feedback records from the database with their associated sessions
        """
        try:
            return self.db.query(Feedback)\
                .options(joinedload(Feedback.session))\
                .all()
        except Exception as e:
            logger.error(f"Database error while retrieving feedback: {str(e)}")
            raise Exception("Failed to retrieve feedback records")

    def add_feedback(self, message_id: str, session_id: str, feedback_type: FeedbackType):
        # Remove any existing feedback for this message
        existing_feedback = self.db.query(MessageFeedback).filter(
            MessageFeedback.message_id == message_id,
            MessageFeedback.session_id == session_id
        ).first()
        
        if existing_feedback:
            self.db.delete(existing_feedback)
            
        feedback = MessageFeedback(
            message_id=message_id,
            session_id=session_id,
            feedback_type=feedback_type
        )
        self.db.add(feedback)
        self.db.commit()
        return feedback
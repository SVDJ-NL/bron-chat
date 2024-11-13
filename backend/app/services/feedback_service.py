from sqlalchemy.orm import Session
from ..models import Feedback
from ..schemas import FeedbackModel
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
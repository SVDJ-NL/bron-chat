from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.feedback_service import FeedbackService
from ..schemas import FeedbackRequest
from ..models import FeedbackType

router = APIRouter()

@router.post("/messages/{message_id}/feedback")
def set_message_feedback(
    message_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    feedback_service = FeedbackService(db)
    return feedback_service.set_message_feedback(
        message_id=message_id,
        feedback_type=FeedbackType[feedback.feedback_type.upper()],
        notes=feedback.notes
    )

@router.post("/documents/{document_id}/feedback")
def set_document_feedback(
    document_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    feedback_service = FeedbackService(db)
    return feedback_service.set_document_feedback(
        document_id=document_id,
        feedback_type=FeedbackType[feedback.feedback_type.upper()],
        notes=feedback.notes
    )
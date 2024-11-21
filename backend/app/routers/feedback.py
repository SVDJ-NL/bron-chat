from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from ..database import get_db
from ..services.feedback_service import FeedbackService
from ..schemas import MessageFeedbackTypeRequest, MessageFeedbackNotesRequest, SessionFeedbackCreateRequest
from ..models import FeedbackType
from ..config import settings
from uuid import UUID
from app.schemas import (
    MessageFeedbackTypeRequest, 
    MessageFeedbackNotesRequest,
    MessageFeedbackCreate,
    MessageFeedbackUpdate,
    SessionFeedbackCreateRequest,
    FeedbackCreate
)

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"
    
async def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    return FeedbackService(db)

@router.post(base_api_url + "feedback/messages/type/{message_id}")
async def submit_message_feedback_type(
    message_id: UUID,
    feedback: MessageFeedbackTypeRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    existing_feedback = feedback_service.get_message_feedback(str(message_id))
    
    if existing_feedback:
        return feedback_service.update_message_feedback(
            MessageFeedbackUpdate(
                message_id=str(message_id),
                feedback_type=feedback.feedback_type,
                notes=""
            )
        )
    else:
        return feedback_service.create_message_feedback(
            MessageFeedbackCreate(
                message_id=str(message_id),
                feedback_type=feedback.feedback_type
            )
        )

@router.post(base_api_url + "feedback/messages/notes/{message_id}")
async def submit_message_feedback_notes(
    message_id: UUID,
    feedback: MessageFeedbackNotesRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):    
    return feedback_service.update_message_feedback(        
        MessageFeedbackUpdate(
            message_id=str(message_id),
            notes=feedback.notes
        )
    )

# @router.post(base_api_url + "feedback/documents/{document_id}")
# def set_document_feedback(
#     document_id: str,
#     feedback: DocumentFeedbackRequest,
#     db: Session = Depends(get_db)
# ):
#     try:
#         feedback_type = FeedbackType[feedback.feedback_type.upper()]
#         feedback_service = FeedbackService(db)
#         return feedback_service.set_document_feedback(
#             document_id=document_id,
#             feedback_type=feedback_type,
#             notes=feedback.notes
#         )
#     except KeyError:
#         raise HTTPException(
#             status_code=422,
#             detail=f"Invalid feedback type. Must be one of: {[t.name for t in FeedbackType]}"
        # )
    
@router.post(base_api_url + "feedback/{session_id}")
def create_session_feedback(
    session_id: str,
    feedback: SessionFeedbackCreateRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)    
):
    return feedback_service.create_session_feedback(
        FeedbackCreate(     
            question=feedback.question,
            name=feedback.name,
            email=feedback.email,
            session_id=session_id
        )
    )

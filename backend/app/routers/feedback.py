from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from ..config import settings
from ..schemas import FeedbackModel
from ..database import get_db
from ..services.feedback_service import FeedbackService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"

router = APIRouter()

@router.post(base_api_url + "feedback")
async def submit_feedback(    
    question: str = Query(..., description="The feedback question"),
    name: str = Query(None, description="The feedback name"),
    email: str = Query(None, description="The feedback email"),
    session_id: str = Query(None, description="The session ID"),
    db: Session = Depends(get_db)
):
    try:
        feedback_service = FeedbackService(db)
        feedback_record = feedback_service.create_feedback(
            FeedbackModel(
                question=question, 
                name=name, 
                email=email, 
                session_id=session_id
            )
        )
        
        logger.info(f"Saved feedback with ID: {feedback_record.id}")
        return {"status": "success", "message": "Feedback received", "id": feedback_record.id}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import Session, SessionUpdate, SessionCreate, ChatRequest
from ..services.session_service import SessionService
from ..database import get_db
from ..services.qdrant_service import QdrantService
import logging
from datetime import datetime

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    logger.debug(f"Getting session with id: {session_id}")
    session_service = SessionService(db)
    qdrant_service = QdrantService()
    
    session = session_service.get_session(session_id)
    
    qdrant_documents = []
    if session.documents:
        qdrant_documents = qdrant_service.get_documents_by_ids(session.get_documents())    
    
    messages = []
    if session.messages:
        messages = session.get_messages()
        logger.debug(f"Session messages: {session.messages}")
    
    for message in messages:
        if message.formatted_content:
            message.content = message.formatted_content
                     
    response = {
        "id": session.id,
        "name": session.name,
        "messages": messages,
        "documents": qdrant_documents
    }
    
    return response

@router.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db)):
    session_service = SessionService(db)
    return session_service.update_session(session_id, session)

@router.post("/api/generate_session_name")
async def generate_session_name(request: ChatRequest, db: Session = Depends(get_db)):
    session_service = SessionService(db)
    return session_service.generate_session_name(request.content)

@router.post("/api/new_session")
async def create_session(db: Session = Depends(get_db)):
    now = datetime.now()
    session_service = SessionService(db)
    return session_service.create_session(
        SessionCreate(
            name=f"Sessie {now.strftime('%Y-%m-%d %H:%M')}",
            messages=[], 
            documents=[]
        )
    )

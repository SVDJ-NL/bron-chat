from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import SessionCreate, SessionUpdate, ChatRequest
from ..services.session_service import SessionService
from ..database import get_db

router = APIRouter()

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    session_service = SessionService(db)
    session = session_service.get_session(session_id)
           
    return {
        "id": session.id,
        "name": session.name,
        "messages": session.messages,
        "documents": session.documents
    }

@router.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db)):
    session_service = SessionService(db)
    return session_service.update_session(session_id, session)

@router.post("/api/generate_session_name")
async def generate_session_name(request: ChatRequest, db: Session = Depends(get_db)):
    session_service = SessionService(db)
    return session_service.generate_session_name(request.content)

@router.post("/api/new_session")
async def create_new_session(db: Session = Depends(get_db)):
    session_service = SessionService(db)
    return session_service.create_new_session()

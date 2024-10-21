from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import session_service
from ..schemas import SessionCreate, SessionUpdate, ChatRequest

router = APIRouter()

@router.post("/api/sessions")
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    return session_service.create_session(session, db)

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    return session_service.get_session(session_id, db)

@router.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db)):
    return session_service.update_session(session_id, session, db)

@router.post("/api/generate_session_name")
async def generate_session_name(request: ChatRequest):
    return session_service.generate_session_name(request.content)

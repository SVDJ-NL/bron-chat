import uuid
from ..models import Session
from ..schemas import SessionCreate, SessionUpdate
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException
from datetime import datetime

def create_session(session: SessionCreate, db: DBSession):
    db_session = Session(
        id=str(uuid.uuid4()),
        name=session.name or f"Sessie {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        messages=session.messages,
        documents=session.documents
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return {"session_id": db_session.id}

def get_session(session_id: str, db: DBSession):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

def update_session(session_id: str, session: SessionUpdate, db: DBSession):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.name is not None:
        db_session.name = session.name
    if session.messages is not None:
        db_session.messages = session.messages
    if session.documents is not None:
        db_session.documents = session.documents
    
    db.commit()
    db.refresh(db_session)
    return {"message": "Session updated successfully"}

def generate_session_name(content: str):
    # Implement the logic to generate a session name using Cohere
    pass

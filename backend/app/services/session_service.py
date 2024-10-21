import uuid
from ..models import Session
from ..schemas import SessionCreate, SessionUpdate, ChatMessage
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_session(system_message: str, user_message: str, db: DBSession):
    system_message = {"role": "system", "content": system_message}
    message = {"role": "user", "content": user_message}
    messages = [system_message, message]
    documents = []
        
    db_session = Session(
        id=str(uuid.uuid4()),
        name=f"Sessie {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        messages=messages,
        documents=documents
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

def get_session(session_id: str, db: DBSession):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

def update_session(session_id: str, session: SessionUpdate, db: DBSession):
    # logger.info(f"Updating session: {session}")
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.name is not None:
        db_session.name = session.name
    if session.messages is not None:
        db_session.messages.extend(session.messages)
    if session.documents is not None:            
        db_session.documents.extend([
            {
                'id': doc['id'], 
                'score': doc['score']
            } for doc in session.documents
        ])
    
    db.commit()
    db.refresh(db_session)
    return {"message": "Session updated successfully"}

def generate_session_name(content: str):
    # Implement the logic to generate a session name using Cohere
    pass

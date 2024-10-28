from .database_service import DatabaseService
from ..models import Session as SessionModel
from ..schemas import Session, ChatMessage, ChatDocument, SessionCreate, SessionUpdate
from fastapi import HTTPException
from datetime import datetime
import uuid
import logging  
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

class SessionService(DatabaseService):
    def __init__(self, db):
        super().__init__(db)

    def create_session(self, session_create: SessionCreate) -> SessionModel:
        now = datetime.now()
        db_session = SessionModel(
            id=str(uuid.uuid4()),
            name=session_create.name,
            messages=[msg.dict() for msg in session_create.messages],
            documents=[doc.dict() for doc in session_create.documents],
            created_at=now,
            updated_at=now,
        )
            
        logger.debug(f"Creating new db session with messages: {db_session.messages}")    
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session

    def update_session(self, session_id: str, session_update: SessionUpdate) -> SessionModel:
        db_session = self.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_update.name:
            db_session.name = session_update.name
                    
        if session_update.messages:
            db_session.set_messages(session_update.messages)
            
        if session_update.documents:
            db_session.set_documents(session_update.documents)
            
        db_session.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(db_session)
                
        return db_session

    def get_session(self, session_id: str) -> SessionModel:
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")                
        return db_session

    def delete_session(self, session_id: str):
        db_session = self.get_session(session_id)
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        self.db.delete(db_session)
        self.db.commit()

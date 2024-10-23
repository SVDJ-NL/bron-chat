from .database_service import DatabaseService
from ..models import Session
from ..schemas import SessionCreate, SessionUpdate, ChatMessage
from fastapi import HTTPException
from datetime import datetime
import uuid
import logging  

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionService(DatabaseService):
    def __init__(self, db):
        super().__init__(db)

    def create_new_session(self):
        db_session = Session(
            id=str(uuid.uuid4()),
            name=f"Sessie {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session

    def create_session(self, session: SessionCreate):
        messages = [message.to_json() for message in session.messages]
        documents = [document.to_json() for document in session.documents]
        logger.debug(f"Creating session with messages: {messages}")
        logger.debug(f"Creating session with documents: {documents}")
        db_session = Session(
            id=str(uuid.uuid4()),
            name=session.name or f"Sessie {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            messages = messages,
            documents = documents
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session

    def get_session(self, session_id: str):
        db_session = self.db.query(Session).filter(Session.id == session_id).first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return db_session

    def update_session(self, session_id: str, session: SessionUpdate):
        db_session = self.db.query(Session).filter(Session.id == session_id).first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
            
        if session.name is not None:
            db_session.name = session.name
            
        if session.messages is not None and len(session.messages) > 0:
            messages = [message.to_json() for message in session.messages]
            logger.debug(f"Updating session with messages: {session.messages} with {messages}")
            if db_session.messages is None:
                db_session.messages = []
            db_session.messages = db_session.messages + messages
        
        if session.documents is not None and len(session.documents) > 0:
            documents = [document.to_json() for document in session.documents]
            logger.debug(f"Updating with documents: {session.documents} with {documents}")
            if db_session.documents is None:
                db_session.documents = []
            db_session.documents = db_session.documents + documents
                
        logger.debug(f"Updated session with messages: {db_session.messages}")
        self.db.commit()
        self.db.refresh(db_session)
        return {"message": "Session updated successfully"}

    def generate_session_name(self, content: str):
        # Implement the logic to generate a session name using Cohere
        pass

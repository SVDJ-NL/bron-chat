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
        messages = [message.dict() for message in session.messages]
        documents = [document.dict() for document in session.documents]
        logger.info(f"Creating session with messages: {messages}")
        logger.info(f"Creating session with documents: {documents}")
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
        if session.messages is not None:
            messages = [message.to_json() for message in session.messages]
            logger.info(f"Updating session with messages: {session.messages} with {messages}")
            db_session.messages = messages
        if session.documents is not None:
            documents = [document.to_json() for document in session.documents]
            logger.info(f"Updating session with messages: {session.documents} with {documents}")
            db_session.documents = documents
                
        self.db.commit()
        self.db.refresh(db_session)
        return {"message": "Session updated successfully"}

    def generate_session_name(self, content: str):
        # Implement the logic to generate a session name using Cohere
        pass

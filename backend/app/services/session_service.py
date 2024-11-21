from .database_service import DatabaseService
from ..models import Session, Message, Document, MessageFeedback, MessageDocument
from ..schemas import ChatMessage, ChatDocument
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
            # Clear existing messages
            db_session.messages = []
            self.db.commit()
            
            # Add new messages as proper Message model instances
            for idx, msg in enumerate(session_update.messages):
                new_message = Message(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    sequence=idx,
                    role=msg.role,
                    content=msg.content,
                    formatted_content=msg.formatted_content,
                )
                self.db.add(new_message)
                
                # Handle documents if present
                if msg.documents:
                    for doc_data in msg.documents:
                        # Check if document already exists
                        existing_doc = self.db.query(Document).filter(Document.id == doc_data.id).first()
                        if existing_doc:
                            doc = existing_doc
                        else:
                            doc = Document(
                                id=doc_data.id,
                                content=doc_data.content,
                                score=doc_data.score,
                                title=doc_data.title,
                                url=doc_data.url,
                            )
                            self.db.add(doc)
                        
                        new_message.documents.append(doc)
                        
        db_session.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_session)
                
        return db_session
    
    def get_session(self, session_id: str) -> SessionModel:
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # Ensure the session is attached to the current db session
        self.db.refresh(db_session)
        return db_session

    def delete_session(self, session_id: str):
        db_session = self.get_session(session_id)
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        self.db.delete(db_session)
    
    def get_messages(self, session: Session) -> List[ChatMessage]:
        # Query messages directly instead of accessing relationship
        messages = self.db.query(Message)\
            .filter(Message.session_id == session.id)\
            .outerjoin(MessageFeedback)\
            .order_by(Message.sequence)\
            .all()
        
        return [
            ChatMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                formatted_content=msg.formatted_content,
                feedback=msg.feedback
            ) for msg in messages
        ]
        
    def get_documents(self, session: Session) -> List[ChatDocument]:
        # Query documents directly through message_documents relationship
        documents = self.db.query(Document)\
            .join(MessageDocument)\
            .join(Message)\
            .filter(Message.session_id == session.id)\
            .distinct()\
            .all()
        
        return [
            ChatDocument(
                id=doc.id,
                content=doc.content,
                score=doc.score,
                title=doc.title,
                url=doc.url
            ) for doc in documents
        ]
        
        
    
    def add_message(self, session: Session, message: ChatMessage):
        new_message = Message(
            session_id=session.id,
            sequence=len(session.messages),
            role=message.role,
            content=message.content
        )
        self.db.add(new_message)
        
        if message.documents:
            for doc_data in message.documents:
                existing_doc = self.db.query(Document).filter(Document.id == doc_data.id).first()
                if existing_doc:
                    doc = existing_doc
                else:
                    doc = Document(
                        id=doc_data.id,
                        content=doc_data.content,
                        score=doc_data.score,
                        title=doc_data.title,
                        url=doc_data.url,
                        meta=doc_data.dict(exclude={'id', 'content', 'score', 'title', 'url', 'feedback_type', 'feedback_notes'})
                    )
                    self.db.add(doc)
                
                new_message.documents.append(doc)
        
        self.db.commit()

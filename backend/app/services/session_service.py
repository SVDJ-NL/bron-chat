from .database_service import DatabaseService
from ..models import Session as SessionModel, DocumentFeedback as DocumentFeedbackModel, Message, Document, MessageFeedback as MessageFeedbackModel, MessageDocument
from ..schemas import SessionCreate, SessionUpdate, ChatMessage, ChatDocument, Session, DocumentFeedback, MessageFeedback
from fastapi import HTTPException
from datetime import datetime
import uuid
import logging  
from typing import List
from sqlalchemy.orm import joinedload


# Set up logging
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)

class SessionService(DatabaseService):
    def __init__(self, db):
        super().__init__(db)

    def create_session(self, session_create: SessionCreate) -> SessionModel:
        # Create the session first
        logger.info(f"Creating session with name: {session_create.name} and messages: {session_create.messages}")
        
        new_session = SessionModel(
            id=str(uuid.uuid4()),
            name=session_create.name,
            messages=self._messages_schema_to_db_model(session_create.messages)
        )
        self.db.add(new_session)
        self.db.commit()            
        self.db.refresh(new_session)
        
        return self._session_db_model_to_schema(new_session)

    def update_session_name(self, session_id: str, name: str) -> Session:
        db_session = self._get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        db_session.name = name
        self.db.commit()
        self.db.refresh(db_session)
        
        return self._session_db_model_to_schema(db_session)
           
    def get_session(self, session_id: str) -> Session:
        return self._session_db_model_to_schema(self._get_session(session_id))

    def get_session_with_relations(self, session_id: str) -> Session:
        return self._session_db_model_to_schema(self._get_session_with_relations(session_id))

    def delete_session(self, session_id: str):
        db_session = self._get_session(session_id)
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        self.db.delete(db_session)
    
    def get_messages(self, session: Session) -> List[ChatMessage]:
        # Query messages with feedback relationship eagerly loaded
        messages = self.db.query(Message)\
            .filter(Message.session_id == session.id)\
            .outerjoin(MessageFeedback)\
            .options(joinedload(Message.feedback))\
            .order_by(Message.sequence)\
            .all()
        
        return self._messages_db_model_to_schema(messages)
                
    def get_documents(self, session: Session) -> List[ChatDocument]:
        # Query documents directly through message_documents relationship
        documents = self.db.query(Document)\
            .join(MessageDocument)\
            .join(Message)\
            .outerjoin(Document.feedback)\
            .filter(Message.session_id == session.id)\
            .distinct()\
            .all()
        
        return self._documents_db_model_to_schema(documents)
    
    def add_message(self, session_id: int, message: ChatMessage) -> Session:     
        db_session = self._get_session(session_id)
        db_message = self._message_schema_to_db_model(message, len(db_session.messages))
        db_session.messages.append(db_message)

        self.db.commit()
        self.db.refresh(db_message)        
  
        return self._message_db_model_to_schema(db_message)

    def add_messages(self, session_id: int, messages: List[ChatMessage]) -> Session:
        db_session = self._get_session(session_id)
        db_messages = self._messages_schema_to_db_model(messages)
        db_session.messages.extend(db_messages)
        self.db.commit()
        self.db.refresh(db_session, ['messages'])
        return self._session_db_model_to_schema(db_session)

    def _get_session(self, session_id: str) -> SessionModel:
        db_session = self.db.query(SessionModel)\
            .options(joinedload(SessionModel.messages))\
            .filter(SessionModel.id == session_id)\
            .first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return db_session
    
    def _get_session_with_relations(self, session_id: str) -> SessionModel:
        db_session = self.db.query(SessionModel)\
            .options(
                joinedload(SessionModel.messages).joinedload(Message.feedback),
                joinedload(SessionModel.messages).joinedload(Message.documents).joinedload(Document.feedback),
                joinedload(SessionModel.feedback)
            )\
            .filter(SessionModel.id == session_id)\
            .first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return db_session
    
    # Convert DB models to schemas
    def _session_db_model_to_schema(self, db_session: SessionModel) -> Session:
        return Session(
            id=db_session.id,
            name=db_session.name,
            messages=self._messages_db_model_to_schema(db_session.messages),
        )

    def _messages_db_model_to_schema(self, db_messages: List[Message]) -> List[ChatMessage]:
        return [self._message_db_model_to_schema(msg) for msg in db_messages]
    
    def _documents_db_model_to_schema(self, db_documents: List[Document]) -> List[ChatDocument]:
        return [self._document_db_model_to_schema(doc) for doc in db_documents]
    
    def _document_db_model_to_schema(self, db_document: Document) -> ChatDocument:
        if db_document is None:
            return None
        
        return ChatDocument(
            id=db_document.id,
            chunk_id=db_document.chunk_id,
            content=db_document.content,
            score=db_document.score,
            title=db_document.title,
            url=db_document.url,
            feedback=self._document_feedback_db_model_to_schema(db_document.feedback)
        )
        
    def _document_feedback_db_model_to_schema(self, db_feedback: DocumentFeedbackModel) -> DocumentFeedback:
        if db_feedback is None:
            return None
        
        return DocumentFeedback(
            id=db_feedback.id,
            document_id=db_feedback.document_id,
            created_at=db_feedback.created_at,
            feedback_type=db_feedback.feedback_type,
            notes=db_feedback.notes
        )
        
    def _message_feedback_db_model_to_schema(self, db_feedback: MessageFeedbackModel) -> MessageFeedback:
        if db_feedback is None:
            return None
        
        return MessageFeedback(
            id=db_feedback.id,
            message_id=db_feedback.message_id,
            created_at=db_feedback.created_at,
            feedback_type=db_feedback.feedback_type,
            notes=db_feedback.notes
        )
        
    def _message_db_model_to_schema(self, db_message: Message) -> ChatMessage:
        if db_message is None:
            return None
        
        return ChatMessage(
            id=db_message.id,
            role=db_message.role,
            content=db_message.content,
            formatted_content=db_message.formatted_content,
            feedback=self._message_feedback_db_model_to_schema(db_message.feedback),
            documents=self._documents_db_model_to_schema(db_message.documents)
        )
     
    # Convert schemas to DB models
    def _session_schema_to_db_model(self, session: Session) -> SessionModel:
        if session is None:
            return None
        
        return SessionModel(
            id=session.id,
            name=session.name,
            messages=self._messages_schema_to_db_model(session.messages)
        )

    def _messages_schema_to_db_model(self, messages: List[ChatMessage]) -> List[Message]:
        return [self._message_schema_to_db_model(message, i) for i, message in enumerate(messages)]
    
    def _documents_schema_to_db_model(self, documents: List[ChatDocument]) -> List[Document]:
        return [self._document_schema_to_db_model(document) for document in documents]

    def _message_schema_to_db_model(self, message: ChatMessage, sequence: int) -> Message:
        if message is None:
            return None

        return Message(
            sequence=sequence,
            role=message.role,
            content=message.content,
            formatted_content=message.formatted_content,
            documents=self._documents_schema_to_db_model(message.documents)
        )


    def _document_schema_to_db_model(self, document: ChatDocument) -> Document:
        if document is None:
            return None

        return Document(
            chunk_id=document.chunk_id,
            content=document.content,
            score=document.score,
            title=document.title,
            url=document.url,
        )        
        
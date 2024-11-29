from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas import Session, SessionUpdate, SessionCreate, ChatRequest
from ..services.session_service import SessionService
from ..database import get_db
from ..services.qdrant_service import QdrantService
import logging
from datetime import datetime
from ..config import settings
from ..services.cohere_service import CohereService
from ..services.litellm_service import LiteLLMService

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"

@router.get(base_api_url + "sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    logger.debug(f"Getting session with id: {session_id}")
    session_service = SessionService(db)

    llm_service = None
    # Use the configured LLM service
    if settings.LLM_SERVICE.lower() == "litellm":
        llm_service = LiteLLMService()
    else:
        llm_service = CohereService()
        
    qdrant_service = QdrantService(llm_service)
    
    session = session_service.get_session_with_relations(session_id)    
    documents = []
    for message in session.messages:
        documents.extend(message.documents)
        
    logger.debug(f"Found {len(documents)} documents in MySQL for session {session_id}")
    
    qdrant_documents = qdrant_service.get_documents_by_ids(documents)    
    logger.info(f"Found {len(qdrant_documents)} documents in Qdrant for session {session_id}")
        
    # Remove system messages from the session
    session.messages = [msg for msg in session.messages if msg.role != "system"]
    
    # TODO: Remove this once the frontend is updated to use the formatted_content
    for message in session.messages:
        if message.formatted_content:
            message.content = message.formatted_content
                     
    response = {
        "id": session.id,
        "name": session.name,
        "messages": session.messages,
        "documents": qdrant_documents
    }
    
    return response

@router.post(base_api_url + "new_session")
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

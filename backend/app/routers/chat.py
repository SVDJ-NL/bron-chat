from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import json
from asyncio import sleep
from datetime import datetime
from ..database import get_db
from ..services.chat_service import ChatService
from ..services.session_service import SessionService
from ..services.cohere_service import CohereService
from ..services.litellm_service import LiteLLMService
from ..services.qdrant_service import QdrantService
from ..schemas import Session, ChatMessage, ChatDocument, SessionCreate, SessionUpdate
from ..config import settings
from ..models import FeedbackType
from ..services.feedback_service import FeedbackService
router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"

async def event_generator(session, query, session_service, llm_service, chat_service, qdrant_service):
    full_formatted_content = ""
    full_original_content = ""
    
    try:
        yield 'data: ' + json.dumps({
            "type": "session",
            "session_id": session.id
        }) + "\n\n"
        await sleep(0)
        
        yield 'data: ' + json.dumps({
            "type": "status", 
            "role": "assistant", 
            "content": "Uw verzoek wordt nu verwerkt..."
        }) + "\n\n"
        await sleep(0)
                        
        yield 'data: ' + json.dumps({
            "type": "status", 
            "role": "assistant", 
            "content": "Documenten worden gezocht..."
        }) + "\n\n"
        await sleep(0)
        
        try: 
            relevant_docs = qdrant_service.retrieve_relevant_documents(query)
            logger.debug(f"Relevant documents: {relevant_docs}")
        except Exception as e:
            logger.error(f"Error retrieving relevant documents: {e}")
            raise e
        
        session_documents = session_service.get_documents(session)
        if not session_documents:
            combined_relevant_docs = relevant_docs
        else:
            if isinstance(session_documents[0], ChatDocument):
                combined_relevant_docs = relevant_docs
            else:
                combined_relevant_docs = relevant_docs + session_documents

        reordered_relevant_docs = qdrant_service.reorder_documents_by_publication_date(combined_relevant_docs)
                                
        yield 'data: ' + json.dumps({
            "type": "documents",
            "role": "assistant",
            "documents": reordered_relevant_docs
        }) + "\n\n"
        await sleep(0)
        
        yield 'data: ' + json.dumps({
            "type": "status", 
            "role": "assistant", 
            "content": "Documenten gevonden."
        }) + "\n\n"
        await sleep(0)
        
        yield 'data: ' + json.dumps({
            "type": "status", 
            "role": "assistant", 
            "content": "Bron genereert nu een antwoord op uw vraag..."
        }) + "\n\n"
        await sleep(0)
        
        async for response in chat_service.generate_full_response(session_service.get_messages(session), relevant_docs):
            yield 'data: ' + json.dumps(response) + "\n\n"
            await sleep(0)

            if response["type"] == "full":
                full_formatted_content = response["content"]
                full_original_content = response["content_original"]      

    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        yield 'data: ' + json.dumps({"type": "error", "content": str(e)}) + "\n\n"
        await sleep(0)
    finally:
        # Update the session with the assistant's response
        if full_original_content:
            try:
                if not session.id:
                    chat_name = llm_service.create_chat_session_name(query)
                    yield 'data: ' + json.dumps({"type": "session_name", "content": chat_name}) + "\n\n"
                    await sleep(0)
                else:
                    chat_name = session.name
                                        
                session_service.update_session(
                    session_id=session.id,                        
                    session_update=SessionUpdate(
                        name=chat_name,
                        messages = session_service.get_messages(session) + [
                            ChatMessage(
                                role="assistant",
                                content=full_original_content,
                                formatted_content=full_formatted_content,                                    
                                documents = session_service.get_documents(session) + [
                                    ChatDocument(
                                        id=doc.get('id'),
                                        score=doc.get('score'),
                                        content=doc.get('content', ''),
                                        title=doc.get('title', ''),
                                        url=doc.get('url', '')
                                    )
                                    for doc in reordered_relevant_docs
                                ]   
                            )
                        ],
                    )
                )
                
            except Exception as e:
                logger.error(f"Error updating session: {e}", exc_info=True)
            
        # Send a proper close event with data
        yield 'event: close\n\ndata: {"type": "end"}\n\n'
        await sleep(0)

@router.get(base_api_url + "chat")
async def chat_endpoint(
    query: str = Query(..., description="The chat message content"),
    session_id: str = Query(None, description="The session ID"),
    db: Session = Depends(get_db)
):
    llm_service = None
    if settings.LLM_SERVICE.lower() == "litellm":
        llm_service = LiteLLMService()
    else:
        llm_service = CohereService()
        
    chat_service = ChatService(llm_service)
    qdrant_service = QdrantService(llm_service)    
    session_service = SessionService(db)
    
    # Get or create session
    session = None
    if session_id:
        session = session_service.get_session(session_id)
    
    if not session:
        # Create new session with initial messages
        initial_messages = llm_service.get_initial_messages(query)
        session = session_service.create_session(
            SessionCreate(
                messages=initial_messages,
            )
        )
    else:
        # Add message to existing session
        session_messages = session_service.get_messages(session)
        user_message = llm_service.get_user_message(query)
        session = session_service.update_session(
            session.id,
            SessionUpdate(
                messages=session_messages + [user_message]
            )
        )
        logger.info(f"Using existing session: {session.id}")

    return StreamingResponse(
        event_generator(session, query, session_service, llm_service, chat_service, qdrant_service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

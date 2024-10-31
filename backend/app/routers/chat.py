from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import json
from asyncio import sleep
from ..database import get_db
from ..services.chat_service import ChatService
from ..services.session_service import SessionService
from ..services.cohere_service import CohereService
from ..services.qdrant_service import QdrantService
from ..schemas import Session, ChatMessage, ChatDocument, SessionCreate, SessionUpdate
from datetime import datetime
from ..config import config

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = config.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"

@router.get(base_api_url + "chat")
async def chat_endpoint(
    query: str = Query(..., description="The chat message content"),
    session_id: str = Query(None, description="The session ID"),
    db: Session = Depends(get_db)
):
    chat_service = ChatService()
    qdrant_service = QdrantService()
    cohere_service = CohereService()
    session_service = SessionService(db)
    
    session = session_service.get_session(session_id)        
    user_message = cohere_service.get_user_message(query)    
    session_messages = session.get_messages()
    
    is_new_session = not session_messages or len(session_messages) == 0
    
    if is_new_session:        
        system_message_rag = cohere_service.get_rag_system_message()
        
        session = session_service.update_session(
            session.id, 
            SessionUpdate(
                messages=[system_message_rag, user_message],
            )
        )        
    else:
        session = session_service.update_session(
            session.id, 
            SessionUpdate(
                messages=session_messages + [user_message]
            )
        )
        logger.info(f"Using existing session: {session.id}")

    async def event_generator():
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
            
            session_documents = session.get_documents()
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
            
            async for response in chat_service.generate_full_response(session.get_messages(), relevant_docs):
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
                    if is_new_session:
                        chat_name = cohere_service.create_chat_session_name(user_message)
                        # Always send end and close events
                        yield 'data: ' + json.dumps({"type": "session_name", "content": chat_name}) + "\n\n"
                        await sleep(0)
                    else:
                        chat_name = session.name
                                        
                    session_service.update_session(
                        session_id=session.id,                        
                        session_update=SessionUpdate(
                            name=chat_name,
                            messages = session.get_messages() + [
                                ChatMessage(
                                    role="assistant",
                                    content=full_original_content,
                                    formatted_content=full_formatted_content
                                )
                            ],
                            documents = session.get_documents() + [
                                ChatDocument(
                                    id=doc['id'],
                                    score=doc['score']
                                )
                                for doc in reordered_relevant_docs
                            ]   
                        )
                    )
                    
                except Exception as e:
                    logger.error(f"Error updating session: {e}", exc_info=True)
            
            # Always send end and close events
            yield 'data: ' + json.dumps({"type": "end", "content": "Done."}) + "\n\n"
            await sleep(0)
            yield 'event: close\ndata: \n\n'
            await sleep(0)

    return StreamingResponse(
        content=event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import logging
import json
from asyncio import sleep
from ..database import get_db
from ..services.session_service import SessionService
from ..services.cohere_service import CohereService
from ..services.base_llm_service import BaseLLMService
from ..services.litellm_service import LiteLLMService
from ..services.qdrant_service import QdrantService
from ..schemas import ChatMessage, ChatDocument, SessionCreate, SessionUpdate, Session
from ..config import settings
from typing import List, Dict, AsyncGenerator
from ..text_utils import get_formatted_date_english, format_text

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENVIRONMENT = settings.ENVIRONMENT

base_api_url = "/"
if ENVIRONMENT == "development":
    base_api_url = "/api/"
    
    
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
        
    qdrant_service = QdrantService(llm_service)    
    session_service = SessionService(db)
            
    session = session_service.get_session_with_relations(session_id)
        
    if len(session.messages) == 0:
        # Create new session with initial messages
        is_initial_message = True
        rag_system_message = llm_service.get_rag_system_message()
        user_message = llm_service.get_user_message(query)
        session = session_service.add_messages(
            session_id=session.id,
            messages=[rag_system_message, user_message]
        )
    else:
        is_initial_message = False
        # Add message to existing session
        user_message = llm_service.get_user_message(query)
        session = session_service.add_message(
            session_id=session.id, 
            message=user_message
        )
        logger.info(f"Using existing session: {session.id}")
    
    return StreamingResponse(
        event_generator(session, query, is_initial_message, session_service, llm_service, qdrant_service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

async def event_generator(
    session : Session, 
    query : str, 
    is_initial_message : bool,
    session_service : SessionService, 
    llm_service : BaseLLMService, 
    qdrant_service : QdrantService
):    
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
        
        async for response in generate_full_response(
            llm_service, 
            session_service, 
            session.messages, 
            relevant_docs, 
            is_initial_message, 
            session.id, 
            query
        ):
            yield 'data: ' + json.dumps(response) + "\n\n"
            await sleep(0)
 
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        yield 'data: ' + json.dumps({"type": "error", "content": str(e)}) + "\n\n"
        await sleep(0)
        
    finally:            
        # Send a proper close event with data
        yield 'event: close\n\ndata: {"type": "end"}\n\n'
        await sleep(0)
        
async def generate_full_response(
    llm_service : BaseLLMService, 
    session_service: SessionService, 
    session_messages: List[ChatMessage], 
    relevant_docs: List[Dict], 
    is_initial_message: bool, 
    session_id: str, 
    query: str
):
    logger.debug(f"Generating full response for query: {session_messages[-1].content}")
    full_text = ""
    text_formatted = ""
    citations = []
    
    async for event in generate_response(llm_service, session_messages, relevant_docs):
        if event["type"] == "status":
            yield {
                "type": "status",
                "role": "assistant",
                "content": event["content"],
                "content_original": event["content"],
            }
        elif event["type"] == "text":
            full_text += event["content"]
            yield {
                "type": "partial",
                "role": "assistant",
                "content": event["content"],
            }
        elif event["type"] == "citation":
            citations.append(event["content"])
            text_formatted = format_text(full_text, citations)
            yield {
                "type": "citation",
                "role": "assistant",
                "content": text_formatted,
                "content_original": full_text,
                "citations": citations,
            }
    
    if not full_text:
        yield {
            "type": "status",
            "role": "assistant",
            "content": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "content_original": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "citations": []
        }    
    else:
        if is_initial_message:
            try:
                chat_name = llm_service.create_chat_session_name(query)
                session_service.update_session_name(session_id=session_id, name=chat_name)
            except Exception as e:
                logger.error(f"Error creating session name: {e}", exc_info=True)
             
        try:      
            session_service.add_message(
                session_id=session_id,
                message=ChatMessage(                                
                    role="assistant",
                    content=full_text,
                    formatted_content=text_formatted,                                    
                    documents = [
                        ChatDocument(
                            chunk_id=doc.get('chunk_id'),
                            score=doc.get('score'),
                            content=doc.get('content', ''),
                            title=doc.get('title', ''),
                            url=doc.get('url', '')
                        )
                        for doc in relevant_docs
                    ]   
                )
            )
        except Exception as e:
            logger.error(f"Error updating session: {e}", exc_info=True)
            
        text_formatted = format_text(full_text, citations)    
        session = session_service.get_session_with_relations(session_id)                  
        
        yield {
            "type": "full",
            "session": session.model_dump()
        }
        
async def generate_response(llm_service: BaseLLMService, messages: List[ChatMessage], relevant_docs: List[Dict]) -> AsyncGenerator[Dict, None]:        
    logger.debug(f"Generating response for messages and documents: {messages}")
    
    formatted_docs = [{     
        'id': doc['chunk_id'],   
        "data": {
            "title": doc['data']['title'],
            "snippet": doc['data']['content'],
            "publication date": get_formatted_date_english(
                doc['data']['published']
            ),
            "municipality": doc['data']['location_name'],
            "source": llm_service.get_human_readable_source(
                doc['data']['source']
            ),
            "type": doc['data']['type'],
        }
    } for doc in relevant_docs]
    
    current_citation = None
    first_citation = True
    
    try:
        for event in llm_service.chat_stream(messages, formatted_docs):
            if event:
                if hasattr(event, 'type'):
                    if event.type == "content-delta":
                        if hasattr(event, 'delta') and hasattr(event.delta, 'message') and hasattr(event.delta.message, 'content'):
                            yield {
                                "type": "text",
                                "content": event.delta.message.content.text
                            }
                    elif event.type == 'citation-start':       
                        if first_citation:
                            yield {
                                "type": "status",
                                "content": "De bronnen om deze tekst te onderbouwen worden er nu bij gezocht."
                            }
                            first_citation = False
                        
                        if (hasattr(event, 'delta') and 
                            hasattr(event.delta, 'message') and 
                            hasattr(event.delta.message, 'citations')):
                            
                            document_ids = []
                            if hasattr(event.delta.message.citations, 'sources') and event.delta.message.citations.sources:
                                document_ids = [source.document.get('id') for source in event.delta.message.citations.sources if hasattr(source, 'document')]
                            
                            current_citation = {
                                'start': event.delta.message.citations.start,
                                'end': event.delta.message.citations.end,
                                'text': event.delta.message.citations.text,
                                'document_ids': document_ids
                            }
                    
                    elif event.type == 'citation-end':
                        if current_citation:
                            yield {
                                "type": "citation",
                                "content": current_citation
                            }
                            current_citation = None                    
    except GeneratorExit:
        logger.info("Generator closed by client")
        return
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        raise
    finally:
        logger.info("Exiting generate_response")

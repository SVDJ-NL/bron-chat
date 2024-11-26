from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import json
from asyncio import sleep
from ..database import get_db
from ..services.session_service import SessionService
from ..services.cohere_service import CohereService
from ..services.base_llm_service import BaseLLMService
from ..services.litellm_service import LiteLLMService
from ..services.qdrant_service import QdrantService
from ..schemas import ChatMessage, ChatDocument, SessionCreate, SessionUpdate
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
    
    # Get or create session
    session = None
    if session_id:
        session = session_service.get_session(session_id)
    
    is_initial_session = False
    
    if not session:
        # Create new session with initial messages
        is_initial_session = True
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
        event_generator(session, query, is_initial_session, session_service, llm_service, qdrant_service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

async def event_generator(
    session, 
    query, 
    is_initial_session : bool,
    session_service : SessionService, 
    llm_service : BaseLLMService, 
    qdrant_service : QdrantService
):
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
        
        async for response in generate_full_response(llm_service, session.messages, relevant_docs):
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
                if is_initial_session:
                    chat_name = llm_service.create_chat_session_name(query)
                else:
                    chat_name = session.name
            except Exception as e:
                logger.error(f"Error creating session name: {e}", exc_info=True)
                         
            try:               
                saved_session = session_service.update_session(
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
                                        chunk_id=doc.get('chunk_id'),
                                        score=doc.get('score'),
                                        content=doc.get('content', ''),
                                        title=doc.get('title', ''),
                                        url=doc.get('url', '')
                                    )
                                    for doc in relevant_docs
                                ]   
                            )
                        ],
                    )
                )
                
                logger.debug(f"Saved session: {saved_session}")
                yield 'data: ' + json.dumps({"type": "full_session", "session": saved_session.model_dump()}) + "\n\n"
                await sleep(0)                
                
            except Exception as e:
                logger.error(f"Error updating session: {e}", exc_info=True)
            
        # Send a proper close event with data
        yield 'event: close\n\ndata: {"type": "end"}\n\n'
        await sleep(0)
        
async def generate_full_response(llm_service : BaseLLMService, session_messages: List[ChatMessage], relevant_docs: List[Dict]):
    logger.debug(f"Generating full response for query: {session_messages[-1].content}")
    full_text = ""
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
        # Send the final full message
        text_formatted = format_text(full_text, citations)
        yield {
            "type": "full",
            "role": "assistant",
            "message_id": session_messages[-1].id,
            "content": text_formatted,
            "content_original": full_text,
            "citations": citations,
        }


async def generate_response(llm_service: BaseLLMService, messages: List[ChatMessage], relevant_docs: List[Dict]) -> AsyncGenerator[Dict, None]:        
    logger.debug(f"Generating response for messages and documents: {messages}")
    
    formatted_docs = [{     
            'id': doc['id'],   
            "data": {
                "title": doc['data']['title'],
                "snippet": doc['data']['content'],
                "publication date": get_formatted_date_english(
                    doc['data']['published']
                ),
                "municipality": doc['data']['location_name']
            }
        } for doc in relevant_docs
    ]
    
    current_citation = None
    first_citation = True
    try:
        for event in llm_service.chat_stream(messages, formatted_docs):
            if event:
                if event.type == "content-delta":
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
                        
                    current_citation = {
                        'start': event.delta.message.citations.start,
                        'end': event.delta.message.citations.end,
                        'text': event.delta.message.citations.text,
                        'document_ids': [source.document['id'] for source in event.delta.message.citations.sources]
                    }
                    
                elif event.type == 'citation-end':
                    if current_citation:
                        yield {
                            "type": "citation",
                            "content": current_citation
                        }
                        current_citation = None
    except GeneratorExit:
        logger.info("Generator closed due to GeneratorExit")
        # Handle any cleanup if necessary
    finally:
        # Perform any necessary cleanup here
        logger.info("Exiting generate_response")

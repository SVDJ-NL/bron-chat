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
from ..schemas import SessionCreate, SessionUpdate, ChatMessage

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/api/chat")
async def chat_endpoint(
    content: str = Query(..., description="The chat message content"),
    session_id: str = Query(None, description="The session ID"),
    db: Session = Depends(get_db)
):
    chat_service = ChatService()
    cohere_service = CohereService()
    session_service = SessionService(db)
    
    system_message = {"role": "system", "content": cohere_service.get_system_message() }
    message = {"role": "user", "content": content}
    
    if not session_id or session_id is None or session_id == '' or session_id == 'null':
        session = session_service.create_session(SessionCreate(messages=[system_message, message]))        
    else:
        session = session_service.get_session(session_id)
        session_service.update_session(session.id, SessionUpdate(messages=[system_message, message]))
        logger.info(f"Using existing session: {session.id}")

    async def event_generator():
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
            
            relevant_docs = await chat_service.retrieve_relevant_documents(session)
            logger.info(f"Relevant documents: {relevant_docs}")
            
            session_service.update_session(session.id, SessionUpdate(documents=relevant_docs))
            
            initial_response = await chat_service.generate_initial_response(content, relevant_docs)
            yield 'data: ' + json.dumps(initial_response) + "\n\n"
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
            
            async for response in chat_service.generate_full_response(content, relevant_docs):
                yield 'data: ' + json.dumps(response) + "\n\n"
                await sleep(0)

                # Update the session with the assistant's response
                if response["type"] == "full":
                    session_service.update_session(
                        session_id,
                        SessionUpdate(messages=[ChatMessage(
                            role="assistant",
                            content=response["content"]
                        )])
                    )

        except Exception as e:
            logger.error(f"Error in chat_endpoint: {e}")
            yield 'data: ' + json.dumps({"type": "error", "content": str(e)}) + "\n\n"
            await sleep(0)
        
        finally:
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

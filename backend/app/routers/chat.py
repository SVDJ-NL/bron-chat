from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import json
from asyncio import sleep
from ..database import get_db
from ..services.chat_service import ChatService
from ..services.session_service import SessionService
from ..schemas import SessionCreate, SessionUpdate, ChatMessage

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_data(message):
    yield 'data: ' + json.dumps(message) + "\n\n"
    await sleep(0)

@router.get("/api/chat")
async def chat_endpoint(
    content: str = Query(..., description="The chat message content"),
    session_id: str = Query(None, description="The session ID"),
    db: Session = Depends(get_db)
):
    chat_service = ChatService()
    session_service = SessionService()
    
    if not session_id or session_id is None or session_id == '' or session_id == 'null':
        system_message = {"role": "system", "content": chat_service.get_system_message() }
        message = {"role": "user", "content": content}
        session = session_service.create_session(SessionCreate(messages=[system_message, message]), db)        
    else:
        session = session_service.get_session(session_id, db)          
        system_message = {"role": "system", "content": chat_service.get_system_message() }
        message = {"role": "user", "content": content}
        session_service.update_session(session.id, SessionUpdate(messages=[system_message, message]), db)
        logger.info(f"Using existing session: {session.id}")

    async def event_generator():
        try:
            await send_data({
                "type": "session",
                "session_id": session.id
            })
            
            await send_data({
                "type": "status", 
                "role": "assistant", 
                "content": "Uw verzoek wordt nu verwerkt..."
            })
            
            await send_data({
                "type": "status", 
                "role": "assistant", 
                "content": "Documenten worden gezocht..."
            })
            
            relevant_docs = await chat_service.retrieve_relevant_documents(session)
            logger.info(f"Relevant documents: {relevant_docs}")
            
            session_service.update_session(session.id, SessionUpdate(documents=relevant_docs), db)
            
            initial_response = await chat_service.generate_initial_response(content, relevant_docs)
            await send_data(initial_response)
            
            await send_data({
                "type": "status", 
                "role": "assistant", 
                "content": "Documenten gevonden."
            })
            
            await send_data({
                "type": "status", 
                "role": "assistant", 
                "content": "Bron genereert nu een antwoord op uw vraag..."
            })
            
            async for response in chat_service.generate_full_response(content, relevant_docs):
                await send_data(response)

                # Update the session with the assistant's response
                if response["type"] == "full":
                    session_service.update_session(
                        session_id,
                        SessionUpdate(messages=[ChatMessage(
                            role="assistant",
                            content=response["content"]
                        )]),
                        db
                    )

        except Exception as e:
            logger.error(f"Error in chat_endpoint: {e}")
            await send_data({"type": "error", "content": str(e)})
        
        finally:
            # Always send end and close events
            await send_data({"type": "end", "content": "Done."})
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

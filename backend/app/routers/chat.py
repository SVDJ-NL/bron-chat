from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.chat_service import retrieve_relevant_documents, generate_full_response, generate_initial_response
from ..schemas import ChatRequest, SessionCreate, SessionUpdate
import logging
import json
from asyncio import sleep
from ..services.session_service import create_session, update_session

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
    if not session_id:
        # Create a new session
        new_session = create_session(SessionCreate(messages=[]), db)
        session_id = new_session["session_id"]

    async def event_generator():
        try:
            yield 'data: ' + json.dumps({
                "type": "session",
                "session_id": session_id
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
            
            relevant_docs = await retrieve_relevant_documents(content)                       
            initial_response = await generate_initial_response(content, relevant_docs)
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
            
            # After processing the message, update the session in the database
            update_session(
                session_id,
                SessionUpdate(messages=[{"role": "user", "content": content}]),
                db
            )

            async for response in generate_full_response(content, relevant_docs):
                yield 'data: ' + json.dumps(response) + "\n\n"
                await sleep(0)

                # Update the session with the assistant's response
                if response["type"] == "full":
                    update_session(
                        session_id,
                        SessionUpdate(messages=[{
                            "role": "assistant",
                            "content": response["content_original"],
                            "citations": response["citations"]
                        }]),
                        db
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

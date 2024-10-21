from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.chat_service import retrieve_relevant_documents, generate_full_response, generate_initial_response
from ..schemas import ChatRequest
import logging
import json
from asyncio import sleep

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/api/chat")
async def chat_endpoint(
    content: str = Query(..., description="The chat message content"),
    db: Session = Depends(get_db)
):
    async def event_generator():
        try:
            yield 'data: ' + json.dumps({
                "type": "start", 
                "role": "assistant", 
                "content": "Documenten worden opgehaald..."
                }) + "\n\n"
            await sleep(0)
            
            relevant_docs = await retrieve_relevant_documents(content)            
            
            # Send initial response
            initial_response = await generate_initial_response(content, relevant_docs)
            yield 'data: ' + json.dumps(initial_response) + "\n\n"
            await sleep(0)
                        
            async for response in generate_full_response(content, relevant_docs):
                yield 'data: ' + json.dumps(response) + "\n\n"
                await sleep(0)
            
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

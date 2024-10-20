import os
from typing import List, Dict, AsyncGenerator, Tuple
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qdrant_client
from qdrant_client import QdrantClient
from cohere import ClientV2 as CohereClient
import logging
# from fastembed.sparse import SparseTextEmbedding, SparseEmbedding
from fastembed.text import TextEmbedding
import json
from fastapi.responses import StreamingResponse
import asyncio
from markdown import markdown 
from dotenv import load_dotenv
import locale
from sqlalchemy.orm import Session
from database import get_db, Session as DBSession
import uuid
from datetime import datetime


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,    
    allow_origins=[
        "http://localhost:5173", 
        "http://0.0.0.0:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:8000", 
        "http://0.0.0.0:8000", 
        "http://127.0.0.1:8000", 
        "http://dl:8000",
        "http://bron.ngrok.app", 
        "https://bron.ngrok.app", 
        "http://bron.ngrok.app:5173", 
        "https://bron.ngrok.app:5173", 
        "http://bron.ngrok.app:8000", 
        "https://bron.ngrok.app:8000", 
        "http://bron.ngrok.io", 
        "https://bron.ngrok.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize clients
# qdrant_client = QdrantClient(os.getenv("QDRANT_URL"))
# qdrant_client = QdrantClient(host="host.docker.internal", port=6333)
# cohere_client = CohereClient(api_key=os.getenv("COHERE_API_KEY"))

load_dotenv()

qdrant_host = os.getenv("QDRANT_HOST", "host.docker.internal")
qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
cohere_api_key = os.getenv("COHERE_API_KEY")

# Initialize clients
qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
cohere_client = CohereClient(api_key=cohere_api_key)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    content: str

def format_content(content):
    # Remove leading and trailing whitespace
    content = f'[...] {content} [...]'
    return markdown(content)

async def retrieve_relevant_documents(query: str) -> List[Dict]:  
    logger.info(f"Retrieving relevant documents for query: {query}")
    # Get documents from Qdrant
    qdrant_documents = get_bron_documents_from_qdrant(
        cohere_client=cohere_client,
        query=query, 
        limit=100
    )

    # Check if qdrant_documents is None or empty
    if not qdrant_documents:
        logger.warning("No documents retrieved from Qdrant")
        return []

    # Rerank documents using Cohere
    logger.info(f"Documents: {qdrant_documents[0]}")
    # convert Qdrant ScoredPoint to Cohere RerankDocument
    document_texts = [document.payload['content'] for document in qdrant_documents]
    reranked_documents = cohere_client.rerank(
        query = query,
        documents = document_texts,
        top_n = 20,
        model = 'rerank-multilingual-v3.0',
        return_documents=True
    )
    
    qdrant_documents = [qdrant_documents[result.index] for result in reranked_documents.results]           
      
    logger.info(f"Reranked documents: {qdrant_documents[0]}")  
    
    return [ 
        { 
            'id': f'{doc.id}',                
            'score': doc.score,  
            'data': { 
                'source_id': doc.payload['meta']['source_id'],
                'url': doc.payload['meta']['url'],
                'title': doc.payload['meta']['title'],
                'location': doc.payload['meta']['location'],
                'location_name': doc.payload['meta']['location_name'],
                'modified': doc.payload['meta']['modified'],
                'published': doc.payload['meta']['published'],
                'type': doc.payload['meta']['type'],
                'identifier': doc.payload['meta']['identifier'],
                'url': doc.payload['meta']['url'],
                'source': doc.payload['meta']['source'],                
                'page_number': doc.payload['meta']['page_number'] ,                
                'page_count': doc.payload['meta']['page_count'] ,                
                'content': format_content(doc.payload['content'])
            } 
        } for doc in qdrant_documents 
    ]  
  
models_dir = os.path.join(os.path.dirname(__file__), 'models')

# sparse_document_embedder_0 = SparseTextEmbedding(
#     cache_dir=models_dir,
#     model_name="Qdrant/bm25",
#     providers=[("CUDAExecutionProvider", {"device_id": 0})]
# )

# def generate_sparse_vector(query):
#     logger.info(f"Generating sparse vector for query: {query}")
#     return sparse_document_embedder_0.embed(query)
    
def get_bron_documents_from_qdrant(cohere_client, query, limit=50):   
    logger.info(f"Retrieving documents from Qdrant for query: {query}")
    try:
        # Generate dense embedding
        dense_vector = cohere_client.embed(
            texts=[query], 
            input_type="search_query", 
            model="embed-multilingual-light-v3.0",
            embedding_types=["float"]
        ).embeddings.float[0]
    except Exception as e:
        logger.error(f"Error creating dense vector from query using Cohere: {e}")
        return None
            
    try:
        qdrant_documents = qdrant_client.search(
            query_vector=("text-dense", dense_vector),
            collection_name="1_gemeente_cohere",            
            limit=limit   
        )
        
        if not qdrant_documents:
            logger.warning("No documents found in Qdrant")
        
        return qdrant_documents    
    except Exception as e:
        logger.error(f"Error retrieving documents from Qdrant: {e}")   
        return None

def get_formatted_dutch_date():    
    from datetime import datetime

    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date in Dutch using the locale settings
    try:
        formatted_date = current_datetime.strftime('%A, %d %B %Y %H:%M:%S %Z')
    except:
        logger.warning("Failed to format date using locale. Using default format.")
        formatted_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')

    # Set the locale to Dutch
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date in Dutch using the locale settings
    formatted_date = current_datetime.strftime('%A, %d %B %Y %H:%M:%S %Z')
    
    return formatted_date

def get_system_message():
    formatted_date = get_formatted_dutch_date()
    
    pirate_system_message='''

## Task and Context

You are Command. You are an extremely capable large language model built by Cohere. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. Today’s date is {date}”

## Style Guide

Always answer in Dutch. Formulate your response as an investigative journalist would.

'''
    # Update the pirate_system_message with the formatted date
    pirate_system_message = pirate_system_message.format(date=formatted_date)
    
    return pirate_system_message

async def generate_response(messages: List[ChatMessage], relevant_docs: List[Dict]) -> AsyncGenerator[Dict, None]:
    system_message = ChatMessage(role="system", content=get_system_message())    
    messages = [system_message] + messages
    
    logger.info(f"Generating response for messages and documents: {messages}")
    
    formatted_docs = [{     
            'id': doc['id'],   
            "data": {
                "title": doc['data']['title'],
                "snippet": doc['data']['content']
            }
        } for doc in relevant_docs
    ]
    
    response_stream = cohere_client.chat_stream(
        model="command-r-plus",
        messages=[{"role": msg.role, "content": msg.content} for msg in messages],
        documents=formatted_docs
    )    
    
    current_citation = None
    first_citation = True
    for event in response_stream:   
        if event:
            if event.type == "content-delta":
                yield {
                    "type": "text",
                    "content": event.delta.message.content.text
                }
            elif event.type == 'citation-start':       
                if first_citation:
                    yield {
                        "type": "text",
                        "content": " \n\n<em>De bronnen om deze tekst te onderbouwen worden er nu bij gezocht.</em>"
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

async def generate_initial_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating initial response for query: {query}")
    initial_response = {
        "type": "initial",
        "role": "assistant",
        "documents": relevant_docs,
        "content": "Hier vast de relevante documenten. Bron genereert nu een antwoord op uw vraag...",
        "content_original": "Hier vast de relevante documenten. Bron genereert nu een antwoord op uw vraag..."
    }
    return json.dumps(initial_response) + "\n"

async def generate_full_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating full response for query: {query}")
    full_text = ""
    citations = []
    
    async for event in generate_response([ChatMessage(role="user", content=query)], relevant_docs):
        if event["type"] == "text":
            full_text += event["content"]
            yield json.dumps({
                "type": "partial",
                "role": "assistant",
                "content": event["content"],
            }) + "\n"
            await asyncio.sleep(0)
        elif event["type"] == "citation":
            citations.append(event["content"])
            text_formatted = format_text(full_text, citations)
            yield json.dumps({
                "type": "citation",
                "role": "assistant",
                "content": text_formatted,
                "content_original": full_text,
                "citations": citations,
            }) + "\n"
            await asyncio.sleep(0)
    
    if not full_text:
        full_response = {
            "type": "full",
            "role": "assistant",
            "content": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "content_original": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "citations": []
        }    
        yield json.dumps(full_response) + "\n"
        await asyncio.sleep(0)
    else:
        # Send the final full message
        text_formatted = format_text(full_text, citations)
        yield json.dumps({
            "type": "full",
            "role": "assistant",
            "content": text_formatted,
            "content_original": full_text,
            "citations": citations,
        }) + "\n"
        await asyncio.sleep(0)

def format_text(text, citations):
    text_w_citations = add_citations_to_text(text, citations)    
    html_text = markdown(text_w_citations)  # Change this line
    return html_text

def add_citations_to_text(text, citations):
    citations_list = sorted(citations, key=lambda x: x['start'])
    
    text_w_citations = ""
    last_end = 0
    
    for i, citation in enumerate(citations_list, start=1):
        # Add text before the citation
        text_w_citations += text[last_end:citation['start']]
        
        # Add the citation
        citation_text = text[citation['start']:citation['end']] 
        document_id_list_string = ','.join([f"'{doc_id}'" for doc_id in citation['document_ids']])
        text_w_citations += f'<span class="citation-link" data-document-ids="[{document_id_list_string}]">{citation_text}</span>'                
        last_end = citation['end']
    
    # Add any remaining text after the last citation
    text_w_citations += text[last_end:]    
    
    return text_w_citations

# Try to set the locale, but don't fail if it's not available
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
except locale.Error:
    logger.warning("Failed to set locale to nl_NL.UTF-8. Trying nl_NL.utf8...")
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.utf8')
    except locale.Error:
        logger.warning("Failed to set locale to nl_NL.utf8. Using default locale.")

class SessionCreate(BaseModel):
    name: str = None
    messages: List[Dict] = []
    documents: List[Dict] = []

class SessionUpdate(BaseModel):
    name: str = None
    messages: List[Dict] = None
    documents: List[Dict] = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Received chat request: {request.content}")
    try:
        query = request.content
        
        async def response_generator():
            relevant_docs = await retrieve_relevant_documents(query)
            
            # Send initial response
            initial_response = await generate_initial_response(query, relevant_docs)
            yield initial_response
            await asyncio.sleep(0)  # Ensure the initial response is flushed
            
            # Send full response
            async for response in generate_full_response(query, relevant_docs):
                yield response
        
        return StreamingResponse(
            response_generator(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"}
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"error": "An error occurred while processing your request."}


@app.get("/api/documents")
async def documents_endpoint():
    query = "klimaat almelo"
    relevant_docs = await retrieve_relevant_documents(query)
    return {"documents": relevant_docs}


@app.post("/api/sessions")
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating session: {session}")
    
    try:
        if session.name is None:
            # Generate a default name if none is provided
            default_name = f"Sessie {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            session.name = default_name

        db_session = DBSession(
            id=str(uuid.uuid4()),
            name=session.name,
            messages=session.messages,
            documents=session.documents
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return {"session_id": db_session.id}
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while creating the session")


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, session: SessionUpdate, db: Session = Depends(get_db)):
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.name is not None:
        db_session.name = session.name
    if session.messages is not None:
        db_session.messages = session.messages
    if session.documents is not None:
        db_session.documents = session.documents
    
    db.commit()
    db.refresh(db_session)
    return {"message": "Session updated successfully"}

@app.post("/api/generate_session_name")
async def generate_session_name(request: ChatRequest):
    system_message = "You are an AI assistant tasked with generating a short, catchy name for a chat session based on its content. The name should be concise, relevant, and engaging. Always generate the name in Dutch."
    
    response = cohere_client.chat(
        model="command",
        message=f"Generate a short, catchy name (maximum 5 words) in Dutch for a chat session with the following content: {request.content}",
        temperature=0.7,
        chat_history=[{"role": "system", "message": system_message}]
    )
    
    return {"name": response.text.strip()}




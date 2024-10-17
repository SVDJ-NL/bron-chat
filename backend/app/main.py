import os
from typing import List, Dict
from fastapi import FastAPI
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

    # Rerank documents using Cohere
    if qdrant_documents is not None and len(qdrant_documents) > 0:
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
        
        return qdrant_documents    
    except Exception as e:
        logger.error(f"Error retrieving documents from Qdrant: {e}")   
        return None

async def generate_response(messages: List[ChatMessage], relevant_docs: List[Dict]):    
    
    from datetime import datetime

    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date in Dutch using the locale settings
    try:
        formatted_date = current_datetime.strftime('%A, %d %B %Y %H:%M:%S')
    except:
        logger.warning("Failed to format date using locale. Using default format.")
        formatted_date = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # Set the locale to Dutch
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

    # Get the current date and time
    current_datetime = datetime.now()

    # Format the date in Dutch using the locale settings
    formatted_date = current_datetime.strftime('%A, %d %B %Y %H:%M:%S')

    
    pirate_system_message='''

## Task and Context

You are Command. You are an extremely capable large language model built by Cohere. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. Today’s date is {date}”

## Style Guide

Always answer in Dutch. Formulate your response as an investigative journalist would.

'''
    # Update the pirate_system_message with the formatted date
    pirate_system_message = pirate_system_message.format(date=formatted_date)
    
    system_message = ChatMessage(role="system", content=pirate_system_message)
    messages = [system_message] + messages
    
    logger.info(f"Generating response for messages and documents: {messages}")
    
    formatted_docs = [{     
            'id': doc['id'],   
            "data": {
                "title": doc['data']['title'],
                "snippet": doc['data']['content']  # Limit snippet to 1000 characters
            }
        } for doc in relevant_docs
    ]
    
    response = cohere_client.chat(
        model="command-r-plus",
        messages=[{"role": msg.role, "content": msg.content} for msg in messages],
        documents=formatted_docs
    )
    # logger.info(f"Response: {response}")
    return response

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
    llm_response = await generate_response([ChatMessage(role="user", content=query)], relevant_docs)
    
    if llm_response is None:
        # Handle the case where no valid documents were found
        full_response = {
            "type": "full",
            "role": "assistant",
            "content": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "content_original": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
            "citations": []
        }
    else:
        text = llm_response.message.content[0].text
        citations = llm_response.message.citations
        
        processed_citations = []
        text_formatted = text
        if citations:
            for citation in citations:
                processed_citation = {
                    'start': citation.start,
                    'end': citation.end,
                    'text': citation.text,
                    'document_ids': [source.document['id'] for source in citation.sources]
                }
                processed_citations.append(processed_citation)
        
            text_formatted = format_text(text, processed_citations)

        full_response = {
            "type": "full",
            "role": "assistant",
            "content": text_formatted,
            "content_original": text,
            "citations": processed_citations
        }
    
    return json.dumps(full_response) + "\n"

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
            full_response = await generate_full_response(query, relevant_docs)
            yield full_response
        
        return StreamingResponse(
            response_generator(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"}  # Disable nginx buffering if you're using it
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"error": "An error occurred while processing your request."}

@app.get("/api/documents")
async def documents_endpoint():
    query = "klimaat almelo"
    relevant_docs = await retrieve_relevant_documents(query)
    return {"documents": relevant_docs}

# @app.get("/")
# async def root():
#     return {"message": "Hello Worlds"}

def format_text(text, citations):
    text_w_citations = add_citations_to_text(text, citations)    
    html_text = markdown(text_w_citations)  # Change this line
    return html_text

def add_citations_to_text(text, citations):
    citations_list = sorted(citations, key=lambda x: x['start'])
    
    text_w_citations = ""
    last_end = 0
    footnotes = []
    
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

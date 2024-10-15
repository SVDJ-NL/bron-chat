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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize clients
# qdrant_client = QdrantClient(os.getenv("QDRANT_URL"))
qdrant_client = QdrantClient(host="host.docker.internal", port=6333)
cohere_client = CohereClient(api_key=os.getenv("COHERE_API_KEY"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    content: str

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
            
    return [ 
        { 
            'id': f'{doc.id}',
            'data': { 
                'source_id': doc.payload['meta']['source_id'],
                'url': doc.payload['meta']['url'],
                'title': doc.payload['meta']['title'],
                'location': doc.payload['meta']['location_name'],
                'snippet': doc.payload['content'] 
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
    logger.info(f"Generating response for messages and documents: {messages}")
    system_message = ChatMessage(role="system", content="You are a helpful assistant that can answer questions and help with tasks. You can use the provided documents to answer questions. If you don't know the answer, say so. If you are not sure, say so. If you are not sure, say so. Always answer all questions in the Dutch language.")
    messages = [system_message] + messages
    response = cohere_client.chat(
        model="command-r-plus",
        messages=messages,
        documents=relevant_docs
    )
    logger.info(f"Response: {response}")
    return response

async def generate_initial_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating initial response for query: {query}")
    initial_response = {
        "type": "initial",
        "role": "assistant",
        "documents": relevant_docs,
        "content": "Processing your request. Here are some relevant documents while I generate a response:"
    }
    return json.dumps(initial_response) + "\n"

async def generate_full_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating full response for query: {query}")
    llm_response = await generate_response([ChatMessage(role="user", content=query)], relevant_docs)
    
    text = llm_response.message.content[0].text
    
    logger.info(f"LLM response: {llm_response}")
    
    citations = []
    text_w_citations = text
    if llm_response.message.citations:
        for citation in llm_response.message.citations:
            processed_citation = {
            'start': citation.start,
            'end': citation.end,
            'text': citation.text,
            'document_ids': [source.document.id for source in citation.sources]
        }
        citations.append(processed_citation)
    
        text_w_citations = insert_citations(text, citations)
    
    full_response = {
        "type": "full",
        "role": "assistant",
        "content": text,
        "citations": citations,
        "text_w_citations": text_w_citations
    }
    
    return json.dumps(full_response) + "\n"

@app.post("/chat")
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

@app.get("/documents")
async def documents_endpoint():
    query = "klimaat almelo"
    relevant_docs = await retrieve_relevant_documents(query)
    return {"documents": relevant_docs}

@app.get("/")
async def root():
    return {"message": "Hello World"}

def insert_citations(text, citations):
    citations_list = sorted(citations, key=lambda x: x['start'])
    
    text_w_citations = ""
    last_end = 0
    footnotes = []
    
    for i, citation in enumerate(citations_list, start=1):
        # Add text before the citation
        text_w_citations += text[last_end:citation['start']]
        
        # Add the citation
        citation_text = text[citation['start']:citation['end']]
        text_w_citations += f"*{citation_text}*[^fn{i}]"
        
        # Prepare the footnote
        footnote = f"[^fn{i}]: Sources: "
        footnote += ", ".join(citation['document_ids'][:3])  # Limit to first 3 sources
        if len(citation['document_ids']) > 3:
            footnote += f", and {len(citation['document_ids']) - 3} more"
        footnotes.append(footnote)
        
        last_end = citation['end']
    
    # Add any remaining text after the last citation
    text_w_citations += text[last_end:]
    
    # Add footnotes
    text_w_citations += "\n\n" + "\n".join(footnotes)
    
    return text_w_citations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

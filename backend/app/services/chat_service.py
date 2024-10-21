from ..config import settings
from ..schemas import ChatMessage
import os
from typing import List, Dict, AsyncGenerator, Tuple
from qdrant_client import QdrantClient
from cohere import ClientV2 as CohereClient
from fastapi.responses import StreamingResponse
import asyncio
import json
from markdown import markdown 
import logging
import locale
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_dir = os.path.join(os.path.dirname(__file__), 'models')

qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
cohere_client = CohereClient(api_key=settings.COHERE_API_KEY)

# sparse_document_embedder_0 = SparseTextEmbedding(
#     cache_dir=models_dir,
#     model_name="Qdrant/bm25",
#     providers=[("CUDAExecutionProvider", {"device_id": 0})]
# )

# def generate_sparse_vector(query):
#     logger.info(f"Generating sparse vector for query: {query}")
#     return sparse_document_embedder_0.embed(query)
  

def format_content(content):
    # Remove leading and trailing whitespace
    content = f'[...] {content} [...]'
    return markdown(content)

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
    return {
        "type": "initial",
        "role": "assistant",
        "content": "Hier vast de relevante documenten. Bron genereert nu een antwoord op uw vraag...",
        "content_original": "Hier vast de relevante documenten. Bron genereert nu een antwoord op uw vraag...",
        "documents": relevant_docs
    }

async def generate_full_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating full response for query: {query}")
    full_text = ""
    citations = []
    
    async for event in generate_response([ChatMessage(role="user", content=query)], relevant_docs):
        if event["type"] == "text":
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
            "type": "full",
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
            "content": text_formatted,
            "content_original": full_text,
            "citations": citations,
        }

# Try to set the locale, but don't fail if it's not available
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
except locale.Error:
    logger.warning("Failed to set locale to nl_NL.UTF-8. Trying nl_NL.utf8...")
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.utf8')
    except locale.Error:
        logger.warning("Failed to set locale to nl_NL.utf8. Using default locale.")

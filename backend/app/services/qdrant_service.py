from ..config import settings
from ..schemas import ChatMessage
from ..models import Session
from qdrant_client import QdrantClient
import logging
from typing import List, Dict, AsyncGenerator, Tuple
from markdown import markdown 
import os
from ..services.cohere_service import CohereService
from ..text_utils import format_content

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.cohere_service = CohereService()

    def get_documents_by_ids(self, documents: List):
        document_ids = []
        for doc in documents:
            document_ids.append(doc['id'])
                    
        if not document_ids:
            logger.warning("No valid document IDs found.")
            return []
        
        try:
            qdrant_documents = self.qdrant_client.retrieve(
                collection_name=settings.QDRANT_COLLECTION,
                ids=document_ids,
            )
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")
            return []
                
        return self.prepare_documents_with_scores(qdrant_documents, documents)        

    def get_bron_documents_from_qdrant(self, query, limit=50):   
        logger.info(f"Retrieving documents from Qdrant for query: {query}")

        try:
            # Generate dense embedding using CohereService
            dense_vector = self.cohere_service.generate_dense_embedding(query)
        except Exception as e:
            logger.error(f"Error creating dense vector from query using Cohere: {e}")
            return None
                
        try:
            qdrant_documents = self.qdrant_client.search(
                query_vector=("text-dense", dense_vector),
                collection_name=settings.QDRANT_COLLECTION,            
                limit=limit   
            )
            
            if not qdrant_documents:
                logger.warning("No documents found in Qdrant")
            
            return qdrant_documents    
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")   
            return None

    def retrieve_relevant_documents(self, query: str) -> List[Dict]:          
        logger.info(f"Retrieving relevant documents for query: {query}")
        # Get documents from Qdrant
        qdrant_documents = self.get_bron_documents_from_qdrant(
            query=query, 
            limit=100
        )

        # Check if qdrant_documents is None or empty
        if not qdrant_documents:
            logger.warning("No documents retrieved from Qdrant")
            return []

        # Rerank documents using Cohere
        # logger.info(f"Documents: {qdrant_documents[0]}")
        # convert Qdrant ScoredPoint to Cohere RerankDocument
        document_texts = [document.payload['content'] for document in qdrant_documents]
        reranked_documents = self.cohere_service.rerank_documents(
            query = query,
            documents = document_texts,
        )
        
        qdrant_documents = [qdrant_documents[result.index] for result in reranked_documents.results]        
        # logger.info(f"Reranked documents: {qdrant_documents[0]}")  
        
        return self.prepare_documents(qdrant_documents)
    
    def prepare_documents(self, qdrant_documents):
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
                    'source': doc.payload['meta']['source'],                
                    'page_number': doc.payload['meta']['page_number'],                
                    'page_count': doc.payload['meta']['page_count'],                
                    'content': format_content(doc.payload['content'])
                } 
            } for doc in qdrant_documents 
        ]

    def prepare_documents_with_scores(self, qdrant_documents, documents):
        # Create a dictionary mapping document IDs to their scores
        score_map = {str(doc['id']): doc['score'] for doc in documents}
        
        return [
            {
                'id': f'{doc.id}',  
                'score': score_map.get(doc.id, 0),
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
                    'source': doc.payload['meta']['source'],
                    'page_number': doc.payload['meta']['page_number'],
                    'page_count': doc.payload['meta']['page_count'],
                    'content': format_content(doc.payload['content'])
                }
            } for doc in qdrant_documents 
        ]

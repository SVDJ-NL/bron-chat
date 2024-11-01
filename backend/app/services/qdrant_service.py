from ..config import settings
from ..schemas import ChatMessage
from ..models import Session
from qdrant_client import QdrantClient, models
import logging
from typing import List, Dict, AsyncGenerator, Tuple
from markdown import markdown 
import os
from ..services.cohere_service import CohereService
from ..text_utils import format_content
from fastembed.sparse import SparseTextEmbedding
from qdrant_client.http import models
from ..schemas import ChatDocument
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantService:
    DENSE_VECTORS_NAME = "text-dense"
    SPARSE_VECTORS_NAME = "text-sparse"
    
    def __init__(self):
        self.dense_model_name = settings.COHERE_EMBED_MODEL
        self.sparse_model_name = settings.SPARSE_EMBED_MODEL
        
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.cohere_service = CohereService()        
        self.sparse_document_embedder = SparseTextEmbedding(
            cache_dir=self.models_dir,
            model_name=self.sparse_model_name,
        )

    def generate_sparse_embedding(self, query: str):
        sparse_vectors = self.sparse_document_embedder.query_embed(query)
        return next(iter(sparse_vectors), None)

    def get_documents_by_ids(self, documents: List[ChatDocument]):
        document_ids = []
        for doc in documents:
            document_ids.append(doc.id)
                    
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

    def hybrid_search(self, query):
        logger.debug(f"Retrieving documents from Qdrant for query using hybrid search: {query}")
        
        sparse_vector = self.generate_sparse_embedding(query)
        dense_vector = self.cohere_service.generate_dense_embedding(query)        
        
        try:            
            qdrant_documents = self.qdrant_client.query_points(
                collection_name=settings.QDRANT_COLLECTION,
                prefetch=[
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_vector.indices,
                            values=sparse_vector.values,
                        ),
                        using=self.SPARSE_VECTORS_NAME,
                        filter=None,
                        limit=settings.QDRANT_SPARSE_RETRIEVE_LIMIT
                    ),
                    models.Prefetch(
                        query=dense_vector,
                        using=self.DENSE_VECTORS_NAME,
                        filter=None,
                        limit=settings.QDRANT_DENSE_RETRIEVE_LIMIT
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=settings.QDRANT_HYBRID_RETRIEVE_LIMIT,
                score_threshold=None,
                with_payload=True,
                with_vectors=False,
            ).points
            
            
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")   
            return None
        
        if not qdrant_documents:
            logger.warning("No documents found in Qdrant")
                    
        return qdrant_documents

    def dense_vector_search(self, query):   
        logger.debug(f"Retrieving documents from Qdrant for query: {query}")

        try:
            # Generate dense embedding using CohereService
            dense_vector = self.cohere_service.generate_dense_embedding(query)
        except Exception as e:
            logger.error(f"Error creating dense vector from query using Cohere: {e}")
            return None

        try:
            qdrant_documents = self.qdrant_client.search(
                query_vector=(self.DENSE_VECTORS_NAME, dense_vector),
                collection_name=settings.QDRANT_COLLECTION,            
                limit=settings.QDRANT_DENSE_RETRIEVE_LIMIT   
            )
            
            if not qdrant_documents:
                logger.warning("No documents found in Qdrant")
            
            return qdrant_documents    
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")   
            return None

    def retrieve_relevant_documents(self, query: str) -> List[Dict]:          
        logger.debug(f"Retrieving relevant documents for query: {query}")
        # Get documents from Qdrant
        # qdrant_documents = self.dense_vector_search(
        #     query=query
        # )

        qdrant_documents = self.hybrid_search(query)
        
        # Check if qdrant_documents is None or empty
        if not qdrant_documents:
            logger.warning("No documents retrieved from Qdrant")
            return []

        # Rerank documents using Cohere
        logger.debug(f"Documents: {qdrant_documents[0]}")
        # convert Qdrant ScoredPoint to Cohere RerankDocument
        document_texts = [document.payload['content'] for document in qdrant_documents]
        reranked_documents = self.cohere_service.rerank_documents(
            query = query,
            documents = document_texts,
        )
        
        qdrant_documents = [qdrant_documents[result.index] for result in reranked_documents.results]        
        logger.debug(f"Reranked documents: {qdrant_documents[0]}")  
        
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

    def prepare_documents_with_scores(self, qdrant_documents, documents: List[ChatDocument]):
        # Create a dictionary mapping document IDs to their scores
        score_map = {str(doc.id): doc.score for doc in documents}
        
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

    def reorder_documents_by_publication_date(self, documents: List[Dict]):
        # Filter out ChatDocument instances and convert them to the expected format
        formatted_documents = []
        for doc in documents:
            if isinstance(doc, ChatDocument):
                # Skip ChatDocument instances as they don't contain publication dates
                continue
            formatted_documents.append(doc)
        
        return sorted(formatted_documents, key=lambda x: x['data']['published'], reverse=True)
    
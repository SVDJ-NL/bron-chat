from ..config import settings
from ..schemas import ChatMessage
from ..models import Session
from qdrant_client import QdrantClient, models
import logging
from typing import List, Dict, AsyncGenerator, Tuple
from markdown import markdown 
import os
from ..services.cohere_service import CohereService
from ..services.litellm_service import LiteLLMService
from ..text_utils import format_content
from fastembed.sparse import SparseTextEmbedding
from qdrant_client.http import models
from ..schemas import ChatDocument
import threading
import queue
from contextlib import contextmanager
from datetime import datetime
import time
from typing import Optional
from .qdrant_pool import QdrantConnectionPool
from .base_llm_service import BaseLLMService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantService:
    DENSE_VECTORS_NAME = "text-dense"
    SPARSE_VECTORS_NAME = "text-sparse"
    
    _sparse_document_embedder = None
    _embedder_lock = threading.Lock()
    # Adjust semaphore based on available CPU cores and workers
    # Using (CPU cores * 2) as a good balance for concurrent embeddings
    _query_semaphore = threading.BoundedSemaphore(16)  
    
    # Add batch size control for optimal memory usage
    BATCH_SIZE = 32  # Process embeddings in batches
    
    @classmethod
    def get_sparse_embedder(cls):
        if cls._sparse_document_embedder is None:
            with cls._embedder_lock:
                if cls._sparse_document_embedder is None:
                    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
                    try:
                        # Set num_threads based on CPU cores while leaving room for other operations
                        cls._sparse_document_embedder = SparseTextEmbedding(
                            cache_dir=models_dir,
                            model_name=settings.SPARSE_EMBED_MODEL,
                            num_threads=4  # Half of CPU cores for embedding
                        )
                    except Exception as e:
                        logger.error(f"Failed to initialize sparse embedder: {e}")
                        raise
        return cls._sparse_document_embedder
    
    def __init__(self, llm_service: BaseLLMService):
        self.llm_service = llm_service
        self.dense_model_name = settings.COHERE_EMBED_MODEL
        self.sparse_model_name = settings.SPARSE_EMBED_MODEL
        self.pool = QdrantConnectionPool.get_instance()
        
        
    def generate_sparse_embedding(self, query: str):
        try:
            with self._query_semaphore:
                sparse_vectors = self.get_sparse_embedder().query_embed(query)
                return next(iter(sparse_vectors), None)
        except Exception as e:
            logger.error(f"Error generating sparse embedding: {e}")
            return None

    def get_documents_by_ids(self, documents: List[ChatDocument]):
        document_ids = []
        for doc in documents:
            document_ids.append(doc.id)
                    
        if not document_ids:
            logger.warning("No valid document IDs found.")
            return []
        
        try:
            with self.pool.get_client() as client:
                qdrant_documents = client.retrieve(
                    collection_name=settings.QDRANT_COLLECTION,
                    ids=document_ids,
                )
                return self.prepare_documents_with_scores(qdrant_documents, documents)
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {e}")
            return []

    def hybrid_search(self, query):
        logger.debug(f"Retrieving documents from Qdrant for query using hybrid search: {query}")
        
        sparse_vector = self.generate_sparse_embedding(query)
        dense_vector = self.llm_service.generate_dense_embedding(query)        
        
        try:            
            with self.pool.get_client() as client:
                qdrant_documents = client.query_points(
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
            # Generate dense embeddings
            dense_vector = self.llm_service.generate_dense_embedding(query)
        except Exception as e:
            logger.error(f"Error creating dense vector from query using Cohere: {e}")
            return None

        try:
            qdrant_documents = self.pool.get_client().search(
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
        
        qdrant_documents = self.hybrid_search(query)
        
        # Check if qdrant_documents is None or empty
        if not qdrant_documents:
            logger.warning("No documents retrieved from Qdrant")
            return []

        # Rerank documents using LiteLLM
        logger.debug(f"Documents: {qdrant_documents[0]}")
        document_texts = [document.payload['content'] for document in qdrant_documents]
        reranked_documents = self.llm_service.rerank_documents(
            query = query,
            documents = document_texts,
        )
        
        qdrant_documents = [qdrant_documents[result.index] for result in reranked_documents.results]
        # Response contains results list with document, index, and relevance_score
        # qdrant_documents = [qdrant_documents[result['index']] for result in reranked_response.results]
        logger.debug(f"Reranked documents: {qdrant_documents[0]}")  
        
        return self.prepare_documents(qdrant_documents)
    
    def _get_best_url(self, doc):
        url = ""
        if doc.payload['meta']['doc_url']:
            url = doc.payload['meta']['doc_url']
        elif doc.payload['meta']['url']:
            url = doc.payload['meta']['url'] 
        return url
    
    def _prepare_document_dict(self, doc, score=None):
        """Helper method to prepare a single document dictionary"""
        return {
            'id': f'{doc.id}',  
            'score': score if score is not None else doc.score,
            'data': {
                'source_id': doc.payload['meta']['source_id'],
                'url': self._get_best_url(doc),
                'title': doc.payload['meta']['title'],
                'location': doc.payload['meta']['location'],
                'location_name': doc.payload['meta']['location_name'],
                # 'modified': doc.payload['meta']['modified'],
                'published': doc.payload['meta']['published'],
                'type': doc.payload['meta']['type'],
                'source': doc.payload['meta']['source'],
                # 'page_number': doc.payload['meta']['page_number'],
                # 'page_count': doc.payload['meta']['page_count'],
                'content': format_content(doc.payload['content'])
            }
        }

    def prepare_documents(self, qdrant_documents):
        return [self._prepare_document_dict(doc) for doc in qdrant_documents]

    def prepare_documents_with_scores(self, qdrant_documents, documents: List[ChatDocument]):
        # Create a dictionary mapping document IDs to their scores
        score_map = {str(doc.id): doc.score for doc in documents}
        return [self._prepare_document_dict(doc, score_map.get(doc.id, 0)) 
                for doc in qdrant_documents]

    def reorder_documents_by_publication_date(self, documents: List[Dict]):
        # Filter out ChatDocument instances and convert them to the expected format
        formatted_documents = []
        for doc in documents:
            if isinstance(doc, ChatDocument):
                # Skip ChatDocument instances as they don't contain publication dates
                continue
            formatted_documents.append(doc)
        
        return sorted(formatted_documents, key=lambda x: x['data']['published'], reverse=True)
    
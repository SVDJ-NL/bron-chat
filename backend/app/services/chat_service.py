from ..config import settings
from ..schemas import ChatMessage
from ..models import Session
from typing import List, Dict, AsyncGenerator, Tuple
import logging
from datetime import datetime
from ..services.qdrant_service import QdrantService
from ..services.cohere_service import CohereService
from ..text_utils import to_markdown, format_content

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.qdrant_service = QdrantService()
        self.cohere_service = CohereService()  # Initialize the new service

    def add_citations_to_text(self, text, citations):
        citations_list = sorted(citations, key=lambda x: x['start'])
        
        text_w_citations = ""
        last_end = 0
        
        for citation in citations_list:
            text_w_citations += text[last_end:citation['start']]
            citation_text = text[citation['start']:citation['end']]
            document_id_list_string = ','.join([f"'{doc_id}'" for doc_id in citation['document_ids']])
            text_w_citations += f'<span class="citation-link" data-document-ids="[{document_id_list_string}]">{citation_text}</span>'
            last_end = citation['end']
        
        text_w_citations += text[last_end:]
        
        return text_w_citations

    def format_text(self, text, citations):
        text_w_citations = self.add_citations_to_text(text, citations)    
        html_text = to_markdown(text_w_citations)  # Change this line
        return html_text

    async def retrieve_relevant_documents(self, session: Session) -> List[Dict]:  
        query = session.messages[-1]['content']
        
        logger.info(f"Retrieving relevant documents for query: {query}")
        # Get documents from Qdrant
        qdrant_documents = self.qdrant_service.get_bron_documents_from_qdrant(
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
        reranked_documents = await self.cohere_service.rerank_documents(query, document_texts)  # Updated call
        
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
        
    async def generate_response(self, messages: List[ChatMessage], relevant_docs: List[Dict]) -> AsyncGenerator[Dict, None]:
        
        system_message = ChatMessage(role="system", content=self.cohere_service.get_system_message())    
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
        
        current_citation = None
        first_citation = True
        for event in await self.cohere_service.chat_stream(messages, formatted_docs):
            if event:
                if event.type == "content-delta":
                    yield {
                        "type": "text",
                        "content": event.delta.message.content.text
                    }
                elif event.type == 'citation-start':       
                    if first_citation:
                        yield {
                            "type": "status",
                            "content": "De bronnen om deze tekst te onderbouwen worden er nu bij gezocht."
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

    async def generate_initial_response(self, query: str, relevant_docs: List[Dict]):
        logger.info(f"Generating initial response for query: {query}")
        return {
            "type": "documents",
            "role": "assistant",
            "documents": relevant_docs
        }

    async def generate_full_response(self, query: str, relevant_docs: List[Dict]):
        logger.info(f"Generating full response for query: {query}")
        full_text = ""
        citations = []
        
        async for event in self.generate_response([ChatMessage(role="user", content=query)], relevant_docs):
            if event["type"] == "status":
                yield {
                    "type": "status",
                    "role": "assistant",
                    "content": event["content"],
                    "content_original": event["content"],
                }
            elif event["type"] == "text":
                full_text += event["content"]
                yield {
                    "type": "partial",
                    "role": "assistant",
                    "content": event["content"],
                }
            elif event["type"] == "citation":
                citations.append(event["content"])
                text_formatted = self.format_text(full_text, citations)
                yield {
                    "type": "citation",
                    "role": "assistant",
                    "content": text_formatted,
                    "content_original": full_text,
                    "citations": citations,
                }
        
        if not full_text:
            yield {
                "type": "status",
                "role": "assistant",
                "content": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
                "content_original": "Excuses, ik kon geen relevante informatie vinden om uw vraag te beantwoorden.",
                "citations": []
            }    
        else:
            # Send the final full message
            text_formatted = self.format_text(full_text, citations)
            yield {
                "type": "full",
                "role": "assistant",
                "content": text_formatted,
                "content_original": full_text,
                "citations": citations,
            }

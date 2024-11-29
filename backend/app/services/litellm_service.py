import os
from ..config import settings
from litellm import completion, embedding, rerank
from litellm.exceptions import APIConnectionError, Timeout, APIError
import logging
from ..text_utils import get_formatted_current_date_english, get_formatted_current_year
from ..schemas import ChatMessage
from .base_llm_service import BaseLLMService
from typing import Generator
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiteLLMService(BaseLLMService):    
    def __init__(self):
        os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
        
    def chat_stream(self, messages: list[ChatMessage], documents: list) -> Generator:
        logger.info("Starting chat stream...")
        os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY
        
        try:
            completion_response = completion(
                model="cohere/command-r-plus",
                messages=[{
                    'role': message.role, 
                    'content': message.content
                    } for message in messages
                ],
                documents=documents,
                    stream=True
                )
            
            # Handle the new streaming response format
            for chunk in completion_response:
                if hasattr(chunk, 'delta') and chunk.delta.content:
                    yield chunk.delta.content
                elif hasattr(chunk, 'choices') and chunk.choices:
                    yield chunk.choices[0].delta.content
                    
        except GeneratorExit:
            logger.info("Chat stream generator closed")
            return
        except APIConnectionError as e:
            logger.error(f'Chat stream connection failed: {e}')
            raise
        except Timeout as e:
            logger.error(f'Chat stream request timed out: {e}')
            raise
        except APIError as e:
            logger.error(f'Chat stream API error occurred: {e}')
            raise

    def rerank_documents(self, query: str, documents: list):
        logger.info("Reranking documents...")
        try:
            return rerank(
                query=query,
                documents=documents,
                top_n=20,
                model=f"cohere/{settings.COHERE_RERANK_MODEL}",
                return_documents=True
            )            
        except APIConnectionError as e:
            logger.error(f'Reranking connection failed: {e}')
        except Timeout as e:
            logger.error(f'Reranking request timed out: {e}')
        except APIError as e:
            logger.error(f'Reranking API error occurred: {e}')

    def generate_dense_embedding(self, query: str):
        try:
            embedding_response = embedding(
                input=[query], 
                input_type="search_query", 
                model=f"cohere/{settings.COHERE_EMBED_MODEL}"
            )
                
            return embedding_response.data[0]['embedding']
        except APIConnectionError as e:
            logger.error(f'Embedding connection failed: {e}')
        except Timeout as e:
            logger.error(f'Embedding request timed out: {e}')
        except APIError as e:
            logger.error(f'Embedding API error occurred: {e}')         

    def create_chat_session_name(self, user_message: ChatMessage):      
        system_message = self._get_chat_name_system_message()  
        messages = [system_message, user_message]
        response = None
        
        try:
            response = completion(
                model="cohere/command-r",
                messages=[{
                    'role': message.role, 
                    'content': message.formatted_content
                    } for message in messages
                ],
            )
        except APIConnectionError as e:
            logger.error(f'Chat name connection failed: {e}')
        except Timeout as e:
            logger.error(f'Chat name request timed out: {e}')
        except APIError as e:
            logger.error(f'Chat name API error occurred: {e}') 

        if response:
            name = response.message.content[0].text
            return self._truncate_chat_name(name)
        else:
            return None
        
    def rewrite_query(self, query: str, messages: list[ChatMessage]) -> str:
        logger.info("Rewriting query based on chat history...")
        return query

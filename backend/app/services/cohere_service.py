from ..config import settings
from cohere import ClientV2 as CohereClient
import logging
from ..schemas import ChatMessage
from .base_llm_service import BaseLLMService
from typing import Generator
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CohereService(BaseLLMService):    
    def __init__(self):
        self.client = CohereClient(api_key=settings.COHERE_API_KEY)
        
    def chat_stream(self, messages: list[ChatMessage], documents: list) -> Generator:
        logger.info(f"Starting chat stream with {len(messages)} messages and {len(documents)} documents...")
        try:
            return self.client.chat_stream(
                model="command-r-plus",
                messages=[{
                    'role': message.role, 
                    'content': message.formatted_content
                    } for message in messages
                ],
                documents=documents
            )
        except GeneratorExit:
            logger.info("Chat stream generator closed")
            return
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            raise
        
    def rerank_documents(self, query: str, documents: list):
        logger.info(f"Reranking {len(documents)} documents...")
        return self.client.rerank(
            query=query,
            documents=documents,
            top_n=20,
            model=settings.COHERE_RERANK_MODEL,
            return_documents=True
        )

    def generate_dense_embedding(self, query: str):
        logger.info(f"Generating dense embedding for query: {query}")
        
        if settings.EMBEDDING_QUANTIZATION == "float":
            return self.client.embed(
                texts=[query], 
                input_type="search_query", 
                model=settings.COHERE_EMBED_MODEL,
                embedding_types=["float"]
            ).embeddings.float[0]
        elif settings.EMBEDDING_QUANTIZATION == "uint8":
            return self.client.embed(
                texts=[query], 
                input_type="search_query", 
                model=settings.COHERE_EMBED_MODEL,
                embedding_types=["uint8"]
            ).embeddings.uint8[0]
        else:
            return self.client.embed(
                texts=[query], 
                input_type="search_query", 
                model=settings.COHERE_EMBED_MODEL,
                embedding_types=["float"]
            ).embeddings.float[0]
        
    def create_chat_session_name(self, user_message: ChatMessage):      
        logger.info(f"Creating chat session name for query: {user_message.content}, using rewritten query: {user_message.formatted_content}")
        system_message = self._get_chat_name_system_message()  
        messages = [system_message, user_message]
        
        response = self.client.chat(
            model="command-r",
            messages=[{
                'role': message.role, 
                'content': message.formatted_content
                } for message in messages
            ],
        )
        
        name = response.message.content[0].text
        return self._truncate_chat_name(name)

    def rewrite_query(self, new_message: ChatMessage, messages: list[ChatMessage]) -> str:
        logger.info("Rewriting query based on chat history...")
        
        # Filter out system messages and get last few messages for context
        # Get up to last 6 messages, but works with fewer messages too
        chat_history = [msg for msg in messages if msg.role != "system"][-6:]
        
        system_message = ChatMessage(
            role="system",
            content=self.QUERY_REWRITE_SYSTEM_MESSAGE
        )
        
        # Format chat history and new query
        history_context = "\n".join([
            f"{msg.role}: {msg.formatted_content}" for msg in chat_history
        ])
        user_message = ChatMessage(
            role="user",
            content=f"""Chat history:
            {history_context}
            
            New query: {new_message.content}
            
            Rewrite this query to include relevant context from the chat history."""
        )
        
        try:
            response = self.client.chat(
                model="command-r",
                messages=[{
                    'role': msg.role,
                    'content': msg.content
                } for msg in [system_message, user_message]],
                temperature=0.1
            )
            
            rewritten_query = response.message.content[0].text
            logger.info(f"Original query: {new_message.content}")
            logger.info(f"Rewritten query: {rewritten_query}")
            return rewritten_query
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return new_message.content  # Fall back to original query if rewriting fails


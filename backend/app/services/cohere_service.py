from ..config import settings
from cohere import ClientV2 as CohereClient
import logging
from ..text_utils import get_formatted_current_date_english
from ..schemas import ChatMessage
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CohereService:
    RAG_SYSTEM_MESSAGE='''

## Task and Context

You are Command. You are an extremely capable large language model built by Cohere. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. Today’s date is {date}”

## Style Guide

Always answer in Dutch. Formulate your answers in the style of a journalist, and when making factual statements, always cite your sources.

'''

    CHAT_NAME_SYSTEM_MESSAGE='''

## Task and Context

You are Command. You are an extremely capable large language model built by Cohere. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with a query. Your job is to turn this query into a title for a AI chatbot session.”

## Style Guide

Always create a short and descriptive title in Dutch. Don't use any special characters or punctuation.

'''
    
    def __init__(self):
        self.client = CohereClient(api_key=settings.COHERE_API_KEY)
        
    def chat_stream(self, messages: list, documents: list):
        logger.info("Starting chat stream...")
        return self.client.chat_stream(
            model="command-r-plus",
            messages=[{
                'role': message.role, 
                'content': message.content
                } for message in messages
            ],
            documents=documents
        )

    def rerank_documents(self, query: str, documents: list):
        logger.info("Reranking documents...")
        return self.client.rerank(
            query=query,
            documents=documents,
            top_n=20,
            model=settings.COHERE_RERANK_MODEL,
            return_documents=True
        )

    def generate_dense_embedding(self, query: str):
        return self.client.embed(
            texts=[query], 
            input_type="search_query", 
            model=settings.COHERE_EMBED_MODEL,
            embedding_types=["float"]
        ).embeddings.float[0]
        
    def get_rag_system_message(self):
        formatted_date = get_formatted_current_date_english()                
        
        return ChatMessage(
            role="system", 
            content=self.RAG_SYSTEM_MESSAGE.format(date=formatted_date) 
        )
        
    def get_chat_name_system_message(self):
        return ChatMessage(
            role="system", 
            content=self.CHAT_NAME_SYSTEM_MESSAGE
        )

    def get_user_message(self, content: str):
        return ChatMessage(
            role="user",
            content=content
        )        

    def create_chat_session_name(self, message: ChatMessage):      
        system_message = self.get_chat_name_system_message()  
        messages = [system_message, message]
        
        response = self.client.chat(
            model="command-r",
            messages=[{
                'role': message.role, 
                'content': message.content
                } for message in messages
            ],
        )
        
        return response.message.content[0].text
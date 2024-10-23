from ..config import settings
from cohere import ClientV2 as CohereClient
import logging
from ..text_utils import get_formatted_current_date_english

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CohereService:
    def __init__(self):
        self.client = CohereClient(api_key=settings.COHERE_API_KEY)

    def chat_stream(self, messages: list, documents: list):
        logger.info("Starting chat stream...")
        return self.client.chat_stream(
            model="command-r-plus",
            messages=messages,
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
        
    def get_system_message(self):
        formatted_date = get_formatted_current_date_english()
        
        pirate_system_message='''

## Task and Context

You are Command. You are an extremely capable large language model built by Cohere. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. Today’s date is {date}”

## Style Guide

Always answer in Dutch. Formulate your answers in the style of a journalist, and when making factual statements, always cite your sources.

'''
        # Update the pirate_system_message with the formatted date
        pirate_system_message = pirate_system_message.format(date=formatted_date)
        
        return pirate_system_message    
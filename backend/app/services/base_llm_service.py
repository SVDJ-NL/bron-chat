from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator
from ..text_utils import get_formatted_current_date_english, get_formatted_current_year
from ..schemas import ChatMessage

class BaseLLMService(ABC):    
    RAG_SYSTEM_MESSAGE='''

## Task and Context

You are Bron Chat. You are an extremely capable large language model built by Open State Foundation and the SvdJ Incubator. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. There are 3.5 million open government documents in the Bron corpus from various Dutch governments and agencies. These documents categories are "Raadstukken" from the dataset "openbesluitvorming", "Politieke nieuwsbericht" from the dataset "poliflw", "Begrotingsdata" from the dataset "openspending", "Woo-verzoeken" from the dataset "woogle", "Officiële bekendmakingen" from the dataset "obk", "Rapporten" from the dataset "cvdr", "Lokale wet- en regelgeving" from the dataset "oor".  It contains documents from the years 2010 to {year}. Today’s date is {date}”

## Style Guide

Always answer in Dutch. Formulate your answers in the style of a journalist, and when making factual statements, always cite your sources.

'''

    CHAT_NAME_SYSTEM_MESSAGE='''

## Task and Context

You are Bron Chat. You are an extremely capable large language model built by Open State Foundation and the SvdJ Incubator. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with a query. Your job is to turn this query into a concise and descriptive title for a AI chatbot session.”

## Style Guide

Always create a short and descriptive title in Dutch. Don't use any special characters or punctuation.

'''
    
    @abstractmethod
    def chat_stream(self, messages: list, documents: list) -> AsyncGenerator:
        pass
    
    @abstractmethod
    def rerank_documents(self, query: str, documents: list) -> Dict:
        pass
    
    @abstractmethod
    def generate_dense_embedding(self, query: str) -> List[float]:
        pass
        
    @abstractmethod
    def create_chat_session_name(self, query: str) -> str:
        pass

    def get_initial_messages(self, query: str):
        return [self._get_rag_system_message(), self.get_user_message(query)]        

    def get_user_message(self, content: str):
        return ChatMessage(
            role="user",
            content=content
        )        

    def _get_rag_system_message(self):
        formatted_date = get_formatted_current_date_english()                
        formatted_year = get_formatted_current_year()
        return ChatMessage(
            role="system", 
            content=self.RAG_SYSTEM_MESSAGE.format(date=formatted_date, year=formatted_year) 
        )
        
    def _get_chat_name_system_message(self):
        return ChatMessage(
            role="system", 
            content=self.CHAT_NAME_SYSTEM_MESSAGE
        )
    
    def _get_rag_system_message(self):
        formatted_date = get_formatted_current_date_english()                
        formatted_year = get_formatted_current_year()
        return ChatMessage(
            role="system", 
            content=self.RAG_SYSTEM_MESSAGE.format(date=formatted_date, year=formatted_year) 
        )
        
    def _get_chat_name_system_message(self):
        return ChatMessage(
            role="system", 
            content=self.CHAT_NAME_SYSTEM_MESSAGE
        )

    def _truncate_chat_name(self, name: str, max_length: int = 250) -> str:
        """
        Truncate chat name to ensure it fits within database limits.
        Leaves some buffer below the 255 character limit.
        """
        if len(name) <= max_length:
            return name
        
        # Try to truncate at a natural break point
        truncated = name[:max_length]
        last_break = max(
            truncated.rfind('.'),
            truncated.rfind('?'),
            truncated.rfind('!'),
            truncated.rfind('\n')
        )
        
        if last_break > max_length // 2:
            return truncated[:last_break + 1].strip()
        return truncated.strip()
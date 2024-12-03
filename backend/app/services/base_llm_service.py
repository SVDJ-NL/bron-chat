from abc import ABC, abstractmethod
from typing import List, Dict, Generator
from ..text_utils import get_formatted_current_date_english, get_formatted_current_year
from ..schemas import ChatMessage, MessageRole, MessageType

class BaseLLMService(ABC):    
    RAG_SYSTEM_MESSAGE='''

## Task and Context

You are Bron Chat. You are an extremely capable large language model built by Open State Foundation and the SvdJ Incubator. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with government documents and asked to answer questions based on these documents. There are 3.5 million open government documents in the Bron corpus from various Dutch government agencies and organizations. These documents categories are "Raadstukken" from the dataset "openbesluitvorming", "Politieke nieuwsbericht" from the dataset "poliflw", "Begrotingsdata" from the dataset "openspending", "Woo-verzoeken" from the dataset "woogle", "Officiële bekendmakingen" from the dataset "obk", "Rapporten" from the dataset "cvdr", "Lokale wet- en regelgeving" from the dataset "oor".  It contains documents from the years 2010 to {year}. Today’s date is {date}”

## Style Guide

1. Always answer in Dutch. 
2. When generating a list, always add two new lines before the start of the list.
3. Formulate your answers in the style of a journalist.
4. When making factual statements, always cite the source document(s) that provided the information.
5. If the answer is not specifically found in the context, prefer to answer "Ik heb het antwoord niet kunnen vinden." instead of guessing.
6. When asked about the present, or time sensitive information, be sure to qualify your answer with the publication date of the latest relevant document, and state that you cannot provide information about events after the publication date of retrieved the document(s).
7. Review the latest publication date of the retrieved documents and state that this is the latest date of the retrieved documents in your answer.

'''
# 7. If you cannot find any documents supporting a factual answer of the question, suggest that the user review the Bron Gids which suggests resources and organizations that might be able to help.


    CHAT_NAME_SYSTEM_MESSAGE='''

## Task and Context

You are Bron Chat. You are an extremely capable large language model built by Open State Foundation and the SvdJ Incubator. You are given instructions programmatically via an API that you follow to the best of your ability. Your users are journalists and researchers based in the Netherlands. You will be provided with a query. Your job is to turn this query into a concise and descriptive title for a AI chatbot session.”

## Style Guide

Always create a short and descriptive title of five words or less in Dutch. Don't use any special characters or punctuation.

'''

    QUERY_REWRITE_SYSTEM_MESSAGE = '''
    
## Task and Context

You are a search query rewriter. Your task is to enhance the user query for searching a vector database of Dutch government documents using hybrid vector and BM25 retrieval.

## Instructions

1. Maintain the original intent of the latest query
2. Keep the rewritten query concise and focused
3. Write the query in Dutch
4. Only output the rewritten query, no explanations or additional text
5. Keep any text formatting instructions from the original query

## Examples

### Example 1

Query: "Wat zijn de regels voor zonnepanelen?"
Rewritten query: "regels zonnepanelen"

### Example 2

Query: "Ik ben op zoek naar documenten over klimaatbeleid in gemeente Amsterdam"
Rewritten query: "klimaatbeleid gemeente amsterdam"

### Example 3

Query: "Ik ben op zoek naar rapporten over klimaatbeleid in gemeente Amsterdam"
Rewritten query: "rapport klimaatbeleid gemeente amsterdam"

'''

    QUERY_REWRITE_SYSTEM_MESSAGE_WITH_HISTORY = '''
    
## Task and Context

You are a search query rewriter. Your task is to enhance the user's new query by incorporating relevant context from the previous user queries. The enhanced query will be used to search a database of Dutch government documents using hybrid vector and BM25 retrieval.

## Instructions

1. Analyze the conversation history to understand the full context
2. Focus on the user's latest query
3. Add essential context from previous messages that could improve search results
4. Focus on local context, such as municipalities, provinces, ministries, etc. and time context, such as years
5. Maintain the original intent of the latest query
6. Keep the rewritten query concise and focused
7. Write the query in Dutch
8. Only output the rewritten query, no explanations or additional text

## Example

Conversation:
User query 1: "Wat zijn de regels voor zonnepanelen?"
New query: "En wat kost de vergunning?"
Rewritten query: "kosten vergunning zonnepanelen gemeente"

'''

    HUMAN_READABLE_SOURCES = {
        "openbesluitvorming": "Raadstuk",
        "poliflw": "Politiek nieuwsbericht",
        "openspending": "Begrotingsdata",
        "woogle": "Woo-verzoek",
        "obk": "Officiële bekendmaking",
        "cvdr": "Rapport",
        "oor": "Lokale wet- en regelgeving",
    }

    @abstractmethod
    def chat_stream(self, messages: list[ChatMessage], documents: list) -> Generator:
        pass
    
    @abstractmethod
    def rerank_documents(self, query: str, documents: list, top_n: int = 20, return_documents: bool = True) -> Dict:
        pass
    
    @abstractmethod
    def generate_dense_embedding(self, query: str) -> List[float]:
        pass
        
    @abstractmethod
    def create_chat_session_name(self, user_message: ChatMessage) -> str:
        pass   

    @abstractmethod
    def rewrite_query(self, query: str) -> str:
        pass

    @abstractmethod
    def rewrite_query_with_history(self, query: str, messages: list[ChatMessage]) -> str:
        pass

    def get_human_readable_source(self, source: str) -> str: 
        return self.HUMAN_READABLE_SOURCES.get(source, source)

    def get_user_message(self, content: str):
        return ChatMessage(
            role=MessageRole.USER,
            message_type=MessageType.USER_MESSAGE,
            content=content,
        )        

    def get_rag_system_message(self):
        formatted_date = get_formatted_current_date_english()                
        formatted_year = get_formatted_current_year()
        return ChatMessage(
            role=MessageRole.SYSTEM, 
            message_type=MessageType.SYSTEM_MESSAGE,
            content=self.RAG_SYSTEM_MESSAGE.format(date=formatted_date, year=formatted_year) 
        )
        
    def _get_chat_name_system_message(self):
        return ChatMessage(
            role=MessageRole.SYSTEM, 
            message_type=MessageType.SYSTEM_MESSAGE,
            content=self.CHAT_NAME_SYSTEM_MESSAGE
        )
            
    def _get_chat_name_system_message(self):
        return ChatMessage(
            role=MessageRole.SYSTEM, 
            message_type=MessageType.SYSTEM_MESSAGE,
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
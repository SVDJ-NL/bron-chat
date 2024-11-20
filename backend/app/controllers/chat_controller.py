from ..config import settings
from ..schemas import ChatMessage
from ..models import Session
from typing import List, Dict, AsyncGenerator, Tuple
import logging
import json
from asyncio import sleep
from datetime import datetime
from ..services.qdrant_service import QdrantService
from ..services.cohere_service import CohereService
from ..services.litellm_service import LiteLLMService
from ..text_utils import to_markdown, format_content, get_formatted_date_english, get_formatted_current_date_dutch
from ..services.base_llm_service import BaseLLMService
from ..schemas import Session, ChatMessage, ChatDocument, SessionCreate, SessionUpdate
from ..services.session_service import SessionService
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatController:
    def __init__(self):                
        # Use the configured LLM service
        if settings.LLM_SERVICE.lower() == "litellm":
            self.llm_service = LiteLLMService()
        else:
            self.llm_service = CohereService()
        self.qdrant_service = QdrantService(self.llm_service)
        
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

    def update_session(self, db, query, session_id):
        session_service = SessionService(db)
        
        # Get session and store necessary data
        session = session_service.get_session(session_id)
        current_session_id = session.id  # Store session ID
        session_messages = session.get_messages()  # Get messages
        
        is_new_session = not session_messages or len(session_messages) == 0
        
        if is_new_session:        
            initial_messages = self.llm_service.get_initial_messages(query)
            session = session_service.update_session(
                current_session_id,  # Use stored session ID
                SessionUpdate(
                    messages=initial_messages,
                )
            )        
        else:
            user_message = self.llm_service.get_user_message(query)
            session = session_service.update_session(
                current_session_id,  # Use stored session ID
                SessionUpdate(
                    messages=session_messages + [user_message]
                )
            )
            logger.info(f"Using existing session: {current_session_id}")
            
        return session        

    async def event_generator(self, session):
        full_formatted_content = ""
        full_original_content = ""
        
        try:
            yield 'data: ' + json.dumps({
                "type": "session",
                "session_id": session.id  # Use stored session ID
            }) + "\n\n"
            await sleep(0)
            
            yield 'data: ' + json.dumps({
                "type": "status", 
                "role": "assistant", 
                "content": "Uw verzoek wordt nu verwerkt..."
            }) + "\n\n"
            await sleep(0)
                        
            yield 'data: ' + json.dumps({
                "type": "status", 
                "role": "assistant", 
                "content": "Documenten worden gezocht..."
            }) + "\n\n"
            await sleep(0)
            
            try: 
                relevant_docs = self.qdrant_service.retrieve_relevant_documents(query)
                logger.debug(f"Relevant documents: {relevant_docs}")
            except Exception as e:
                logger.error(f"Error retrieving relevant documents: {e}")
                raise e
            
            session_documents = session.get_documents()
            if not session_documents:
                combined_relevant_docs = relevant_docs
            else:
                if isinstance(session_documents[0], ChatDocument):
                    combined_relevant_docs = relevant_docs
                else:
                    combined_relevant_docs = relevant_docs + session_documents

            reordered_relevant_docs = qdrant_service.reorder_documents_by_publication_date(combined_relevant_docs)
                                
            yield 'data: ' + json.dumps({
                "type": "documents",
                "role": "assistant",
                "documents": reordered_relevant_docs
            }) + "\n\n"
            await sleep(0)
            
            yield 'data: ' + json.dumps({
                "type": "status", 
                "role": "assistant", 
                "content": "Documenten gevonden."
            }) + "\n\n"
            await sleep(0)
            
            yield 'data: ' + json.dumps({
                "type": "status", 
                "role": "assistant", 
                "content": "Bron genereert nu een antwoord op uw vraag..."
            }) + "\n\n"
            await sleep(0)
            
            async for response in chat_controller.generate_full_response(session.get_messages(), relevant_docs):
                yield 'data: ' + json.dumps(response) + "\n\n"
                await sleep(0)

                if response["type"] == "full":
                    full_formatted_content = response["content"]
                    full_original_content = response["content_original"]      

        except Exception as e:
            logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
            yield 'data: ' + json.dumps({"type": "error", "content": str(e)}) + "\n\n"
            await sleep(0)
        
        finally:
            # Update the session with the assistant's response
            if full_original_content:
                try:
                    if is_new_session:
                        chat_name = llm_service.create_chat_session_name(query)
                        # Always send end and close events
                        yield 'data: ' + json.dumps({"type": "session_name", "content": chat_name}) + "\n\n"
                        await sleep(0)
                    else:
                        chat_name = session.name
                                        
                    session_service.update_session(
                        session_id=current_session_id,                        
                        session_update=SessionUpdate(
                            name=chat_name,
                            messages = session.get_messages() + [
                                ChatMessage(
                                    role="assistant",
                                    content=full_original_content,
                                    formatted_content=full_formatted_content
                                )
                            ],
                            documents = session.get_documents() + [
                                ChatDocument(
                                    id=doc['id'],
                                    score=doc['score']
                                )
                                for doc in reordered_relevant_docs
                            ]   
                        )
                    )
                    
                except Exception as e:
                    logger.error(f"Error updating session: {e}", exc_info=True)
            
            # Always send end and close events
            yield 'data: ' + json.dumps({"type": "end", "content": "Done."}) + "\n\n"
            await sleep(0)
            yield 'event: close\ndata: \n\n'
            await sleep(0)

        
    async def generate_response(self, messages: List[ChatMessage], relevant_docs: List[Dict]) -> AsyncGenerator[Dict, None]:        
        logger.debug(f"Generating response for messages and documents: {messages}")
        
        formatted_docs = [{     
                'id': doc['id'],   
                "data": {
                    "title": doc['data']['title'],
                    "snippet": doc['data']['content'],
                    "publication date": get_formatted_date_english(
                        doc['data']['published']
                    ),
                    "municipality": doc['data']['location_name']
                }
            } for doc in relevant_docs
        ]
        
        current_citation = None
        first_citation = True
        try:
            for event in self.llm_service.chat_stream(messages, formatted_docs):
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
        except GeneratorExit:
            logger.info("Generator closed due to GeneratorExit")
            # Handle any cleanup if necessary
        finally:
            # Perform any necessary cleanup here
            logger.info("Exiting generate_response")

    async def generate_full_response(self, session_messages: List[ChatMessage], relevant_docs: List[Dict]):
        logger.debug(f"Generating full response for query: {session_messages[-1].content}")
        full_text = ""
        citations = []
        
        async for event in self.generate_response(session_messages, relevant_docs):
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

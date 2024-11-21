from sqlalchemy import create_engine, text
from .config import settings
from .database import SessionLocal
from .models import Base, Session, Message, Document, MessageDocument
import json
import logging
from app.database import database
from app.schemas import FeedbackType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_new_tables(db):
    """Drop the new tables if they exist"""
    try:
        db.execute(text("DROP TABLE IF EXISTS message_documents"))
        db.execute(text("DROP TABLE IF EXISTS messages"))
        db.execute(text("DROP TABLE IF EXISTS documents"))
        db.commit()
        logger.info("Dropped existing tables")
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        db.rollback()

def migrate_up():
    db = SessionLocal()
    try:
        # Force drop existing tables first
        drop_new_tables(db)
        
        # Create new tables
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        db.commit()
        logger.info("Created new tables")
        
        # Get all existing sessions
        result = db.execute(text("""
            SELECT id, name, messages, documents 
            FROM sessions 
            WHERE messages IS NOT NULL OR documents IS NOT NULL
        """))
        sessions_data = [(row.id, row.name, row.messages, row.documents) for row in result]
        db.commit()
        
        logger.info(f"Found {len(sessions_data)} sessions to migrate")
        
        # Process each session
        for session_id, name, messages_json, documents_json in sessions_data:
            try:
                messages = json.loads(messages_json) if messages_json else []
                documents = json.loads(documents_json) if documents_json else []
                
                logger.info(f"Processing session {session_id} with {len(messages)} messages and {len(documents)} documents")
                
                # Process documents first
                session_docs = {}  # Keep track of processed documents
                for doc in documents:
                    try:
                        doc_id = doc.get("id")
                        if not doc_id:
                            logger.warning(f"Skipping document without ID in session {session_id}")
                            continue
                        
                        # Extract all relevant fields
                        doc_content = doc.get("content", "")
                        doc_title = doc.get("title", "")
                        doc_url = doc.get("url", "")
                        doc_score = float(doc.get("score", 0.0))
                        
                        # Extract metadata
                        metadata = {k: v for k, v in doc.items() 
                                 if k not in ["id", "content", "title", "url", "score"]}
                        
                        # Insert or update document
                        db.execute(text("""
                            INSERT INTO documents (
                                id, content, meta, score, title, url
                            ) VALUES (
                                :id, :content,  :meta, :score, :title, :url
                            ) ON DUPLICATE KEY UPDATE
                                content = VALUES(content),
                                meta = VALUES(meta),    
                                score = VALUES(score),
                                title = VALUES(title),
                                url = VALUES(url)
                        """), {
                            "id": doc_id,
                            "content": doc_content,
                            "meta": json.dumps(metadata),
                            "score": doc_score,
                            "title": doc_title,
                            "url": doc_url
                        })
                        db.commit()
                        session_docs[doc_id] = True
                        logger.info(f"Processed document {doc_id}")
                    except Exception as e:
                        logger.error(f"Error processing document {doc.get('id', 'unknown')}: {str(e)}")
                        db.rollback()
                
                # Process messages
                for idx, msg in enumerate(messages):
                    try:
                        message_id = msg.get("id", f"{session_id}-msg-{idx}")
                        
                        # Insert message
                        db.execute(text("""
                            INSERT INTO messages (
                                id, session_id, sequence, role, content, formatted_content
                            ) VALUES (
                                :id, :session_id, :sequence, :role, :content, :formatted_content
                            )
                        """), {
                            "id": message_id,
                            "session_id": session_id,
                            "sequence": idx,
                            "role": msg.get("role"),
                            "content": msg.get("content", ""),
                            "formatted_content": msg.get("formatted_content", "")
                        })
                        db.commit()
                        logger.info(f"Processed message {message_id}")
                        
                        # Link documents to message
                        if msg.get("role") == "assistant" and session_docs:
                            # For assistant messages, link all session documents
                            for doc_id in session_docs:
                                try:
                                    db.execute(text("""
                                        INSERT IGNORE INTO message_documents 
                                        (message_id, document_id)
                                        VALUES (:message_id, :document_id)
                                    """), {
                                        "message_id": message_id,
                                        "document_id": doc_id
                                    })
                                    db.commit()
                                except Exception as e:
                                    logger.error(f"Error linking document {doc_id} to message {message_id}: {str(e)}")
                                    db.rollback()
                            
                            logger.info(f"Linked {len(session_docs)} documents to message {message_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing message {idx} for session {session_id}: {str(e)}")
                        db.rollback()

                logger.info(f"Successfully processed session {session_id}")

            except Exception as e:
                logger.error(f"Error processing session {session_id}: {str(e)}")
                db.rollback()

        # Drop old columns in a final transaction
        try:
            db.execute(text("ALTER TABLE sessions DROP COLUMN IF EXISTS messages"))
            db.execute(text("ALTER TABLE sessions DROP COLUMN IF EXISTS documents"))
            db.commit()
            logger.info("Successfully dropped old columns")
        except Exception as e:
            logger.error(f"Error dropping old columns: {str(e)}")
            db.rollback()
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()

def migrate_down():
    db = SessionLocal()
    try:
        # Check if rollback is needed
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'sessions' 
                AND column_name = 'messages'
            );
        """))
        if result.scalar():
            logger.info("Tables already in old format, skipping rollback...")
            return

        # Convert back to old format
        sessions = db.execute(text("SELECT id FROM sessions")).fetchall()
        
        # Add back the columns
        db.execute(text("ALTER TABLE sessions ADD COLUMN messages JSON"))
        db.execute(text("ALTER TABLE sessions ADD COLUMN documents JSON"))
        
        for session_row in sessions:
            session_id = session_row[0]
            
            # Get all messages for this session
            messages = db.execute(text("""
                SELECT * FROM messages 
                WHERE session_id = :session_id 
                ORDER BY sequence
            """), {"session_id": session_id}).fetchall()
            
            # Get all documents for this session
            documents = db.execute(text("""
                SELECT DISTINCT d.* 
                FROM documents d
                JOIN message_documents md ON md.document_id = d.id
                JOIN messages m ON m.id = md.message_id
                WHERE m.session_id = :session_id
            """), {"session_id": session_id}).fetchall()
            
            # Convert to old format
            messages_json = []
            for msg in messages:
                messages_json.append({
                    "role": msg.role,
                    "content": msg.content,
                    "formatted_content": msg.formatted_content
                })
            
            documents_json = []
            for doc in documents:
                documents_json.append({
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": json.loads(doc.meta) if doc.meta else {}
                })
            
            # Update session
            db.execute(text("""
                UPDATE sessions 
                SET messages = :messages,
                    documents = :documents
                WHERE id = :id
            """), {
                "id": session_id,
                "messages": json.dumps(messages_json),
                "documents": json.dumps(documents_json)
            })
        
        # Drop new tables
        db.execute(text("DROP TABLE IF EXISTS message_documents"))
        db.execute(text("DROP TABLE IF EXISTS documents"))
        db.execute(text("DROP TABLE IF EXISTS messages"))
        
        db.commit()
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "down":
            migrate_down()
        elif sys.argv[1] == "force":
            logger.info("Forcing migration...")
            drop_new_tables(SessionLocal())
            migrate_up()
    else:
        migrate_up() 
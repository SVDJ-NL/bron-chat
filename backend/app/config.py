import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "host.docker.internal")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    DATABASE_URL: str = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST', 'mysql')}/{os.getenv('MYSQL_DATABASE')}"
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY")
    COHERE_EMBED_MODEL: str = os.getenv("COHERE_EMBED_MODEL")
    COHERE_RERANK_MODEL: str = os.getenv("COHERE_RERANK_MODEL")
    ALLOWED_ORIGINS: str = [
        "http://localhost:5173",
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://0.0.0.0:8000",
        "http://127.0.0.1:8000",
        "http://dl:8000",
        "http://bron.ngrok.app",
        "https://bron.ngrok.app",
        "http://bron.ngrok.app:5173",
        "https://bron.ngrok.app:5173",
        "http://bron.ngrok.app:8000",
        "https://bron.ngrok.app:8000",
        "http://bron.ngrok.io",
        "https://bron.ngrok.io"
    ]
    

settings = Settings()

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "host.docker.internal")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    DATABASE_URL: str = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST', 'mysql')}/{os.getenv('MYSQL_DATABASE')}"
    OPENSPENDING_DATABASE_URL: str = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'postgres')}/{os.getenv('POSTGRES_DATABASE')}"
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY")
    COHERE_EMBED_MODEL: str = os.getenv("COHERE_EMBED_MODEL")
    COHERE_RERANK_MODEL: str = os.getenv("COHERE_RERANK_MODEL")
    SPARSE_EMBED_MODEL: str = os.getenv("SPARSE_EMBED_MODEL")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION")
    QDRANT_SPARSE_RETRIEVE_LIMIT: int = int(os.getenv("QDRANT_SPARSE_RETRIEVE_LIMIT"))
    QDRANT_DENSE_RETRIEVE_LIMIT: int = int(os.getenv("QDRANT_DENSE_RETRIEVE_LIMIT"))
    QDRANT_HYBRID_RETRIEVE_LIMIT: int = int(os.getenv("QDRANT_HYBRID_RETRIEVE_LIMIT"))
    RERANK_DOC_RETRIEVE_LIMIT: int = int(os.getenv("RERANK_DOC_RETRIEVE_LIMIT"))
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "").split(",")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    # Qdrant settings
    QDRANT_POOL_SIZE: int = 20
    QDRANT_POOL_TIMEOUT: int = 30
    QDRANT_TIMEOUT: int = 10
settings = Settings()

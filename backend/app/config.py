"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""

    # App info
    app_name: str = "CodeCompass API"
    version: str = "0.1.0"
    debug: bool = True

    # Database
    database_name: str = "codecompass.db"
    database_url: Optional[str] = None  # Override for Docker: sqlite:///data/codecompass.db

    # Data directory (for Docker volume mounts)
    data_dir: str = "."  # Override for Docker: /app/data

    # Qdrant Vector Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # LLM Configuration
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:0.5b" #"phi3.5"
    llm_base_url: str = "http://localhost:11434"

    # Embedding Configuration
    embedding_base_url: str = "http://localhost:11435"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # Debug settings
    debug_analysis_delay: int = 0  # Seconds to delay between analysis phases (0 to disable)

    # Limits
    max_file_size_mb: int = 10
    max_repo_size_mb: int = 1000
    max_chat_message_length: int = 10000
    max_search_query_length: int = 500
    max_search_limit: int = 100

    class Config:
        env_file = ".env"


settings = Settings()

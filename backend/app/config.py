"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # App info
    app_name: str = "CodeCompass API"
    version: str = "0.1.0"
    debug: bool = True

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # LLM Configuration (for MVP, static values)
    llm_provider: str = "local"
    llm_model: str = "microsoft/Phi-3.5-mini-instruct"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # Limits
    max_file_size_mb: int = 10
    max_repo_size_mb: int = 1000
    max_chat_message_length: int = 10000
    max_search_query_length: int = 500
    max_search_limit: int = 100

    class Config:
        env_file = ".env"


settings = Settings()

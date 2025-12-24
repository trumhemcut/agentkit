import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # LLM settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Agent settings
    DEFAULT_AGENT: str = "chat"
    
    class Config:
        env_file = ".env"


settings = Settings()

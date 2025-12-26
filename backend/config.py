import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # LLM settings - Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"
    
    # LLM settings - Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # LLM settings - Azure OpenAI
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_MODEL: str = "gpt-4"
    
    # Default provider
    DEFAULT_PROVIDER: str = "ollama"
    DEFAULT_MODEL: str = "qwen:7b"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Agent settings
    DEFAULT_AGENT: str = "chat"
    
    class Config:
        env_file = ".env"


settings = Settings()

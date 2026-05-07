from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    
    # Environment
    environment: str = "development"
    
    # Gemini API Keys
    gemini_api_key_1: str = ""
    gemini_api_key_2: str = ""

    # Embedding — must match the model your teammate used to build the FAISS index
    embedding_model: str = "all-MiniLM-L6-v2"
    faiss_dim: int = 384
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

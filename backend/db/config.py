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
    
    # API Keys
    gemini_api_key_1: str = ""
    gemini_api_key_2: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

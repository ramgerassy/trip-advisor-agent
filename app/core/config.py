"""
Application configuration using Pydantic settings.
"""
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./data/trip_planner.db", env="DATABASE_URL")
    
    # AI/LLM
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.1:8b", env="OLLAMA_MODEL")
    # Backup cloud providers (optional)
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    DEFAULT_LLM_PROVIDER: str = Field(default="ollama", env="DEFAULT_LLM_PROVIDER")
    DEFAULT_MODEL: str = Field(default="llama3.1:8b", env="DEFAULT_MODEL")
    
    # APIs
    OPENMETEO_BASE_URL: str = Field(default="https://api.open-meteo.com/v1", env="OPENMETEO_BASE_URL")
    WIKIPEDIA_API_URL: str = Field(default="https://en.wikipedia.org/api/rest_v1", env="WIKIPEDIA_API_URL")
    GEODB_API_KEY: str = Field(default="", env="GEODB_API_KEY")
    GEODB_BASE_URL: str = Field(default="https://wft-geo-db.p.rapidapi.com/v1", env="GEODB_BASE_URL")
    
    # Cache
    CACHE_TTL_HOURS: int = Field(default=6, env="CACHE_TTL_HOURS")
    TOOL_TIMEOUT_SECONDS: int = Field(default=30, env="TOOL_TIMEOUT_SECONDS")
    
    # Conversation
    MAX_CONVERSATION_TURNS: int = Field(default=50, env="MAX_CONVERSATION_TURNS")
    CONTEXT_SYNOPSIS_MAX_TOKENS: int = Field(default=400, env="CONTEXT_SYNOPSIS_MAX_TOKENS")
    MAX_CLARIFY_QUESTIONS: int = Field(default=3, env="MAX_CLARIFY_QUESTIONS")
    
    # Security
    SECRET_KEY: str = Field(default="change-this-in-production", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:3001"], env="CORS_ORIGINS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
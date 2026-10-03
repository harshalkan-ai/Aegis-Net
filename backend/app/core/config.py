"""
AEGIS-NET Core Configuration Settings.
Loads application parameters, Supabase credentials, and AI engine flags from environment variables.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """AEGIS-NET Backend Settings."""
    
    # Project Identity
    PROJECT_NAME: str = "AEGIS-NET Security Engine"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase Integration
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # AI Integration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    TAVILY_API_KEY: str = ""
    
    # Security & CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Risk Engine & Fast Path Latency Guardrails
    RISK_THRESHOLD_ALLOW: float = 0.30
    RISK_THRESHOLD_REVIEW: float = 0.60
    FAST_PATH_MAX_LATENCY_MS: float = 40.0
    
    # Circuit Breaker Defaults
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RESET_TIMEOUT_SEC: int = 60

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

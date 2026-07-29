"""
Application Configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os
import json


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "DigiLocker 2.0"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./digilocker.db"

    # Blockchain (Ganache)
    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"
    CHAIN_ID: int = 1337
    CONTRACT_ADDRESS: str = ""

    # IPFS
    IPFS_HOST: str = "127.0.0.1"
    IPFS_PORT: int = 5001
    IPFS_GATEWAY: str = "http://127.0.0.1:8080"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PQC (Post-Quantum Cryptography)
    PQC_ALGORITHM: str = "Dilithium2"
    PQC_KEYS_DIR: str = "./keys"

    # Biometric
    BIOMETRIC_MODEL: str = "Facenet"
    BIOMETRIC_THRESHOLD: float = 0.6
    BIOMETRIC_EMBEDDINGS_DIR: str = "./embeddings"

    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@digilocker.com"
    SMTP_FROM_NAME: str = "DigiLocker 2.0"

    # Share Links
    SHARE_LINK_BASE_URL: str = "http://localhost:3000/verify"
    SHARE_LINK_DEFAULT_EXPIRY_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS from string (JSON or comma-separated) or list"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try parsing as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            
            # Try comma-separated values
            if "," in v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            
            # Single value
            return [v.strip()] if v.strip() else []
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        os.makedirs(self.PQC_KEYS_DIR, exist_ok=True)
        os.makedirs(self.BIOMETRIC_EMBEDDINGS_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)


# Create global settings instance
settings = Settings()

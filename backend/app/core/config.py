"""Configuration des modèles et paramètres"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration de l'application"""
    
    # HuggingFace
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    USE_LOCAL_MODELS: bool = os.getenv("USE_LOCAL_MODELS", "True") == "True"
    
    # Modèles
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    LLM_MODEL: str = os.getenv(
        "LLM_MODEL",
        "mistralai/Mistral-7B-Instruct-v0.2"
    )
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./student_assistant.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
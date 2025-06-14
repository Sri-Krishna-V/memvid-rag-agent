"""
Configuration management for Memvid RAG Agent
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the Memvid RAG Agent"""

    # LLM Provider Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # LangSmith Configuration
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv(
        "LANGSMITH_PROJECT", "memvid-rag-project")
    LANGSMITH_TRACING: bool = os.getenv(
        "LANGSMITH_TRACING", "false").lower() == "true"

    # Application Configuration
    MEMVID_STORAGE_PATH: str = os.getenv("MEMVID_STORAGE_PATH", "./memories")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    DEFAULT_MODEL_NAME: str = os.getenv(
        "DEFAULT_MODEL_NAME", "gpt-4-turbo-preview")

    # Memvid Configuration
    MEMVID_CHUNK_SIZE: int = int(os.getenv("MEMVID_CHUNK_SIZE", "512"))
    MEMVID_OVERLAP: int = int(os.getenv("MEMVID_OVERLAP", "50"))
    MEMVID_EMBEDDING_MODEL: str = os.getenv(
        "MEMVID_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
    MEMVID_VIDEO_FPS: int = int(os.getenv("MEMVID_VIDEO_FPS", "30"))
    MEMVID_FRAME_SIZE: int = int(os.getenv("MEMVID_FRAME_SIZE", "256"))

    # Advanced Settings
    MAX_MEMORIES_LOADED: int = int(os.getenv("MAX_MEMORIES_LOADED", "10"))
    SEARCH_TOP_K: int = int(os.getenv("SEARCH_TOP_K", "5"))
    CONTEXT_MAX_TOKENS: int = int(os.getenv("CONTEXT_MAX_TOKENS", "4000"))


def get_config() -> Config:
    """Get configuration instance"""
    return Config()


def get_memvid_config() -> Dict[str, Any]:
    """Get Memvid-specific configuration"""
    config = get_config()
    return {
        "chunk_size": config.MEMVID_CHUNK_SIZE,
        "overlap": config.MEMVID_OVERLAP,
        "embedding_model": config.MEMVID_EMBEDDING_MODEL,
        "video_fps": config.MEMVID_VIDEO_FPS,
        "frame_size": config.MEMVID_FRAME_SIZE,
    }


def validate_api_keys() -> Dict[str, bool]:
    """Validate which API keys are available"""
    config = get_config()
    return {
        "openai": bool(config.OPENAI_API_KEY),
        "anthropic": bool(config.ANTHROPIC_API_KEY),
        "google": bool(config.GOOGLE_API_KEY),
    }


def get_available_providers() -> list[str]:
    """Get list of available LLM providers based on API keys"""
    validation = validate_api_keys()
    return [provider for provider, available in validation.items() if available]

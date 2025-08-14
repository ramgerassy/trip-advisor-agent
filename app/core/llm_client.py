"""
LangChain LLM clients for different purposes.
"""
import logging
from typing import Optional

from langchain_ollama import OllamaLLM
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm() -> OllamaLLM:
    """Get a configured Ollama LLM instance for conversations (temperature=0.7)."""
    try:
        llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
        )
        logger.info(f"Created conversational LLM with model {settings.OLLAMA_MODEL}")
        return llm
    except Exception as e:
        logger.error(f"Failed to create conversational LLM: {e}")
        raise


def get_factual_llm() -> OllamaLLM:
    """Get a configured Ollama LLM instance for factual queries (temperature=0)."""
    try:
        llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0,  # Deterministic for factual data
            top_p=1.0,      # No sampling randomness
        )
        logger.info(f"Created factual LLM with model {settings.OLLAMA_MODEL}")
        return llm
    except Exception as e:
        logger.error(f"Failed to create factual LLM: {e}")
        raise


def test_llm_connection() -> bool:
    """Test if Ollama is working."""
    try:
        llm = get_llm()
        response = llm.invoke("Say hello")
        logger.info(f"LLM test successful: {response[:50]}...")
        return True
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return False
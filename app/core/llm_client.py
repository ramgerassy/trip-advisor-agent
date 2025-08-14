"""
Simple LangChain LLM client for Ollama.
"""
import logging
from typing import Optional

from langchain_ollama import OllamaLLM
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm() -> OllamaLLM:
    """Get a configured Ollama LLM instance."""
    try:
        llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.3,
        )
        logger.info(f"Created Ollama LLM with model {settings.OLLAMA_MODEL}")
        return llm
    except Exception as e:
        logger.error(f"Failed to create LLM: {e}")
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
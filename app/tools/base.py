"""
Base tool class for all travel planning tools.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """Standard result format for all tools."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: str = "medium"  # high, medium, low
    cached: bool = False
    cache_expires_at: Optional[datetime] = None


class BaseTool(ABC):
    """Base class for all tools."""
    
    def __init__(self, name: str, cache_ttl_hours: int = 6):
        self.name = name
        self.cache_ttl_hours = cache_ttl_hours
        self._cache: Dict[str, ToolResult] = {}
    
    def _get_cache_key(self, **params) -> str:
        """Generate cache key from parameters."""
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        key_parts = [f"{k}={v}" for k, v in sorted_params]
        return f"{self.name}:" + "|".join(key_parts)
    
    def _is_cache_valid(self, result: ToolResult) -> bool:
        """Check if cached result is still valid."""
        if not result.cache_expires_at:
            return False
        return datetime.now() < result.cache_expires_at
    
    def _get_from_cache(self, cache_key: str) -> Optional[ToolResult]:
        """Get result from cache if valid."""
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if self._is_cache_valid(cached_result):
                logger.debug(f"Cache hit for {cache_key}")
                cached_result.cached = True
                return cached_result
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
                logger.debug(f"Cache expired for {cache_key}")
        return None
    
    def _store_in_cache(self, cache_key: str, result: ToolResult):
        """Store result in cache."""
        result.cache_expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
        result.cached = False
        self._cache[cache_key] = result
        logger.debug(f"Cached result for {cache_key}")
    
    @abstractmethod
    def _execute(self, **params) -> ToolResult:
        """Execute the tool logic. Must be implemented by subclasses."""
        pass
    
    def execute(self, **params) -> ToolResult:
        """
        Execute tool with caching.
        This is the main entry point for all tools.
        """
        try:
            # Generate cache key
            cache_key = self._get_cache_key(**params)
            
            # Check cache first
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Execute tool
            logger.info(f"Executing {self.name} with params: {params}")
            result = self._execute(**params)
            
            # Cache successful results
            if result.success:
                self._store_in_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                confidence="low"
            )
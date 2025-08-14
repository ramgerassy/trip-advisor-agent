"""
City information tool using Wikipedia API with LLM fallback.
"""
import logging
import re

import httpx
from app.tools.base import BaseTool, ToolResult
from app.core.config import settings
from app.core.llm_client import get_factual_llm

logger = logging.getLogger(__name__)


class CityInfoTool(BaseTool):
    """Tool for getting city information using Wikipedia API."""
    
    def __init__(self):
        super().__init__("city_info", cache_ttl_hours=settings.CACHE_TTL_HOURS)
        self.base_url = settings.WIKIPEDIA_API_URL
        self.timeout = settings.TOOL_TIMEOUT_SECONDS
        self.factual_llm = get_factual_llm()
    
    def _get_city_info_from_api(self, city: str) -> tuple[bool, dict]:
        """
        Get city information from Wikipedia API.
        Returns (success, data)
        """
        try:
            # First, search for the page
            search_url = f"{self.base_url}/page/summary/{city}"
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(search_url)
                
                if response.status_code == 404:
                    # Try with common variations
                    variations = [
                        f"{city} city",
                        f"{city}, France" if "paris" in city.lower() else f"{city}",
                        f"{city} (city)"
                    ]
                    
                    for variation in variations:
                        try:
                            search_url = f"{self.base_url}/page/summary/{variation}"
                            response = client.get(search_url)
                            if response.status_code == 200:
                                break
                        except:
                            continue
                    else:
                        return False, {"error": f"No Wikipedia page found for {city}"}
                
                response.raise_for_status()
                data = response.json()
            
            # Extract relevant information
            overview = data.get("extract", "")
            if not overview:
                return False, {"error": f"No content found for {city}"}
            
            # Clean and truncate overview
            overview = self._clean_overview(overview)
            
            result = {
                "overview": overview,
                "title": data.get("title", city),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "coordinates": data.get("coordinates", {}),
                "source": "Wikipedia API"
            }
            
            return True, result
            
        except httpx.TimeoutException:
            return False, {"error": "Wikipedia API timeout"}
        except httpx.HTTPError as e:
            return False, {"error": f"Wikipedia API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Wikipedia API error for {city}: {e}")
            return False, {"error": f"Wikipedia API failed: {str(e)}"}
    
    def _get_city_info_from_llm(self, city: str) -> tuple[bool, dict]:
        """
        Get city information from LLM as fallback.
        Returns (success, data)
        """
        try:
            prompt = f"""Provide a brief travel overview of {city} for tourists.

IMPORTANT: If you don't know about this city or are unsure, respond with "none".
Only provide information if you are confident it is accurate.

If you know about this city, provide:
1. A brief overview (2-3 sentences about what the city is known for)
2. 2-3 main highlights/attractions
3. Any important travel considerations or safety notes
4. Best months to visit (if known)

Format your response as:
overview: [brief description]
highlights: [attraction1, attraction2, attraction3]
safety: [any safety notes or "generally safe"]
best_months: [months or "year-round"]

Example:
overview: Tokyo is Japan's bustling capital, known for its modern skyscrapers, traditional temples, and vibrant culture. It's a major global financial center and offers incredible food, shopping, and nightlife.
highlights: Tokyo Skytree, Senso-ji Temple, Shibuya Crossing
safety: generally safe, very low crime rate
best_months: March-May, September-November"""

            response = self.factual_llm.invoke(prompt)
            logger.debug(f"LLM city info response for {city}: {response}")
            
            # Parse the response
            lines = response.strip().split('\n')
            
            if any('none' in line.lower() for line in lines):
                return False, {"error": f"LLM doesn't know about '{city}'"}
            
            overview = ""
            highlights = []
            safety = ""
            best_months = ""
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('overview:'):
                    overview = line.split(':', 1)[1].strip()
                elif line.startswith('highlights:'):
                    highlights_str = line.split(':', 1)[1].strip()
                    highlights = [h.strip() for h in highlights_str.split(',')]
                elif line.startswith('safety:'):
                    safety = line.split(':', 1)[1].strip()
                elif line.startswith('best_months:'):
                    best_months = line.split(':', 1)[1].strip()
            
            if not overview:
                return False, {"error": f"LLM couldn't provide useful info for '{city}'"}
            
            result = {
                "overview": overview,
                "highlights": highlights,
                "caution": [safety] if safety and safety != "generally safe" else [],
                "best_months": best_months.split(', ') if best_months else [],
                "source": "LLM knowledge"
            }
            
            return True, result
            
        except Exception as e:
            logger.error(f"LLM city info error for {city}: {e}")
            return False, {"error": f"LLM failed: {str(e)}"}
    
    def _clean_overview(self, text: str) -> str:
        """Clean and truncate Wikipedia overview text."""
        # Remove common Wikipedia markup
        text = re.sub(r'\([^)]*\)', '', text)  # Remove parenthetical content
        text = re.sub(r'\s+', ' ', text)       # Normalize whitespace
        text = text.strip()
        
        # Truncate to reasonable length for travel info
        if len(text) > 500:
            sentences = text.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) < 400:
                    truncated += sentence + ". "
                else:
                    break
            text = truncated.strip()
        
        return text
    
    def _execute(self, city: str) -> ToolResult:
        """Get city information with API first, LLM fallback."""
        
        if not city or len(city.strip()) < 2:
            return ToolResult(
                success=False,
                error="City name too short or empty",
                confidence="high"
            )
        
        # Try Wikipedia API first
        success, data = self._get_city_info_from_api(city)
        if success:
            logger.debug(f"Used Wikipedia API for {city}")
            
            # Normalize API response to standard format
            result_data = {
                "overview": data["overview"],
                "highlights": [],  # Wikipedia doesn't provide structured highlights
                "caution": [],
                "best_months": [],
                "confidence": "high",
                "source": "Wikipedia API",
                "url": data.get("url", "")
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                confidence="high"
            )
        
        # Fallback to LLM
        logger.info(f"Wikipedia API failed for {city}, trying LLM fallback")
        success, data = self._get_city_info_from_llm(city)
        if success:
            logger.info(f"Used LLM fallback for city info: {city}")
            
            result_data = {
                **data,
                "confidence": "medium"  # LLM is less reliable than API
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                confidence="medium"
            )
        
        # Both failed
        return ToolResult(
            success=False,
            error=f"Could not find information about '{city}' via Wikipedia or LLM. "
                  f"Please check the city name or try a nearby major city.",
            confidence="high",
            data={
                "overview": f"General info unavailable for {city}. Consider researching major attractions, "
                           f"local customs, and current travel advisories before visiting.",
                "highlights": [],
                "caution": ["Verify current travel conditions"],
                "best_months": [],
                "confidence": "low",
                "source": "fallback message"
            }
        )


# Global city info tool instance
_city_info_tool = CityInfoTool()


def get_city_info_tool() -> CityInfoTool:
    """Get the city info tool instance."""
    return _city_info_tool
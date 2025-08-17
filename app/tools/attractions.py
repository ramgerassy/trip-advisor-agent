"""
LLM-powered attraction recommendation tool.
"""
import logging
from typing import Dict, List, Any, Optional

from app.tools.base import BaseTool, ToolResult
from app.core.llm_client import get_factual_llm

logger = logging.getLogger(__name__)


class AttractionsTool(BaseTool):
    """LLM-powered attraction recommendations."""
    
    def __init__(self):
        super().__init__("attractions", cache_ttl_hours=24)  # Cache for 24h since attractions don't change often
        self.llm = get_factual_llm()
    
    def _execute(
        self,
        destination: str,
        interests: List[str] = None,
        family_composition: str = None,
        trip_duration_days: int = None,
        budget_level: str = "mid-range",
        names: List[str] = None,
        ages: List[int] = None,
        special_requirements: str = None
    ) -> ToolResult:
        """Generate attraction recommendations using LLM."""
        
        try:
            # Build context for LLM
            context = self._build_context(
                destination, interests, family_composition, 
                trip_duration_days, budget_level, names, ages, special_requirements
            )
            
            # Generate attractions using LLM
            attractions_data = self._generate_attractions_with_llm(destination, context)
            
            if not attractions_data:
                return ToolResult(
                    success=False,
                    error=f"Unable to find suitable attractions for {destination}. Consider trying a different destination or providing more specific preferences.",
                    confidence="high"
                )
            
            # Validate and structure the response
            structured_data = self._structure_attractions_data(attractions_data, destination, context)
            
            return ToolResult(
                success=True,
                data=structured_data,
                confidence="high",
                cached=False
            )
            
        except Exception as e:
            logger.error(f"Error generating attractions for {destination}: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to generate attraction recommendations: {str(e)}",
                confidence="low"
            )
    
    def _build_context(
        self, 
        destination: str, 
        interests: List[str], 
        family_composition: str,
        trip_duration_days: int,
        budget_level: str,
        names: List[str],
        ages: List[int],
        special_requirements: str
    ) -> Dict[str, Any]:
        """Build context dictionary for LLM prompt."""
        
        context = {
            "destination": destination,
            "budget_level": budget_level or "mid-range"
        }
        
        if interests:
            context["interests"] = interests
        
        if family_composition:
            context["family_composition"] = family_composition
            context["is_family_trip"] = True
        else:
            context["is_family_trip"] = False
        
        if trip_duration_days:
            context["duration"] = trip_duration_days
            
        if names:
            context["traveler_names"] = names
            
        if ages:
            context["ages"] = ages
            # Determine if child-friendly needed
            context["needs_child_friendly"] = any(age < 12 for age in ages)
            
        if special_requirements:
            context["special_requirements"] = special_requirements
            
        return context
    
    def _generate_attractions_with_llm(self, destination: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use LLM to generate personalized attraction recommendations."""
        
        # Build comprehensive prompt
        prompt = self._build_attraction_prompt(destination, context)
        
        try:
            response = self.llm.chat.completions.create(
                model="llama3.1:8b",
                messages=[{
                    "role": "system",
                    "content": "You are a knowledgeable travel advisor. Provide specific, accurate attraction recommendations based on the user's requirements. If you cannot provide good recommendations for a destination, be honest about it."
                }, {
                    "role": "user", 
                    "content": prompt
                }],
                temperature=0.3,  # Lower temperature for more consistent recommendations
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the LLM response into structured data
            return self._parse_llm_response(content, destination, context)
            
        except Exception as e:
            logger.error(f"LLM call failed for attractions: {e}")
            return None
    
    def _build_attraction_prompt(self, destination: str, context: Dict[str, Any]) -> str:
        """Build detailed prompt for LLM attraction generation."""
        
        prompt = f"Generate specific attraction recommendations for {destination}.\n\n"
        
        # Add context
        if context.get("interests"):
            interests_str = ", ".join(context["interests"])
            prompt += f"Traveler interests: {interests_str}\n"
        
        if context.get("is_family_trip"):
            prompt += f"Family trip: {context.get('family_composition', 'family group')}\n"
            
        if context.get("needs_child_friendly"):
            prompt += "IMPORTANT: Must include child-friendly and family-suitable attractions.\n"
            
        if context.get("duration"):
            prompt += f"Trip duration: {context['duration']} days\n"
            
        prompt += f"Budget level: {context.get('budget_level', 'mid-range')}\n\n"
        
        prompt += """Please provide 5-8 specific attractions with the following format for each:

ATTRACTION_NAME: [Name]
TYPE: [museum/beach/park/historic site/restaurant/market/etc]
DESCRIPTION: [2-3 sentence description]
WHY_RECOMMENDED: [Why this fits their interests/family needs]
PRACTICAL_INFO: [Opening hours, entry fees, location details]
FAMILY_FRIENDLY: [Yes/No and why]

If you cannot provide good recommendations for this destination, respond with: "INSUFFICIENT_DATA: [reason why recommendations cannot be provided]"

Be specific and accurate. Only recommend attractions you are confident exist."""
        
        return prompt
    
    def _parse_llm_response(self, content: str, destination: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured data."""
        
        # Check if LLM indicated insufficient data
        if "INSUFFICIENT_DATA:" in content:
            logger.info(f"LLM indicated insufficient data for {destination}")
            return None
        
        # Parse attractions from response
        attractions = []
        current_attraction = {}
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('ATTRACTION_NAME:'):
                # Save previous attraction if exists
                if current_attraction.get('name'):
                    attractions.append(current_attraction)
                # Start new attraction
                current_attraction = {
                    'name': line.replace('ATTRACTION_NAME:', '').strip()
                }
            elif line.startswith('TYPE:'):
                current_attraction['type'] = line.replace('TYPE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                current_attraction['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('WHY_RECOMMENDED:'):
                current_attraction['why_recommended'] = line.replace('WHY_RECOMMENDED:', '').strip()
            elif line.startswith('PRACTICAL_INFO:'):
                current_attraction['practical_info'] = line.replace('PRACTICAL_INFO:', '').strip()
            elif line.startswith('FAMILY_FRIENDLY:'):
                family_friendly_text = line.replace('FAMILY_FRIENDLY:', '').strip()
                current_attraction['family_friendly'] = family_friendly_text.lower().startswith('yes')
                current_attraction['family_friendly_notes'] = family_friendly_text
        
        # Don't forget the last attraction
        if current_attraction.get('name'):
            attractions.append(current_attraction)
        
        if not attractions:
            logger.warning(f"No attractions parsed from LLM response for {destination}")
            return None
            
        return {
            "attractions": attractions,
            "destination": destination,
            "total_count": len(attractions)
        }
    
    def _structure_attractions_data(self, attractions_data: Dict[str, Any], destination: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the final attractions data with metadata."""
        
        attractions = attractions_data.get("attractions", [])
        
        # Filter for family-friendly if needed
        if context.get("needs_child_friendly"):
            family_friendly_attractions = [a for a in attractions if a.get('family_friendly', False)]
            if family_friendly_attractions:
                attractions = family_friendly_attractions
        
        # Categorize attractions by type
        categories = {}
        for attraction in attractions:
            attraction_type = attraction.get('type', 'other')
            if attraction_type not in categories:
                categories[attraction_type] = []
            categories[attraction_type].append(attraction)
        
        # Create summary
        summary = f"Found {len(attractions)} attractions in {destination}"
        if context.get("interests"):
            summary += f" matching your interests in {', '.join(context['interests'])}"
        if context.get("is_family_trip"):
            summary += " with family-friendly options"
        
        return {
            "attractions": attractions,
            "categories": categories,
            "destination": destination,
            "summary": summary,
            "total_count": len(attractions),
            "context": context,
            "generated_for": {
                "interests": context.get("interests", []),
                "family_friendly": context.get("needs_child_friendly", False),
                "duration": context.get("duration"),
                "budget": context.get("budget_level")
            }
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Public execute method with caching."""
        cache_key = self._get_cache_key(**kwargs)
        
        # Check cache first
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if self._is_cache_valid(cached_result):
                logger.info(f"Returning cached attractions for {kwargs.get('destination')}")
                cached_result.cached = True
                return cached_result
        
        # Execute and cache
        result = self._execute(**kwargs)
        if result.success:
            self._store_in_cache(cache_key, result)
            
        return result


def get_attractions_tool() -> AttractionsTool:
    """Factory function to get attractions tool instance."""
    return AttractionsTool()
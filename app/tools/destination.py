"""
Destination recommendation tool using LLM intelligence.
"""
import logging
from typing import Dict, List, Any, Optional
import json

from app.tools.base import BaseTool, ToolResult
from app.core.config import settings
from app.core.llm_client import get_llm

logger = logging.getLogger(__name__)


class DestinationRecommendationTool(BaseTool):
    """Tool for recommending travel destinations using LLM intelligence."""
    
    def __init__(self):
        super().__init__("destination_recommendation", cache_ttl_hours=settings.CACHE_TTL_HOURS)
        self.llm = get_llm()
    
    def _execute(
        self,
        user_preferences: List[str],
        travelers: Dict[str, int],
        date_range: Dict[str, Any],
        budget: Optional[str] = None,
        departure_location: Optional[str] = None,
        destination_criteria: Optional[Dict[str, Any]] = None,
        max_recommendations: int = 5
    ) -> ToolResult:
        """Generate destination recommendations using LLM."""
        
        try:
            # Validate inputs
            if not user_preferences:
                return ToolResult(
                    success=False,
                    error="User preferences are required for destination recommendations",
                    confidence="high"
                )
            
            if not travelers:
                travelers = {"adults": 1, "kids": 0}
            
            # Build the prompt for LLM
            prompt = self._build_recommendation_prompt(
                user_preferences, travelers, date_range, budget, 
                departure_location, destination_criteria, max_recommendations
            )
            
            # Get LLM response
            llm_response = self.llm.invoke(prompt)
            
            # Parse the response
            recommendations = self._parse_llm_response(llm_response)
            
            if not recommendations:
                return ToolResult(
                    success=False,
                    error="Unable to generate destination recommendations. Please try with more specific preferences.",
                    confidence="medium"
                )
            
            # Generate summary
            summary = self._generate_summary(recommendations, user_preferences, travelers)
            
            return ToolResult(
                success=True,
                data={
                    "recommendations": recommendations,
                    "summary": summary,
                    "search_criteria": {
                        "preferences": user_preferences,
                        "travelers": travelers,
                        "budget": budget,
                        "duration": date_range.get("duration_days"),
                        "travel_month": date_range.get("month") or date_range.get("start"),
                        "departure_location": departure_location
                    },
                    "recommendations_count": len(recommendations)
                },
                confidence="high"
            )
            
        except Exception as e:
            logger.error(f"Destination recommendation error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to generate destination recommendations: {str(e)}",
                confidence="low"
            )
    
    def _build_recommendation_prompt(
        self,
        user_preferences: List[str],
        travelers: Dict[str, int],
        date_range: Dict[str, Any],
        budget: Optional[str],
        departure_location: Optional[str],
        destination_criteria: Optional[Dict[str, Any]],
        max_recommendations: int
    ) -> str:
        """Build a comprehensive prompt for destination recommendations."""
        
        prompt = f"""As a world-class travel expert, recommend {max_recommendations} destinations for this traveler based on their specific preferences and requirements.

TRAVELER PROFILE:
• Preferences: {', '.join(user_preferences)}
• Travelers: {travelers.get('adults', 1)} adults"""
        
        if travelers.get('kids', 0) > 0:
            prompt += f", {travelers['kids']} children"
        
        if budget:
            prompt += f"\n• Budget: {budget}"
        
        if date_range.get('duration_days'):
            prompt += f"\n• Trip duration: {date_range['duration_days']} days"
        
        if date_range.get('month'):
            prompt += f"\n• Travel month: {date_range['month']}"
        elif date_range.get('start'):
            prompt += f"\n• Travel dates: {date_range['start']}"
        
        if departure_location:
            prompt += f"\n• Departing from: {departure_location}"
        
        if destination_criteria:
            prompt += f"\n• Additional criteria: {destination_criteria}"
        
        prompt += f"""

Please provide {max_recommendations} specific destination recommendations that best match these preferences. For each destination, provide:

1. **Destination name** (City, Country or Region, Country)
2. **Why it matches** (2-3 sentences explaining why this destination fits their preferences)
3. **Key highlights** (3-4 main attractions or experiences)
4. **Best time to visit** (considering their travel timing if specified)
5. **Budget considerations** (relative cost level and money-saving tips if budget-conscious)
6. **Practical tips** (1-2 insider recommendations or important considerations)

Format your response as JSON:
```json
{{
  "recommendations": [
    {{
      "destination": "City, Country",
      "match_explanation": "Why this destination fits their preferences...",
      "highlights": ["Attraction 1", "Experience 2", "Activity 3", "Sight 4"],
      "best_time_to_visit": "Month range or season",
      "budget_notes": "Budget considerations and tips",
      "practical_tips": "Insider recommendations and considerations",
      "estimated_daily_budget": "Amount range per day",
      "recommended_duration": "X-Y days"
    }}
  ]
}}
```

Focus on destinations that genuinely match their interests. Consider seasonality, budget constraints, traveler composition, and practical accessibility. Provide diverse options across different regions if possible."""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM JSON response into recommendations."""
        
        try:
            # Extract JSON from the response
            json_start = response.find('```json')
            json_end = response.find('```', json_start + 7)
            
            if json_start != -1 and json_end != -1:
                json_str = response[json_start + 7:json_end].strip()
            else:
                # Try to find JSON without code blocks
                json_str = response.strip()
            
            # Parse JSON
            parsed = json.loads(json_str)
            recommendations = parsed.get('recommendations', [])
            
            # Validate each recommendation has required fields
            valid_recommendations = []
            for rec in recommendations:
                if all(key in rec for key in ['destination', 'match_explanation', 'highlights']):
                    valid_recommendations.append(rec)
            
            return valid_recommendations
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback: try to extract recommendations from text
            return self._parse_text_response(response)
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return []
    
    def _parse_text_response(self, response: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON responses."""
        
        recommendations = []
        
        try:
            # Simple text parsing as fallback
            lines = response.split('\n')
            current_rec = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for destination names (often numbered or bulleted)
                if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '•', '-']):
                    if current_rec and current_rec.get('destination'):
                        recommendations.append(current_rec)
                    
                    # Extract destination name
                    dest_line = line.split('.', 1)[-1].strip()
                    if dest_line.startswith('**') and dest_line.endswith('**'):
                        dest_line = dest_line[2:-2]
                    
                    current_rec = {
                        'destination': dest_line,
                        'match_explanation': 'Recommended destination matching your preferences',
                        'highlights': [],
                        'best_time_to_visit': 'Year-round',
                        'budget_notes': 'Budget varies by season and activities',
                        'practical_tips': 'Research local customs and book accommodations in advance'
                    }
                
                elif current_rec and ('why' in line.lower() or 'match' in line.lower()):
                    current_rec['match_explanation'] = line
                elif current_rec and ('highlight' in line.lower() or 'attraction' in line.lower()):
                    current_rec['highlights'].append(line)
            
            # Add the last recommendation
            if current_rec and current_rec.get('destination'):
                recommendations.append(current_rec)
        
        except Exception as e:
            logger.warning(f"Fallback text parsing failed: {e}")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_summary(
        self, 
        recommendations: List[Dict[str, Any]], 
        user_preferences: List[str],
        travelers: Dict[str, int]
    ) -> str:
        """Generate a summary of the recommendations."""
        
        if not recommendations:
            return "No suitable destinations found."
        
        top_dest = recommendations[0].get("destination", "recommended destination")
        prefs = ", ".join(user_preferences)
        
        summary = f"Based on your interests in {prefs}, "
        
        if travelers.get("kids", 0) > 0:
            summary += f"traveling with {travelers['adults']} adults and {travelers['kids']} children, "
        else:
            adults = travelers.get('adults', 1)
            if adults == 1:
                summary += "as a solo traveler, "
            elif adults == 2:
                summary += "traveling as a couple, "
            else:
                summary += f"traveling with {adults} adults, "
        
        summary += f"I recommend {top_dest} as your top choice. "
        
        if len(recommendations) > 1:
            summary += f"I've also found {len(recommendations)-1} other excellent destinations that match your preferences."
        
        return summary


# Global destination recommendation tool instance
_destination_tool = DestinationRecommendationTool()


def get_destination_tool() -> DestinationRecommendationTool:
    """Get the destination recommendation tool instance."""
    return _destination_tool
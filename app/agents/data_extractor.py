"""
Data extraction helper for parsing user messages into structured slots.
"""
import json
import logging
from typing import Dict, Any, List

from app.core.llm_client import get_factual_llm
from app.schemas import ConversationIntent

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts structured data from user messages."""
    
    def __init__(self):
        self.factual_llm = get_factual_llm()
    
    def extract_travel_data(
        self, 
        user_message: str, 
        intent: ConversationIntent,
        existing_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract travel-related data from user message.
        Returns a dictionary with extracted data.
        """
        existing_data = existing_data or {}
        
        try:
            prompt = self._build_extraction_prompt(user_message, intent, existing_data)
            response = self.factual_llm.invoke(prompt)
            
            logger.debug(f"LLM extraction response: {response}")
            
            # Parse the structured response
            extracted = self._parse_extraction_response(response)
            
            # Merge with existing data (new data takes precedence)
            result = {**existing_data, **extracted}
            
            return result
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return existing_data  # Return what we had before
    
    def _build_extraction_prompt(
        self, 
        user_message: str, 
        intent: ConversationIntent,
        existing_data: Dict[str, Any]
    ) -> str:
        """Build the extraction prompt based on intent."""
        
        base_prompt = f"""Extract travel information from this user message: "{user_message}"

IMPORTANT: Only extract information that is explicitly mentioned. If something is not mentioned, don't include it.

Current data we already have: {json.dumps(existing_data, indent=2)}

Extract any new information and format as JSON. Include only the fields that are mentioned in the message:

"""
        
        if intent == ConversationIntent.DESTINATION_RECOMMENDATION:
            base_prompt += """
Fields to look for:
- departure_location: where they're traveling from
- budget_band: budget, mid-range, luxury, no-limit
- interests: list of activities/interests
- climate_preference: hot, warm, mild, cool, cold
- trip_style: adventure, relaxation, cultural, business, family, romantic
- date_range: {start: "YYYY-MM-DD", end: "YYYY-MM-DD", flexible: true/false, duration_days: number}
- travelers: {adults: number, kids: number, ages: [numbers]}
- must_have_features: list of required destination features
- avoid_features: list of things to avoid

"""
        elif intent == ConversationIntent.PACKING_LIST:
            base_prompt += """
Fields to look for:
- destination: city/country name
- date_range: {start: "YYYY-MM-DD", end: "YYYY-MM-DD", flexible: true/false, duration_days: number}
- travelers: {adults: number, kids: number, ages: [numbers]}
- activities_planned: list of planned activities
- accommodation_type: hotel, hostel, airbnb, camping
- has_laundry: true/false
- is_international: true/false
- requires_flight: true/false
- climate_info: description of expected weather

"""
        elif intent == ConversationIntent.ATTRACTIONS:
            base_prompt += """
Fields to look for:
- destination: city/country name
- visit_duration: number of days
- attraction_types: list of types (museums, parks, restaurants, etc.)
- accessibility_needs: list of accessibility requirements
- avoid_crowds: true/false
- indoor_backup_needed: true/false
- budget_band: budget, mid-range, luxury, no-limit

"""
        
        base_prompt += """
Example response format:
{
  "destination": "Paris",
  "date_range": {"start": "2024-06-15", "end": "2024-06-20", "flexible": false},
  "travelers": {"adults": 2, "kids": 0},
  "activities_planned": ["sightseeing", "museums"]
}

Response (JSON only):"""
        
        return base_prompt
    
    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        try:
            # Try to find JSON in the response
            response = response.strip()
            
            # Look for JSON block
            if response.startswith('{') and response.endswith('}'):
                json_str = response
            else:
                # Try to extract JSON from text
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                else:
                    return {}
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Clean and validate the data
            cleaned_data = {}
            
            for key, value in data.items():
                if value is not None and value != "":
                    cleaned_data[key] = value
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse extraction JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing extraction response: {e}")
            return {}
    
    def get_missing_critical_slots(
        self, 
        intent: ConversationIntent, 
        data: Dict[str, Any]
    ) -> List[str]:
        """Get list of critical slots that are still missing."""
        
        critical_slots = {
            ConversationIntent.DESTINATION_RECOMMENDATION: [
                "interests", "date_range", "travelers"
            ],
            ConversationIntent.PACKING_LIST: [
                "destination", "date_range", "travelers"
            ],
            ConversationIntent.ATTRACTIONS: [
                "destination", "visit_duration"
            ]
        }
        
        required = critical_slots.get(intent, [])
        missing = []
        
        for slot in required:
            if slot not in data or not data[slot]:
                missing.append(slot)
            elif slot == "date_range":
                date_range = data.get("date_range", {})
                if not any([date_range.get("start"), date_range.get("end"), 
                           date_range.get("duration_days"), date_range.get("flexible")]):
                    missing.append(slot)
        
        return missing


# Global instance
_data_extractor = DataExtractor()


def get_data_extractor() -> DataExtractor:
    """Get the data extractor instance."""
    return _data_extractor
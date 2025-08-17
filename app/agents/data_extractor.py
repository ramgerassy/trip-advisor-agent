"""
Enhanced data extraction helper for parsing user messages into structured slots.
"""
import json
import logging
import re
from typing import Dict, Any, List

from app.schemas import ConversationIntent
from app.core.llm_client import get_factual_llm

logger = logging.getLogger(__name__)


class DataExtractor:
    """Enhanced data extractor for user messages."""
    
    def __init__(self):
        self.factual_llm = get_factual_llm()
    
    def extract_travel_data(
        self, 
        user_message: str, 
        intent: ConversationIntent,
        existing_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract travel-related data from user message using pattern matching.
        Returns a dictionary with extracted data.
        """
        existing_data = existing_data or {}
        
        try:
            # Use pattern matching first
            extracted = self._extract_with_patterns(user_message, intent)
            
            # Check if critical data is missing and try LLM fallback
            missing_critical = self._get_missing_critical_data_from_extraction(extracted, intent)
            if missing_critical:
                logger.info(f"Pattern matching missed critical data: {missing_critical}. Trying LLM fallback.")
                llm_extracted = self._extract_with_llm_fallback(user_message, missing_critical, intent)
                if llm_extracted:
                    extracted.update(llm_extracted)
                    logger.info(f"LLM fallback recovered data: {llm_extracted}")
            
            # Merge with existing data (new data takes precedence)
            result = {**existing_data, **extracted}
            
            logger.info(f"Extracted data from message: {extracted}")
            
            return result
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return existing_data  # Return what we had before
    
    def _extract_with_patterns(
        self, 
        user_message: str, 
        intent: ConversationIntent
    ) -> Dict[str, Any]:
        """Extract data using regex patterns and keyword matching."""
        
        message_lower = user_message.lower()
        extracted = {}
        
        # Extract destination
        destination = self._extract_destination(user_message)
        if destination:
            extracted["destination"] = destination
        
        # Extract duration/dates
        duration_info = self._extract_duration(user_message)
        if duration_info:
            extracted["date_range"] = duration_info
        
        # Extract travelers info
        travelers_info = self._extract_travelers(user_message)
        if travelers_info:
            extracted["travelers"] = travelers_info
        
        # Extract activities
        activities = self._extract_activities(user_message)
        if activities:
            extracted["activities_planned"] = activities
        
        # Extract family composition and names
        family_info = self._extract_family_composition(user_message)
        if family_info:
            extracted.update(family_info)
        
        # Extract interests and preferences (for all intents)
        interests = self._extract_interests(user_message)
        if interests:
            extracted["interests"] = interests
        
        # Extract user preferences for destination recommendations
        if intent == ConversationIntent.DESTINATION_RECOMMENDATION:
            preferences = self._extract_user_preferences(user_message)
            if preferences:
                extracted["user_preferences"] = preferences
        
        # Extract accommodation type
        accommodation = self._extract_accommodation(user_message)
        if accommodation:
            extracted["accommodation_type"] = accommodation
        
        # Extract other travel context
        if intent == ConversationIntent.PACKING_LIST:
            # Set some defaults for packing lists
            if "international" in message_lower or any(country in message_lower for country in ["rome", "italy", "paris", "france", "tokyo", "japan"]):
                extracted["is_international"] = True
            else:
                extracted["is_international"] = False
            
            # Assume flight for international destinations
            extracted["requires_flight"] = extracted.get("is_international", True)
            
            # Assume hotel accommodation has laundry
            if extracted.get("accommodation_type") == "hotel":
                extracted["has_laundry"] = True
        
        return extracted
    
    def _extract_destination(self, message: str) -> str:
        """Extract destination from message."""
        # More specific patterns for destinations - avoid capturing names
        patterns = [
            r'(?:to|in|visiting|going to|traveling to)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+with|\s+and|$)',
            r'(?:attractions in|things to do in|visit|activities in)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+with|\s+and|$|\?|\.)',
            r'(?:pack for|packing for)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+with|\s+and|$)',
            r'(?:trip to|vacation to|holiday to)\s+([A-Z][a-zA-Z\s]+?)(?:\s+for|\s+with|\s+and|$)',
            r'(?:near|around)\s+([A-Z][a-zA-Z\s]+?)(?:\s+within|\s+for|\s+with|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                destination = match.group(1).strip()
                # Filter out common non-destination words
                if destination.lower() not in ["traveling", "going", "visiting", "trip", "days", "weeks"]:
                    return destination
        
        # Look for specific known cities (case insensitive)
        known_cities = ["rome", "paris", "london", "tokyo", "new york", "barcelona", "amsterdam", "berlin"]
        message_lower = message.lower()
        
        for city in known_cities:
            if city in message_lower:
                return city.title()
        
        return None
    
    def _extract_duration(self, message: str) -> Dict[str, Any]:
        """Extract trip duration from message."""
        duration_info = {}
        
        # Look for explicit duration patterns
        duration_patterns = [
            r'(\d+)\s*days?',
            r'(\d+)\s*weeks?',
            r'(\d+)\s*nights?',
            r'for\s+(\d+)\s*days?',
            r'(\d+)[-\s]*day'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, message.lower())
            if match:
                num = int(match.group(1))
                if "week" in pattern:
                    duration_info["duration_days"] = num * 7
                elif "night" in pattern:
                    duration_info["duration_days"] = num + 1  # nights + 1 = days
                else:
                    duration_info["duration_days"] = num
                break
        
        # Look for months and seasons
        month_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
        ]
        
        season_patterns = [
            r'\b(spring|summer|fall|autumn|winter)\b'
        ]
        
        message_lower = message.lower()
        
        # Check for months
        for pattern in month_patterns:
            match = re.search(pattern, message_lower)
            if match:
                month = match.group(1)
                duration_info["month"] = month.title()
                break
        
        # Check for seasons
        for pattern in season_patterns:
            match = re.search(pattern, message_lower)
            if match:
                season = match.group(1)
                duration_info["season"] = season.title()
                break
        
        # Look for specific date patterns (basic)
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, message)
            dates_found.extend(matches)
        
        if len(dates_found) >= 2:
            duration_info["start"] = dates_found[0]
            duration_info["end"] = dates_found[1]
            duration_info["flexible"] = False
        elif len(dates_found) == 1:
            duration_info["start"] = dates_found[0]
        
        return duration_info if duration_info else None
    
    def _extract_travelers(self, message: str) -> Dict[str, Any]:
        """Extract traveler information from message."""
        travelers = {}
        
        # Look for explicit numbers
        patterns = [
            r'with\s+(\d+)\s+friends?',
            r'(\d+)\s+people',
            r'(\d+)\s+adults?',
            r'(\d+)\s+kids?',
            r'(\d+)\s+children',
        ]
        
        message_lower = message.lower()
        
        # Default to 1 adult
        adults = 1
        kids = 0
        
        # Look for friend mentions
        if re.search(r'with\s+(?:my\s+)?friend', message_lower):
            adults = 2  # User + friend
        elif re.search(r'with\s+friends', message_lower):
            adults = 3  # User + multiple friends (guess)
        
        # Look for explicit numbers
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                num = int(match.group(1))
                if "friend" in pattern:
                    adults = num + 1  # Add the user
                elif "adult" in pattern:
                    adults = num
                elif "kid" in pattern or "children" in pattern:
                    kids = num
                elif "people" in pattern:
                    adults = num
        
        travelers["adults"] = adults
        travelers["kids"] = kids
        
        return travelers
    
    def _extract_activities(self, message: str) -> List[str]:
        """Extract planned activities from message."""
        activities = []
        
        # Activity keywords mapping
        activity_keywords = {
            "sightseeing": ["sightseeing", "sight seeing", "touring", "exploring"],
            "museums": ["museum", "museums", "gallery", "galleries"],
            "historical": ["historical", "history", "historic sites", "monuments"],
            "temples": ["temple", "temples", "shrine", "shrines", "religious sites"],
            "shopping": ["shopping", "markets", "boutiques"],
            "dining": ["dining", "restaurants", "food", "cuisine"],
            "nightlife": ["nightlife", "bars", "clubs", "entertainment"],
            "nature": ["nature", "parks", "hiking", "outdoor"],
            "beaches": ["beach", "beaches", "swimming", "seaside"],
            "business": ["business", "work", "conference", "meeting"]
        }
        
        message_lower = message.lower()
        
        for activity, keywords in activity_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                activities.append(activity)
        
        return activities if activities else []
    
    def _extract_accommodation(self, message: str) -> str:
        """Extract accommodation type from message."""
        accommodation_keywords = {
            "hotel": ["hotel", "hotels"],
            "hostel": ["hostel", "hostels"],
            "airbnb": ["airbnb", "apartment", "rental"],
            "camping": ["camping", "tent", "campsite"],
            "resort": ["resort", "resorts"]
        }
        
        message_lower = message.lower()
        
        for acc_type, keywords in accommodation_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return acc_type
        
        return None
    
    def _extract_user_preferences(self, message: str) -> List[str]:
        """Extract user preferences for destination recommendations."""
        preferences = []
        
        # Preference keywords mapping
        preference_keywords = {
            "romantic": ["romantic", "romance", "honeymoon", "anniversary", "couple"],
            "luxury": ["luxury", "luxurious", "high-end", "upscale", "premium", "five-star"],
            "budget": ["budget", "cheap", "affordable", "low-cost", "backpacking"],
            "adventure": ["adventure", "adventurous", "adrenaline", "extreme", "outdoors"],
            "cultural": ["cultural", "culture", "traditional", "historic", "heritage"],
            "relaxing": ["relaxing", "peaceful", "tranquil", "calm", "spa", "wellness"],
            "family-friendly": ["family-friendly", "family", "kids", "children"],
            "beaches": ["beach", "beaches", "seaside", "coastal", "ocean", "sea"],
            "mountains": ["mountain", "mountains", "hiking", "alpine", "peaks"],
            "urban": ["urban", "city", "metropolitan", "cosmopolitan"],
            "nature": ["nature", "natural", "wildlife", "parks", "outdoor"],
            "nightlife": ["nightlife", "bars", "clubs", "entertainment"],
            "food": ["food", "cuisine", "culinary", "dining", "gastronomic"],
            "art": ["art", "artistic", "museums", "galleries", "creative"],
            "warm": ["warm", "hot", "tropical", "sunny"],
            "cool": ["cool", "cold", "cooler", "moderate"]
        }
        
        message_lower = message.lower()
        
        for preference, keywords in preference_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                preferences.append(preference)
        
        return preferences if preferences else []
    
    def _get_missing_critical_data_from_extraction(
        self, 
        extracted: Dict[str, Any], 
        intent: ConversationIntent
    ) -> List[str]:
        """Identify which critical data fields are missing from pattern extraction."""
        
        critical_fields = {
            ConversationIntent.DESTINATION_RECOMMENDATION: ["user_preferences"],
            ConversationIntent.PACKING_LIST: ["destination", "date_range", "travelers"],
            ConversationIntent.ATTRACTIONS: ["destination"]
        }
        
        required = critical_fields.get(intent, [])
        missing = []
        
        for field in required:
            if field not in extracted or not extracted[field]:
                missing.append(field)
            elif field == "date_range":
                date_range = extracted.get("date_range", {})
                if not any([date_range.get("start"), date_range.get("end"), 
                           date_range.get("duration_days"), date_range.get("month"), 
                           date_range.get("season")]):
                    missing.append(field)
            elif field == "destination":
                destination = extracted.get("destination", "")
                # Check if destination looks suspicious (too long, contains non-destination words)
                if (len(destination.split()) > 4 or 
                    any(word in destination.lower() for word in ["looking for", "activities", "outdoor", "nature spots", "near"])):
                    missing.append(field)
        
        return missing
    
    def _extract_with_llm_fallback(
        self, 
        user_message: str, 
        missing_fields: List[str], 
        intent: ConversationIntent
    ) -> Dict[str, Any]:
        """Use LLM to extract missing critical data when pattern matching fails."""
        
        if not missing_fields:
            return {}
        
        try:
            # Create targeted prompts for each missing field
            extracted_data = {}
            
            for field in missing_fields:
                field_data = self._extract_field_with_llm(user_message, field, intent)
                if field_data:
                    extracted_data.update(field_data)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"LLM fallback extraction error: {e}")
            return {}
    
    def _extract_field_with_llm(
        self, 
        user_message: str, 
        field: str, 
        intent: ConversationIntent
    ) -> Dict[str, Any]:
        """Extract a specific field using LLM with appropriate prompt."""
        
        prompts = {
            "user_preferences": f"""Extract user travel preferences from this message: "{user_message}"

Analyze the message and identify travel preferences. Return as JSON list.

Common preferences: romantic, luxury, budget, adventure, cultural, relaxing, family-friendly, beaches, mountains, urban, nature, nightlife, food, art, warm, cool

Example: "family-friendly resort with beaches" → ["family-friendly", "luxury", "beaches"]

JSON response:""",

            "destination": f"""Extract the specific destination (city/country/region) from this message: "{user_message}"

Look for the actual place name the person wants to visit. Ignore descriptive words.

Examples:
- "attractions in Paris" → "Paris"
- "outdoor activities near Barcelona" → "Barcelona"  
- "museums in London" → "London"
- "things to do in Tokyo for families" → "Tokyo"

JSON response:""",

            "date_range": f"""Extract travel time information from this message: "{user_message}"

Look for any time-related information. Parse flexible expressions.

Examples:
- "for a week" → {{"duration_days": 7}}
- "in summer" → {{"season": "Summer"}}
- "visiting for 3 days" → {{"duration_days": 3}}
- "in June for 10 days" → {{"month": "June", "duration_days": 10}}

JSON response:""",

            "travelers": f"""Extract number of travelers from this message: "{user_message}"

Count adults and children traveling. Make reasonable assumptions.

Examples:
- "family of 4" → {{"adults": 2, "kids": 2}}
- "me and my wife" → {{"adults": 2, "kids": 0}}
- "solo travel" → {{"adults": 1, "kids": 0}}
- "2 adults and 3 kids" → {{"adults": 2, "kids": 3}}

JSON response:"""
        }
        
        if field not in prompts:
            return {}
        
        try:
            prompt = prompts[field]
            response = self.factual_llm.invoke(prompt)
            logger.debug(f"LLM response for {field}: {response}")
            
            # Clean and parse the response
            response = response.strip()
            
            # Remove any markdown formatting
            if response.startswith("```") and response.endswith("```"):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            elif response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Remove common prefixes that LLMs might add
            response = response.strip()
            if response.startswith("JSON response:"):
                response = response[14:].strip()
            if response.startswith("Response:"):
                response = response[9:].strip()
            
            # Try to extract JSON from response if it contains other text
            import re
            json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            # Parse JSON response
            if field == "user_preferences":
                preferences = json.loads(response)
                if isinstance(preferences, list) and preferences:
                    return {"user_preferences": preferences}
            elif field == "destination":
                destination = json.loads(response)
                if isinstance(destination, str) and destination:
                    return {"destination": destination}
            elif field == "date_range":
                date_info = json.loads(response)
                if isinstance(date_info, dict) and date_info:
                    return {"date_range": date_info}
            elif field == "travelers":
                travelers = json.loads(response)
                if isinstance(travelers, dict) and travelers:
                    return {"travelers": travelers}
            
            return {}
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse LLM response for {field}: {e}")
            return {}
    
    def _extract_family_composition(self, message: str) -> Dict[str, Any]:
        """Extract family composition, names, and ages."""
        extracted = {}
        message_lower = message.lower()
        
        # Extract family member names and ages
        names = []
        family_composition = []
        
        # Pattern for name + age: "Emma(2)", "Sarah(33)", "John(32)"
        name_age_pattern = r'([A-Z][a-z]+)\s*\((\d+)\)'
        for match in re.finditer(name_age_pattern, message):
            name, age = match.groups()
            names.append(name)
            family_composition.append(f"{name} ({age})")
        
        # Pattern for family descriptions
        family_patterns = [
            r'family of (\d+)',
            r'(\d+) people',
            r'my (wife|husband|partner|spouse)',
            r'our (child|daughter|son|kid|kids|children)',
            r'(twin|twins)'
        ]
        
        family_info = []
        for pattern in family_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                family_info.extend(matches)
        
        # Extract specific family context
        if any(word in message_lower for word in ['family', 'wife', 'husband', 'child', 'kids', 'children']):
            extracted["family_composition"] = " ".join(family_composition) if family_composition else "family"
        
        if names:
            extracted["names"] = names
            
        # Extract ages separately
        age_pattern = r'(\d+)\s*(?:years?\s*old|yr|years?)\s*old'
        ages = re.findall(age_pattern, message_lower)
        if ages:
            extracted["ages"] = [int(age) for age in ages]
            
        return extracted
    
    def _extract_interests(self, message: str) -> List[str]:
        """Extract user interests and preferences."""
        message_lower = message.lower()
        interests = []
        
        # Interest keywords mapping
        interest_keywords = {
            "beaches": ["beach", "beaches", "seaside", "ocean", "swimming"],
            "museums": ["museum", "museums", "galleries", "art", "history", "cultural"],
            "food": ["food", "cuisine", "dining", "restaurants", "eating", "street food", "local food"],
            "outdoor": ["outdoor", "hiking", "nature", "parks", "activities"],
            "nightlife": ["nightlife", "bars", "clubs", "entertainment"],
            "shopping": ["shopping", "markets", "boutiques", "stores"],
            "architecture": ["architecture", "buildings", "monuments", "landmarks"],
            "adventure": ["adventure", "extreme", "sports", "thrill"],
            "relaxation": ["relaxation", "spa", "wellness", "peaceful", "quiet"],
            "family-friendly": ["family-friendly", "kid-friendly", "children", "family activities"]
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                interests.append(interest)
        
        # Also capture specific mentions
        interest_patterns = [
            r'we love ([^,.\n]+)',
            r'we enjoy ([^,.\n]+)',
            r'interested in ([^,.\n]+)',
            r'like ([^,.\n]+)',
        ]
        
        for pattern in interest_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) > 3 and len(cleaned) < 50:  # Reasonable length
                    interests.append(cleaned)
        
        return list(set(interests))  # Remove duplicates
    
    def get_missing_critical_slots(
        self, 
        intent: ConversationIntent, 
        data: Dict[str, Any]
    ) -> List[str]:
        """Get list of critical slots that are still missing."""
        
        critical_slots = {
            ConversationIntent.DESTINATION_RECOMMENDATION: [
                "user_preferences"
            ],
            ConversationIntent.PACKING_LIST: [
                "destination", "date_range", "travelers"
            ],
            ConversationIntent.ATTRACTIONS: [
                "destination"
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
_data_extractor = None


def get_data_extractor() -> DataExtractor:
    """Get the data extractor instance."""
    global _data_extractor
    if _data_extractor is None:
        _data_extractor = DataExtractor()
    return _data_extractor
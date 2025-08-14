"""
Conversation state machine for modular service approach.
Each service (destination, packing, attractions) follows the same phase pattern.
"""
from typing import  Dict, List, Optional, Set
from app.schemas import ConversationIntent, ConversationPhase


# Universal phase transitions (same for all services)
VALID_TRANSITIONS: Dict[ConversationPhase, List[ConversationPhase]] = {
    ConversationPhase.INTENT_DETECTION: [ConversationPhase.DATA_COLLECTION],
    ConversationPhase.DATA_COLLECTION: [ConversationPhase.PROCESSING, ConversationPhase.INTENT_DETECTION],  # Can go back if intent changes
    ConversationPhase.PROCESSING: [ConversationPhase.REFINEMENT, ConversationPhase.DATA_COLLECTION],  # Can go back if missing data
    ConversationPhase.REFINEMENT: [ConversationPhase.COMPLETED, ConversationPhase.PROCESSING],  # Can regenerate or complete
    ConversationPhase.COMPLETED: [ConversationPhase.INTENT_DETECTION]  # Can start new service
}

# Required data slots per service and phase
REQUIRED_SLOTS: Dict[ConversationIntent, Dict[ConversationPhase, List[str]]] = {
    ConversationIntent.DESTINATION_RECOMMENDATION: {
        ConversationPhase.INTENT_DETECTION: [],
        ConversationPhase.DATA_COLLECTION: ["user_preferences", "date_range", "destination_criteria"],
        ConversationPhase.PROCESSING: ["user_preferences", "date_range", "destination_criteria"],
        ConversationPhase.REFINEMENT: ["user_preferences", "date_range", "destination_criteria"],
        ConversationPhase.COMPLETED: ["destination_recommendations"]
    },
    ConversationIntent.PACKING_LIST: {
        ConversationPhase.INTENT_DETECTION: [],
        ConversationPhase.DATA_COLLECTION: ["destination_or_climate", "travelers", "date_range", "packing_context"],
        ConversationPhase.PROCESSING: ["destination_or_climate", "travelers", "date_range", "packing_context"],
        ConversationPhase.REFINEMENT: ["destination_or_climate", "travelers", "date_range", "packing_context"],
        ConversationPhase.COMPLETED: ["packing_list"]
    },
    ConversationIntent.ATTRACTIONS: {
        ConversationPhase.INTENT_DETECTION: [],
        ConversationPhase.DATA_COLLECTION: ["destination", "attraction_criteria"],
        ConversationPhase.PROCESSING: ["destination", "attraction_criteria"],
        ConversationPhase.REFINEMENT: ["destination", "attraction_criteria"],
        ConversationPhase.COMPLETED: ["attractions_suggestions"]
    },
    ConversationIntent.GENERAL: {
        ConversationPhase.INTENT_DETECTION: [],
        ConversationPhase.DATA_COLLECTION: [],
        ConversationPhase.PROCESSING: [],
        ConversationPhase.REFINEMENT: [],
        ConversationPhase.COMPLETED: []
    }
}

# Minimum required slots to proceed to processing for each service
MINIMUM_SLOTS_FOR_PROCESSING: Dict[ConversationIntent, List[str]] = {
    ConversationIntent.DESTINATION_RECOMMENDATION: ["user_preferences"],
    ConversationIntent.PACKING_LIST: ["destination_or_climate", "travelers"],
    ConversationIntent.ATTRACTIONS: ["destination"],
    ConversationIntent.GENERAL: []
}

# Questions to ask per service when data is missing
SERVICE_QUESTIONS: Dict[ConversationIntent, Dict[str, str]] = {
    ConversationIntent.DESTINATION_RECOMMENDATION: {
        "user_preferences": "What type of trip are you looking for? (adventure, relaxation, cultural, etc.)",
        "date_range": "When are you planning to travel? (specific dates or just duration)",
        "destination_criteria": "Do you have any specific requirements? (climate, budget, activities)",
        "departure_location": "Where will you be traveling from?"
    },
    ConversationIntent.PACKING_LIST: {
        "destination_or_climate": "What's your destination or what climate will you be in?",
        "travelers": "How many people are traveling and what are their ages?",
        "date_range": "How long will your trip be?",
        "activities_planned": "What activities do you plan to do?",
        "accommodation_info": "What type of accommodation and do they have laundry facilities?"
    },
    ConversationIntent.ATTRACTIONS: {
        "destination": "Which city or area would you like attraction suggestions for?",
        "visit_duration": "How many days will you be visiting?",
        "attraction_types": "What types of attractions interest you? (museums, parks, restaurants, etc.)",
        "user_preferences": "Any specific interests or requirements?"
    }
}

# Data that can be shared between services
SHAREABLE_DATA: Set[str] = {
    "travelers", "date_range", "user_preferences", "budget_band", 
    "destination", "climate_preference", "interests"
}


class ConversationStateManager:
    """Manages conversation state for modular service approach."""
    
    @staticmethod
    def can_transition(from_phase: ConversationPhase, to_phase: ConversationPhase) -> bool:
        """Check if transition between phases is valid."""
        return to_phase in VALID_TRANSITIONS[from_phase]
    
    @staticmethod
    def get_required_slots(intent: ConversationIntent, phase: ConversationPhase) -> List[str]:
        """Get required slots for a given service and phase."""
        return REQUIRED_SLOTS.get(intent, {}).get(phase, [])
    
    @staticmethod
    def get_missing_slots(intent: ConversationIntent, phase: ConversationPhase, collected_slots: List[str]) -> List[str]:
        """Get list of missing required slots for a service/phase."""
        required = REQUIRED_SLOTS.get(intent, {}).get(phase, [])
        return [slot for slot in required if slot not in collected_slots]
    
    @staticmethod
    def can_proceed_to_processing(intent: ConversationIntent, collected_slots: List[str]) -> bool:
        """Check if we have minimum data to start processing."""
        minimum_required = MINIMUM_SLOTS_FOR_PROCESSING.get(intent, [])
        return all(slot in collected_slots for slot in minimum_required)
    
    @staticmethod
    def determine_next_phase(
        current_intent: ConversationIntent,
        current_phase: ConversationPhase,
        collected_slots: List[str],
        has_results: bool = False
    ) -> ConversationPhase:
        """Determine the next phase based on current state."""
        
        if current_phase == ConversationPhase.INTENT_DETECTION:
            # Move to data collection once intent is clear
            return ConversationPhase.DATA_COLLECTION if current_intent != ConversationIntent.GENERAL else ConversationPhase.INTENT_DETECTION
            
        elif current_phase == ConversationPhase.DATA_COLLECTION:
            # Move to processing if we have minimum required data
            if ConversationStateManager.can_proceed_to_processing(current_intent, collected_slots):
                return ConversationPhase.PROCESSING
            else:
                return ConversationPhase.DATA_COLLECTION
                
        elif current_phase == ConversationPhase.PROCESSING:
            # Move to refinement once we have results
            return ConversationPhase.REFINEMENT if has_results else ConversationPhase.PROCESSING
            
        elif current_phase == ConversationPhase.REFINEMENT:
            # User can choose to complete or ask for modifications
            return ConversationPhase.REFINEMENT  # Stay here until user explicitly completes
            
        elif current_phase == ConversationPhase.COMPLETED:
            # Can start a new service
            return ConversationPhase.INTENT_DETECTION
            
        return current_phase
    
    @staticmethod
    def get_next_questions(intent: ConversationIntent, collected_slots: List[str]) -> List[str]:
        """Get all missing questions to ask at once for better UX."""
        service_questions = SERVICE_QUESTIONS.get(intent, {})
        
        missing_questions = []
        for slot, question in service_questions.items():
            if slot not in collected_slots:
                missing_questions.append(question)
                
        return missing_questions
    
    @staticmethod
    def get_aggregated_question(intent: ConversationIntent, collected_slots: List[str]) -> Optional[str]:
        """Get a single aggregated question asking for all missing information."""
        missing_questions = ConversationStateManager.get_next_questions(intent, collected_slots)
        
        if not missing_questions:
            return None
            
        if len(missing_questions) == 1:
            return missing_questions[0]
            
        # Create an aggregated question
        service_name = intent.value.replace("_", " ").title()
        
        if len(missing_questions) == 2:
            return f"To provide the best {service_name.lower()}, I need to know: {missing_questions[0].lower()} and {missing_questions[1].lower()}"
        else:
            questions_text = ", ".join([q.lower() for q in missing_questions[:-1]])
            questions_text += f", and {missing_questions[-1].lower()}"
            return f"To provide the best {service_name.lower()}, I need to know: {questions_text}"
    
    @staticmethod
    def get_prioritized_questions(intent: ConversationIntent, collected_slots: List[str], max_questions: int = 3) -> List[str]:
        """Get the most important questions first, limited to max_questions."""
        all_questions = ConversationStateManager.get_next_questions(intent, collected_slots)
        
        # Define priority order for each service
        priority_order = {
            ConversationIntent.DESTINATION_RECOMMENDATION: [
                "user_preferences", "date_range", "destination_criteria", "departure_location"
            ],
            ConversationIntent.PACKING_LIST: [
                "destination_or_climate", "travelers", "date_range", "activities_planned", "accommodation_info"
            ],
            ConversationIntent.ATTRACTIONS: [
                "destination", "visit_duration", "attraction_types", "user_preferences"
            ]
        }
        
        service_questions = SERVICE_QUESTIONS.get(intent, {})
        priority_slots = priority_order.get(intent, list(service_questions.keys()))
        
        # Get questions in priority order, limited to max_questions
        prioritized_questions = []
        for slot in priority_slots:
            if slot not in collected_slots and slot in service_questions:
                prioritized_questions.append(service_questions[slot])
                if len(prioritized_questions) >= max_questions:
                    break
                    
        return prioritized_questions
    
    @staticmethod
    def detect_intent_from_message(message: str) -> ConversationIntent:
        """Simple intent detection from user message."""
        message_lower = message.lower()
        
        # Destination recommendation keywords
        if any(word in message_lower for word in [
            "where to go", "destination", "recommend", "suggest a place", 
            "where should i travel", "help me choose", "pick a destination"
        ]):
            return ConversationIntent.DESTINATION_RECOMMENDATION
            
        # Packing list keywords
        elif any(word in message_lower for word in [
            "pack", "packing", "what to bring", "luggage", "suitcase", 
            "backpack", "what should i take", "packing list"
        ]):
            return ConversationIntent.PACKING_LIST
            
        # Attractions keywords
        elif any(word in message_lower for word in [
            "attractions", "things to do", "activities", "sightseeing", 
            "visit", "see", "itinerary", "places to visit"
        ]):
            return ConversationIntent.ATTRACTIONS
            
        else:
            return ConversationIntent.GENERAL
    
    @staticmethod
    def can_share_data_between_services(from_intent: ConversationIntent, to_intent: ConversationIntent) -> List[str]:
        """Determine what data can be shared when switching between services."""
        # For now, all services can share the common data
        return list(SHAREABLE_DATA)
    
    @staticmethod
    def get_service_description(intent: ConversationIntent) -> str:
        """Get description of what each service does."""
        descriptions = {
            ConversationIntent.DESTINATION_RECOMMENDATION: "I'll help you find the perfect destination based on your preferences, budget, and travel style.",
            ConversationIntent.PACKING_LIST: "I'll create a personalized packing list based on your destination, activities, and travel details.",
            ConversationIntent.ATTRACTIONS: "I'll suggest attractions and activities for your destination with a personalized itinerary.",
            ConversationIntent.GENERAL: "I can help you with destination recommendations, packing lists, or attraction suggestions. What would you like to start with?"
        }
        return descriptions.get(intent, "How can I help you plan your trip?")


# Maximum questions per service before forcing progression
MAX_QUESTIONS_PER_SERVICE = 5
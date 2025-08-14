"""
Pydantic schemas for request/response validation and data structures.
Updated for modular conversation approach.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums for Conversation Intent/Service
class ConversationIntent(str, Enum):
    DESTINATION_RECOMMENDATION = "destination_recommendation"
    PACKING_LIST = "packing_list"
    ATTRACTIONS = "attractions"
    GENERAL = "general"  # For when user hasn't specified intent yet


class ConversationPhase(str, Enum):
    # Universal phases
    INTENT_DETECTION = "intent_detection"  # Figure out what user wants
    DATA_COLLECTION = "data_collection"    # Gather required info for the service
    PROCESSING = "processing"              # Generate recommendations/lists
    REFINEMENT = "refinement"             # Allow user to modify/refine results
    COMPLETED = "completed"               # Service delivered successfully


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# Travel-related enums
class BudgetBand(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"
    NO_LIMIT = "no-limit"


class TripStyle(str, Enum):
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    CULTURAL = "cultural"
    BUSINESS = "business"
    FAMILY = "family"
    ROMANTIC = "romantic"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"


class ClimatePreference(str, Enum):
    HOT = "hot"
    WARM = "warm"
    MILD = "mild"
    COOL = "cool"
    COLD = "cold"
    NO_PREFERENCE = "no_preference"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Core Data Models
class DateRange(BaseModel):
    start: Optional[str] = None  # ISO date string
    end: Optional[str] = None
    flexible: bool = False
    duration_days: Optional[int] = None  # Alternative to specific dates


class Travelers(BaseModel):
    adults: int = Field(ge=1, default=1)
    kids: int = Field(ge=0, default=0)
    ages: Optional[List[int]] = None


class UserPreferences(BaseModel):
    budget_band: Optional[BudgetBand] = None
    trip_style: List[TripStyle] = Field(default_factory=list)
    climate_preference: Optional[ClimatePreference] = None
    interests: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    mobility_requirements: Optional[str] = None
    accommodation_type: Optional[str] = None  # hotel, hostel, airbnb, etc.


# Service-Specific Data Models

# 1. DESTINATION RECOMMENDATION
class DestinationCriteria(BaseModel):
    """What user is looking for in a destination"""
    departure_location: Optional[str] = None
    max_travel_time_hours: Optional[int] = None
    must_have_features: List[str] = Field(default_factory=list)  # beach, mountains, museums, etc.
    avoid_features: List[str] = Field(default_factory=list)
    previous_destinations: List[str] = Field(default_factory=list)
    language_preference: Optional[str] = None


class DestinationRecommendation(BaseModel):
    name: str
    country: str
    region: Optional[str] = None
    description: str
    why_recommended: str
    best_time_to_visit: List[str]
    estimated_budget_per_day: Optional[Dict[str, float]] = None  # currency -> amount
    highlights: List[str]
    travel_time_from_departure: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1)


# 2. PACKING LIST
class PackingContext(BaseModel):
    """Context needed for packing recommendations"""
    destination: Optional[str] = None
    climate_info: Optional[str] = None  # hot/cold/rainy season, etc.
    activities_planned: List[str] = Field(default_factory=list)
    accommodation_has_laundry: Optional[bool] = None
    checked_bag_allowed: Optional[bool] = None
    bag_size_preference: Optional[str] = None  # backpack, suitcase, carry-on only


class PackingItem(BaseModel):
    name: str
    quantity: int = Field(ge=0)
    category: str
    priority: str = Field(description="essential/recommended/optional")
    reason: Optional[str] = None
    alternatives: List[str] = Field(default_factory=list)


class PackingList(BaseModel):
    context: PackingContext
    items_by_category: Dict[str, List[PackingItem]]
    total_items: int
    notes: List[str] = Field(default_factory=list)
    weather_considerations: Optional[str] = None


# 3. ATTRACTIONS
class AttractionCriteria(BaseModel):
    """What user is looking for in attractions"""
    destination: str
    visit_duration: Optional[int] = None  # days
    attraction_types: List[str] = Field(default_factory=list)  # museums, parks, restaurants, etc.
    max_distance_km: Optional[float] = None
    accessibility_needs: List[str] = Field(default_factory=list)
    avoid_crowds: Optional[bool] = None
    indoor_backup_needed: Optional[bool] = None


class Attraction(BaseModel):
    name: str
    type: str
    description: str
    location: Optional[str] = None
    estimated_visit_time: Optional[str] = None
    best_time_of_day: Optional[str] = None
    cost_estimate: Optional[str] = None
    booking_required: Optional[bool] = None
    accessibility_info: Optional[str] = None
    why_recommended: str


class AttractionsSuggestions(BaseModel):
    destination: str
    criteria: AttractionCriteria
    attractions_by_type: Dict[str, List[Attraction]]
    daily_itinerary_suggestion: Optional[Dict[str, List[str]]] = None  # day -> attraction names
    notes: List[str] = Field(default_factory=list)


# Tool Output Models
class DailyWeather(BaseModel):
    date: str
    tmin: float
    tmax: float
    precip_prob: float = Field(ge=0, le=100)
    conditions: Optional[str] = None


class ToolWeatherOut(BaseModel):
    daily: List[DailyWeather]
    summary: str
    confidence: Confidence = Confidence.MEDIUM


class ToolCityInfoOut(BaseModel):
    overview: str
    highlights: List[str] = Field(default_factory=list)
    caution: List[str] = Field(default_factory=list)
    best_months: List[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


# Conversation State (updated for modular approach)
class ConversationState(BaseModel):
    intent: ConversationIntent
    phase: ConversationPhase
    
    # Common data collected from user
    travelers: Optional[Travelers] = None
    date_range: Optional[DateRange] = None
    user_preferences: Optional[UserPreferences] = None
    
    # Service-specific data
    destination_criteria: Optional[DestinationCriteria] = None
    packing_context: Optional[PackingContext] = None
    attraction_criteria: Optional[AttractionCriteria] = None
    
    # Results
    destination_recommendations: List[DestinationRecommendation] = Field(default_factory=list)
    packing_list: Optional[PackingList] = None
    attractions_suggestions: Optional[AttractionsSuggestions] = None
    
    # Flow control
    pending_questions: List[str] = Field(default_factory=list)
    collected_slots: List[str] = Field(default_factory=list)
    uncertainty_flags: List[str] = Field(default_factory=list)
    ready_for_processing: bool = False


# API Request/Response Models
class StartConversationRequest(BaseModel):
    user_id: Optional[str] = None
    initial_intent: Optional[ConversationIntent] = None
    initial_message: Optional[str] = None


class StartConversationResponse(BaseModel):
    conversation_id: str
    message: str
    intent: ConversationIntent
    phase: ConversationPhase
    next_required: List[str] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, description="Message cannot be empty")


class SendMessageResponse(BaseModel):
    agent_response: str
    intent: ConversationIntent
    phase: ConversationPhase
    next_required: List[str] = Field(default_factory=list)
    missing_slots: List[str] = Field(default_factory=list)
    
    # Service-specific results (only populated when ready)
    destination_recommendations: Optional[List[DestinationRecommendation]] = None
    packing_list: Optional[PackingList] = None
    attractions_suggestions: Optional[AttractionsSuggestions] = None
    
    # Control info
    tool_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    uncertainty_flags: List[str] = Field(default_factory=list)
    ready_for_next_service: bool = False  # Can transition to another service


class GetConversationResponse(BaseModel):
    conversation_id: str
    status: ConversationStatus
    created_at: datetime
    synopsis: Optional[str] = None
    current_intent: ConversationIntent
    current_phase: ConversationPhase
    
    # Results summary
    services_completed: List[ConversationIntent] = Field(default_factory=list)
    destination_recommendations: Optional[List[DestinationRecommendation]] = None
    packing_list: Optional[PackingList] = None
    attractions_suggestions: Optional[AttractionsSuggestions] = None
    
    turn_count: int


# Cross-service transition models
class ServiceTransitionRequest(BaseModel):
    """Request to switch to a different service within the same conversation"""
    new_intent: ConversationIntent
    carry_over_data: bool = True  # Whether to use data from previous service


class ServiceTransitionResponse(BaseModel):
    message: str
    new_intent: ConversationIntent
    new_phase: ConversationPhase
    carried_over_data: List[str] = Field(default_factory=list)
    next_required: List[str] = Field(default_factory=list)
"""
Internal reasoning schemas for chain-of-thought processing.
These are NEVER exposed to users - only used internally.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas import ConversationIntent


class ToolCallPlan(BaseModel):
    """Plan for a tool call."""
    tool_name: str
    reasoning: str
    params: Dict[str, Any]
    priority: int = 1  # 1=high, 2=medium, 3=low
    required: bool = True


class QualityCheck(BaseModel):
    """A quality check to perform."""
    check_name: str
    question: str
    passed: Optional[bool] = None
    reason: Optional[str] = None
    auto_fix_action: Optional[str] = None


class InternalScratchpad(BaseModel):
    """
    Internal reasoning scratchpad - NEVER shown to user.
    Used for chain-of-thought processing.
    """
    # Planning phase
    goals: List[str] = []
    user_constraints: List[str] = []
    steps: List[str] = []
    
    # Tool execution phase
    planned_tool_calls: List[ToolCallPlan] = []
    completed_tool_calls: List[Dict[str, Any]] = []
    
    # Risk assessment
    identified_risks: List[str] = []
    mitigation_strategies: List[str] = []
    
    # Quality checks (pre-finalize)
    quality_checks: List[QualityCheck] = []
    
    # Reasoning and decisions
    key_decisions: List[str] = []
    trade_offs: List[str] = []
    assumptions: List[str] = []
    
    # Output preparation
    user_rationale: Optional[str] = None  # Short explanation for user
    confidence_level: str = "medium"  # high, medium, low
    uncertainty_flags: List[str] = []


class ReasoningEngine:
    """Engine for internal reasoning and chain-of-thought."""
    
    @staticmethod
    def create_scratchpad(
        intent: ConversationIntent,
        user_data: Dict[str, Any]
    ) -> Optional[InternalScratchpad]:
        """
        Create initial scratchpad based on intent and user data.
        Returns None for GENERAL intent (no chain-of-thought needed).
        """
        
        # No chain-of-thought for general intent
        if intent == ConversationIntent.GENERAL:
            return None
        
        scratchpad = InternalScratchpad()
        
        # Set goals based on intent
        if intent == ConversationIntent.PACKING_LIST:
            scratchpad.goals = [
                "Create comprehensive packing list",
                "Consider weather conditions", 
                "Account for activities and trip length",
                "Optimize for luggage constraints"
            ]
            
        elif intent == ConversationIntent.DESTINATION_RECOMMENDATION:
            scratchpad.goals = [
                "Find destinations matching user preferences",
                "Consider budget and timing constraints",
                "Verify travel feasibility", 
                "Provide diverse options"
            ]
            
        elif intent == ConversationIntent.ATTRACTIONS:
            scratchpad.goals = [
                "Identify relevant attractions",
                "Consider time constraints",
                "Plan logical routing",
                "Include weather contingencies"
            ]
        
        # Extract user constraints
        scratchpad.user_constraints = ReasoningEngine._extract_constraints(user_data)
        
        # Plan initial steps
        scratchpad.steps = ReasoningEngine._plan_steps(intent, user_data)
        
        return scratchpad
    
    @staticmethod
    def _extract_constraints(user_data: Dict[str, Any]) -> List[str]:
        """Extract constraints from user data."""
        constraints = []
        
        if user_data.get("budget_band"):
            constraints.append(f"Budget: {user_data['budget_band']}")
            
        if user_data.get("date_range"):
            date_range = user_data["date_range"]
            if date_range.get("duration_days"):
                constraints.append(f"Trip length: {date_range['duration_days']} days")
            if not date_range.get("flexible", True):
                constraints.append("Fixed travel dates")
                
        if user_data.get("travelers"):
            travelers = user_data["travelers"]
            if travelers.get("kids", 0) > 0:
                constraints.append("Traveling with children")
                
        if user_data.get("accommodation_type"):
            constraints.append(f"Accommodation: {user_data['accommodation_type']}")
            
        return constraints
    
    @staticmethod
    def _plan_steps(intent: ConversationIntent, user_data: Dict[str, Any]) -> List[str]:
        """Plan execution steps based on intent."""
        
        # No steps for general intent
        if intent == ConversationIntent.GENERAL:
            return []
        
        if intent == ConversationIntent.PACKING_LIST:
            return [
                "1. Get weather forecast for destination and dates",
                "2. Analyze planned activities and requirements", 
                "3. Consider trip length and laundry availability",
                "4. Generate category-based packing list",
                "5. Add weather-specific items",
                "6. Quality check for completeness"
            ]
            
        elif intent == ConversationIntent.DESTINATION_RECOMMENDATION:
            return [
                "1. Analyze user preferences and constraints",
                "2. Research potential destinations",
                "3. Check weather and seasonal considerations",
                "4. Evaluate budget feasibility",
                "5. Rank options by match quality",
                "6. Prepare recommendations with rationale"
            ]
            
        elif intent == ConversationIntent.ATTRACTIONS:
            return [
                "1. Get destination information and highlights",
                "2. Check weather forecast for visit period",
                "3. Identify attractions matching user interests",
                "4. Plan logical daily itineraries",
                "5. Add indoor backup options",
                "6. Validate time feasibility"
            ]
        
        return []
    
    @staticmethod
    def plan_tool_calls(
        scratchpad: InternalScratchpad,
        intent: ConversationIntent,
        user_data: Dict[str, Any]
    ) -> List[ToolCallPlan]:
        """Plan what tool calls are needed."""
        
        tool_plans = []
        
        # Weather tool is needed for most intents
        if user_data.get("destination") and user_data.get("date_range"):
            tool_plans.append(ToolCallPlan(
                tool_name="weather",
                reasoning="Weather data needed for recommendations",
                params={
                    "city": user_data["destination"],
                    "start_date": "2024-06-01",  # Will be replaced with actual dates
                    "end_date": "2024-06-07"
                },
                priority=1,
                required=True
            ))
        
        # City info for destination-based requests
        if user_data.get("destination"):
            tool_plans.append(ToolCallPlan(
                tool_name="city_info", 
                reasoning="City information needed for context",
                params={"city": user_data["destination"]},
                priority=2,
                required=False
            ))
        
        # Packing tool for packing lists
        if intent == ConversationIntent.PACKING_LIST:
            tool_plans.append(ToolCallPlan(
                tool_name="packing",
                reasoning="Generate rule-based packing recommendations",
                params={
                    "trip_length_days": user_data.get("date_range", {}).get("duration_days", 7),
                    "weather_data": {},  # Will be filled from weather tool
                    "activities": user_data.get("activities_planned", []),
                    "travelers": user_data.get("travelers", {}),
                    "accommodation_type": user_data.get("accommodation_type", "hotel"),
                    "has_laundry": user_data.get("has_laundry", False)
                },
                priority=1,
                required=True
            ))
        
        return tool_plans
    
    @staticmethod
    def create_quality_checks(intent: ConversationIntent) -> List[QualityCheck]:
        """Create quality checks for pre-finalize validation."""
        
        checks = []
        
        # Universal checks
        checks.extend([
            QualityCheck(
                check_name="constraint_compliance",
                question="Have all user constraints been considered?",
                auto_fix_action="Review and adjust recommendations"
            ),
            QualityCheck(
                check_name="weather_conflicts",
                question="Are there any weather-related conflicts?",
                auto_fix_action="Add weather contingencies"
            )
        ])
        
        # Intent-specific checks
        if intent == ConversationIntent.PACKING_LIST:
            checks.extend([
                QualityCheck(
                    check_name="activity_coverage",
                    question="Does packing list cover all planned activities?",
                    auto_fix_action="Add activity-specific items"
                ),
                QualityCheck(
                    check_name="weather_preparation",
                    question="Is user prepared for weather conditions?",
                    auto_fix_action="Add weather-appropriate items"
                )
            ])
            
        elif intent == ConversationIntent.ATTRACTIONS:
            checks.extend([
                QualityCheck(
                    check_name="time_feasibility",
                    question="Is the itinerary realistic for the time available?",
                    auto_fix_action="Reduce activities or extend timeframes"
                ),
                QualityCheck(
                    check_name="indoor_backups",
                    question="Are there indoor alternatives for rainy days?",
                    auto_fix_action="Add indoor attractions and activities"
                )
            ])
        
        return checks
    
    @staticmethod
    def generate_user_rationale(scratchpad: InternalScratchpad) -> str:
        """Generate a short rationale to show the user (hiding internal reasoning)."""
        
        rationale_parts = []
        
        # Mention key decisions without revealing internal process
        if scratchpad.key_decisions:
            rationale_parts.append("Based on your preferences")
            
        # Mention tool usage in general terms
        if any("weather" in call.get("tool_name", "") for call in scratchpad.completed_tool_calls):
            rationale_parts.append("considering current weather conditions")
            
        # Mention constraints
        if scratchpad.user_constraints:
            rationale_parts.append("within your specified constraints")
        
        if not rationale_parts:
            return "Based on your requirements"
            
        return ", ".join(rationale_parts) + "."
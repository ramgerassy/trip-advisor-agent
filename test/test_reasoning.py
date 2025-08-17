"""
Test the internal reasoning system.
"""
from app.schemas.internal import ReasoningEngine, InternalScratchpad
from app.schemas import ConversationIntent

def test_reasoning():
    print("🧠 Testing Internal Reasoning System...")
    
    # Test GENERAL intent first
    print("\n❓ Testing GENERAL intent (no chain-of-thought)...")
    general_scratchpad = ReasoningEngine.create_scratchpad(
        ConversationIntent.GENERAL,
        {}
    )
    
    if general_scratchpad is None:
        print("   ✅ GENERAL intent correctly returns None (no reasoning needed)")
    else:
        print("   ❌ GENERAL intent should not create scratchpad")
    
    # Test data (similar to what we extracted earlier)
    user_data = {
        "destination": "Rome",
        "date_range": {
            "duration_days": 7,
            "flexible": False
        },
        "travelers": {
            "adults": 2,
            "kids": 0
        },
        "activities_planned": ["sightseeing", "museums"],
        "accommodation_type": "hotel",
        "budget_band": "mid-range"
    }
    
    # Test packing list scratchpad
    print("\n🎒 Creating scratchpad for packing list...")
    scratchpad = ReasoningEngine.create_scratchpad(
        ConversationIntent.PACKING_LIST,
        user_data
    )
    
    print(f"📋 Goals: {len(scratchpad.goals)}")
    for i, goal in enumerate(scratchpad.goals, 1):
        print(f"   {i}. {goal}")
    
    print(f"\n🚧 Constraints: {len(scratchpad.user_constraints)}")
    for constraint in scratchpad.user_constraints:
        print(f"   • {constraint}")
    
    print(f"\n📝 Steps: {len(scratchpad.steps)}")
    for step in scratchpad.steps:
        print(f"   {step}")
    
    # Test tool planning
    print(f"\n🔧 Planning tool calls...")
    tool_plans = ReasoningEngine.plan_tool_calls(
        scratchpad,
        ConversationIntent.PACKING_LIST,
        user_data
    )
    
    print(f"Planned {len(tool_plans)} tool calls:")
    for plan in tool_plans:
        print(f"   • {plan.tool_name} (Priority {plan.priority}): {plan.reasoning}")
    
    # Test quality checks
    print(f"\n✅ Creating quality checks...")
    checks = ReasoningEngine.create_quality_checks(ConversationIntent.PACKING_LIST)
    
    print(f"Created {len(checks)} quality checks:")
    for check in checks:
        print(f"   • {check.check_name}: {check.question}")
        if check.auto_fix_action:
            print(f"     Fix: {check.auto_fix_action}")
    
    # Test user rationale generation
    print(f"\n💭 Generating user rationale...")
    scratchpad.key_decisions = ["Selected weather-appropriate items", "Optimized for hotel stay"]
    scratchpad.completed_tool_calls = [{"tool_name": "weather"}, {"tool_name": "packing"}]
    
    rationale = ReasoningEngine.generate_user_rationale(scratchpad)
    print(f"User sees: '{rationale}'")
    print("(Internal reasoning hidden from user)")

if __name__ == "__main__":
    test_reasoning()
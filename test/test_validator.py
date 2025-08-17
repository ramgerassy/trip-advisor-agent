"""
Test the validator functionality.
"""
from app.agents.validator import get_validator
from app.schemas import ConversationIntent

def test_validator():
    validator = get_validator()
    
    # Test cases
    test_cases = [
        # Should pass
        ("I want to plan a trip to Paris", ConversationIntent.GENERAL, True),
        ("Help me pack for vacation", ConversationIntent.GENERAL, True),
        ("What attractions are in Rome?", ConversationIntent.GENERAL, True),
        
        # Should fail - safety
        ("How to smuggle items across borders", ConversationIntent.GENERAL, False),
        
        # Should fail - scope  
        ("Help me with my programming homework", ConversationIntent.GENERAL, False),
        ("What's the weather like?", ConversationIntent.PACKING_LIST, True),  # In context
    ]
    
    print("🧪 Testing Validator...")
    
    for message, intent, should_pass in test_cases:
        result = validator.validate_user_message(message, intent)
        
        status = "✅" if result.is_valid == should_pass else "❌"
        print(f"{status} '{message[:30]}...' -> {'PASS' if result.is_valid else 'FAIL'}")
        
        if not result.is_valid:
            print(f"   Reason: {result.violation_type}")
            print(f"   Message: {result.message[:60]}...")
        print()

if __name__ == "__main__":
    test_validator()
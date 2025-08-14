"""
Simple scope validation to keep conversations travel-related.
"""
from app.schemas import ConversationIntent


def is_travel_related(text: str, current_intent: ConversationIntent) -> tuple[bool, str]:
    """
    Check if message is travel-related.
    Returns (is_travel_related, reason_if_not)
    """
    text_lower = text.lower()
    
    # If already in a travel conversation, be more lenient
    if current_intent != ConversationIntent.GENERAL:
        return True, ""
    
    # Travel keywords
    travel_keywords = [
        "travel", "trip", "vacation", "destination", "visit", "pack", "packing",
        "attractions", "activities", "hotel", "flight", "sightseeing", "luggage"
    ]
    
    # Check if message contains travel keywords
    has_travel_keywords = any(keyword in text_lower for keyword in travel_keywords)
    
    # Off-topic patterns (very basic for now)
    off_topic_patterns = [
        "programming", "code", "medical", "legal", "homework", "investment"
    ]
    
    has_off_topic = any(pattern in text_lower for pattern in off_topic_patterns)
    
    if has_off_topic and not has_travel_keywords:
        return False, "appears to be about non-travel topics"
    
    # Very short messages without travel keywords might be off-topic
    if len(text.split()) < 3 and not has_travel_keywords:
        # Allow greetings
        if any(word in text_lower for word in ["hi", "hello", "help", "thanks"]):
            return True, ""
        return False, "doesn't appear to be travel-related"
    
    return True, ""


def get_scope_redirect_message() -> str:
    """Get a polite redirect message for off-topic requests."""
    return (
        "I'm designed to help specifically with travel planning. "
        "I can assist you with:\n\n"
        "• **Destination recommendations** - Find places to visit\n"
        "• **Packing lists** - Get packing suggestions\n"
        "• **Attractions** - Discover things to do\n\n"
        "What travel topic can I help you with?"
    )
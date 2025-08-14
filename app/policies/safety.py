"""
Simple safety validation.
"""
import re


def is_safe_content(text: str) -> tuple[bool, str]:
    """
    Check if content is safe.
    Returns (is_safe, reason_if_unsafe)
    """
    text_lower = text.lower()
    
    # Very basic harmful patterns
    harmful_patterns = [
        r'\b(kill|murder|bomb|weapon|illegal)\b',
        r'\b(drug|smuggl|traffic)\b',
        r'\b(smuggle|smuggling)\b',
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, text_lower):
            return False, f"Contains potentially harmful content"
    
    return True, ""


def get_safety_refusal_message() -> str:
    """Get a polite refusal message for unsafe content."""
    return (
        "I can't help with that request as it may involve unsafe activities. "
        "I'm here to help with safe travel planning like destinations, "
        "packing lists, and attraction suggestions. What else can I help you with?"
    )
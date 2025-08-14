"""
Simple validator for user input.
"""
import logging
from typing import Optional

from app.core.exceptions import PolicyViolationError
from app.policies.safety import is_safe_content, get_safety_refusal_message
from app.policies.scope import is_travel_related, get_scope_redirect_message
from app.schemas import ConversationIntent

logger = logging.getLogger(__name__)


class ValidationResult:
    """Simple result of validation."""
    def __init__(self, is_valid: bool, message: str = "", violation_type: str = ""):
        self.is_valid = is_valid
        self.message = message
        self.violation_type = violation_type


class Validator:
    """Simple validator for user messages."""
    
    def validate_user_message(
        self, 
        message: str, 
        current_intent: ConversationIntent
    ) -> ValidationResult:
        """
        Validate a user message for safety and scope.
        """
        try:
            # Safety check
            is_safe, safety_reason = is_safe_content(message)
            if not is_safe:
                logger.warning(f"Safety violation: {safety_reason}")
                return ValidationResult(
                    is_valid=False,
                    message=get_safety_refusal_message(),
                    violation_type="safety"
                )
            
            # Scope check
            is_in_scope, scope_reason = is_travel_related(message, current_intent)
            if not is_in_scope:
                logger.info(f"Out of scope: {scope_reason}")
                return ValidationResult(
                    is_valid=False,
                    message=get_scope_redirect_message(),
                    violation_type="scope"
                )
            
            # All good!
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                message="I encountered an error. Please try again.",
                violation_type="error"
            )


# Global validator instance
_validator = Validator()


def get_validator() -> Validator:
    """Get the validator instance."""
    return _validator
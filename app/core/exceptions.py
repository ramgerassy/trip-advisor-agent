"""
Simple exceptions for the trip planner.
"""


class TripPlannerError(Exception):
    """Base exception for all trip planner errors."""
    pass


class PolicyViolationError(TripPlannerError):
    """Raised when content violates safety or scope policies."""
    def __init__(self, message: str, violation_type: str):
        super().__init__(message)
        self.violation_type = violation_type


class ValidationError(TripPlannerError):
    """Raised when validation fails."""
    pass
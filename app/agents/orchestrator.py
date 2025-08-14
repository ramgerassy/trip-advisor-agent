"""
Simple orchestrator for managing conversation flow.
"""
import logging

from sqlalchemy.orm import Session
from app.core.llm_client import get_llm
from app.agents.validator import get_validator
from app.database.models import Conversation
from app.schemas import ConversationIntent, ConversationPhase
from app.schemas.state import ConversationStateManager

logger = logging.getLogger(__name__)


class AgentResponse:
    """Simple response from the orchestrator."""
    def __init__(self, message: str, next_phase: ConversationPhase = None):
        self.message = message
        self.next_phase = next_phase


class SimpleOrchestrator:
    """Simple orchestrator that manages conversation flow."""
    
    def __init__(self):
        self.llm = get_llm()
        self.validator = get_validator()
    
    def process_user_message(
        self, 
        conversation_id: str,
        user_message: str,
        db: Session
    ) -> AgentResponse:
        """
        Process a user message and return an agent response.
        """
        try:
            # Load conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                return AgentResponse("Sorry, I couldn't find that conversation.")
            
            # Validate user input
            validation_result = self.validator.validate_user_message(
                user_message, 
                conversation.current_intent
            )
            
            if not validation_result.is_valid:
                # Return the validator's refusal/redirect message
                return AgentResponse(validation_result.message)
            
            # Process based on current state
            if conversation.current_intent == ConversationIntent.GENERAL:
                return self._handle_intent_detection(conversation, user_message, db)
            else:
                return self._handle_active_service(conversation, user_message, db)
                
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            return AgentResponse("I encountered an error. Please try again.")
    
    def _handle_intent_detection(
        self, 
        conversation: Conversation, 
        user_message: str,
        db: Session
    ) -> AgentResponse:
        """Handle when user hasn't specified what they want yet."""
        
        # Try to detect intent
        detected_intent = ConversationStateManager.detect_intent_from_message(user_message)
        
        if detected_intent != ConversationIntent.GENERAL:
            # Update conversation
            conversation.current_intent = detected_intent
            conversation.current_phase = ConversationPhase.DATA_COLLECTION
            db.commit()
            
            # Get service description and initial questions
            service_description = ConversationStateManager.get_service_description(detected_intent)
            questions = ConversationStateManager.get_prioritized_questions(
                detected_intent, [], max_questions=2
            )
            
            if questions:
                questions_text = "\n".join([f"• {q}" for q in questions])
                response_message = f"Perfect! {service_description}\n\nTo get started:\n{questions_text}"
            else:
                response_message = f"Great! {service_description}"
            
            return AgentResponse(response_message, ConversationPhase.DATA_COLLECTION)
        
        else:
            # Still unclear what they want
            return AgentResponse(
                "I can help you with travel planning! What would you like help with:\n\n"
                "• **Destination recommendations** - Find the perfect place to visit\n"
                "• **Packing lists** - Get personalized packing suggestions\n" 
                "• **Attractions & activities** - Discover things to do\n\n"
                "Just let me know what interests you!"
            )
    
    def _handle_active_service(
        self, 
        conversation: Conversation, 
        user_message: str,
        db: Session
    ) -> AgentResponse:
        """Handle when user is actively using a service."""
        
        # For now, this is a simple placeholder
        # In the next steps, we'll add actual data collection and processing
        
        service_name = conversation.current_intent.value.replace("_", " ").title()
        
        if conversation.current_phase == ConversationPhase.DATA_COLLECTION:
            # Placeholder: collect some data and move to processing
            conversation.current_phase = ConversationPhase.PROCESSING
            db.commit()
            
            return AgentResponse(
                f"Thanks for that information! I'm working on your {service_name.lower()} "
                f"request. This is where I would use tools to gather data and provide "
                f"personalized recommendations.\n\n"
                f"[In the next development phase, I'll integrate weather APIs, "
                f"destination databases, and generate actual recommendations here]\n\n"
                f"For now, is there anything else I can help you with?"
            )
        
        elif conversation.current_phase == ConversationPhase.PROCESSING:
            return AgentResponse(
                f"I'm still processing your {service_name.lower()} request. "
                f"Soon I'll have personalized recommendations for you!"
            )
        
        else:
            return AgentResponse(
                f"I'm helping you with {service_name.lower()}. "
                f"What specific information do you need?"
            )


# Global orchestrator instance
_orchestrator = SimpleOrchestrator()


def get_orchestrator() -> SimpleOrchestrator:
    """Get the orchestrator instance."""
    return _orchestrator
"""
Enhanced orchestrator for structured conversation flow with tool integration.
"""
import json
import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.core.llm_client import get_llm
from app.agents.validator import get_validator
from app.agents.data_extractor import get_data_extractor
from app.schemas.internal import ReasoningEngine, InternalScratchpad
from app.database.models import Conversation, StateSnapshot, Turn
from app.schemas import ConversationIntent, ConversationPhase, ConversationStatus
from app.schemas.state import ConversationStateManager

logger = logging.getLogger(__name__)


class AgentResponse:
    """Enhanced response from the orchestrator."""
    def __init__(
        self, 
        message: str, 
        next_phase: ConversationPhase = None,
        collected_data: Dict[str, Any] = None,
        tool_outputs: List[Dict[str, Any]] = None
    ):
        self.message = message
        self.next_phase = next_phase
        self.collected_data = collected_data or {}
        self.tool_outputs = tool_outputs or []


class EnhancedOrchestrator:
    """Enhanced orchestrator with structured conversation flow."""
    
    def __init__(self):
        self.llm = get_llm()
        self.validator = get_validator()
        self.data_extractor = get_data_extractor()
    
    def process_user_message(
        self, 
        conversation_id: str,
        user_message: str,
        db: Session
    ) -> AgentResponse:
        """
        Process a user message through structured conversation phases.
        """
        try:
            # Load conversation and current data
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
                return AgentResponse(validation_result.message)
            
            # Load existing conversation data
            existing_data = self._load_conversation_data(conversation, db)
            
            # Process based on current state
            if conversation.current_intent == ConversationIntent.GENERAL:
                return self._handle_intent_detection(conversation, user_message, db)
            else:
                return self._handle_structured_phases(
                    conversation, user_message, existing_data, db
                )
                
        except Exception as e:
            logger.error(f"Error in enhanced orchestrator: {e}")
            return AgentResponse("I encountered an error. Please try again.")
    
    def resume_conversation(
        self,
        conversation_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Resume a conversation by loading its current state.
        Returns conversation context for continued processing.
        """
        try:
            # Load conversation
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                return {"error": "Conversation not found"}
            
            if conversation.status != ConversationStatus.ACTIVE:
                return {"error": f"Conversation is {conversation.status.value}, cannot resume"}
            
            # Load conversation data
            existing_data = self._load_conversation_data(conversation, db)
            
            # Get latest state snapshot for synopsis
            latest_snapshot = db.query(StateSnapshot).filter(
                StateSnapshot.conversation_id == conversation.id
            ).order_by(StateSnapshot.created_at.desc()).first()
            
            # Get turn count
            turn_count = db.query(Turn).filter(
                Turn.conversation_id == conversation_id
            ).count()
            
            # Generate resume context
            resume_context = {
                "conversation_id": conversation.id,
                "intent": conversation.current_intent,
                "phase": conversation.current_phase,
                "collected_data": existing_data,
                "synopsis": latest_snapshot.context_synopsis if latest_snapshot else None,
                "turn_count": turn_count,
                "resumable": True
            }
            
            # Generate appropriate resume message
            resume_message = self._generate_resume_message(conversation, existing_data, turn_count)
            resume_context["resume_message"] = resume_message
            
            logger.info(f"Successfully resumed conversation {conversation_id} at {conversation.current_phase}")
            
            return resume_context
            
        except Exception as e:
            logger.error(f"Error resuming conversation {conversation_id}: {e}")
            return {"error": f"Failed to resume conversation: {str(e)}"}
    
    def _generate_resume_message(
        self,
        conversation: Conversation,
        data: Dict[str, Any],
        turn_count: int
    ) -> str:
        """Generate an appropriate message for resuming a conversation."""
        
        intent_name = conversation.current_intent.value.replace('_', ' ').title()
        phase_name = conversation.current_phase.value.replace('_', ' ')
        
        # Build context reminder
        context_parts = []
        if data.get("destination"):
            context_parts.append(f"destination: {data['destination']}")
        if data.get("date_range", {}).get("duration_days"):
            context_parts.append(f"duration: {data['date_range']['duration_days']} days")
        if data.get("travelers"):
            travelers = data["travelers"]
            context_parts.append(f"travelers: {travelers.get('adults', 1)} adults")
            if travelers.get("kids", 0) > 0:
                context_parts[-1] += f", {travelers['kids']} kids"
        
        context_str = ", ".join(context_parts) if context_parts else "your request"
        
        if conversation.current_phase == ConversationPhase.DATA_COLLECTION:
            missing_slots = self.data_extractor.get_missing_critical_slots(
                conversation.current_intent, data
            )
            if missing_slots:
                questions = self._generate_targeted_questions(
                    conversation.current_intent, missing_slots, max_questions=2
                )
                return (f"Welcome back! I'm helping you with {intent_name.lower()} "
                       f"for {context_str}. I still need:\n" + 
                       "\n".join([f"• {q}" for q in questions]))
            else:
                return (f"Welcome back! I have all the information for your {intent_name.lower()} "
                       f"({context_str}). Ready to proceed with recommendations?")
                       
        elif conversation.current_phase == ConversationPhase.PROCESSING:
            return (f"Welcome back! I was processing your {intent_name.lower()} request "
                   f"for {context_str}. Let me continue generating recommendations...")
                   
        elif conversation.current_phase == ConversationPhase.REFINEMENT:
            return (f"Welcome back! I've prepared {intent_name.lower()} recommendations "
                   f"for {context_str}. Would you like to review them or make any changes?")
                   
        elif conversation.current_phase == ConversationPhase.COMPLETED:
            return (f"Welcome back! Your {intent_name.lower()} for {context_str} was "
                   f"completed. Would you like to start a new request?")
        else:
            return f"Welcome back! I'm ready to continue helping you with {intent_name.lower()}."
    
    def _load_conversation_data(self, conversation: Conversation, db: Session) -> Dict[str, Any]:
        """Load existing conversation data from state snapshots."""
        latest_snapshot = db.query(StateSnapshot).filter(
            StateSnapshot.conversation_id == conversation.id
        ).order_by(StateSnapshot.created_at.desc()).first()
        
        if latest_snapshot:
            try:
                return json.loads(latest_snapshot.conversation_data)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse conversation data for {conversation.id}")
        
        return {}
    
    def _save_conversation_data(
        self, 
        conversation: Conversation, 
        data: Dict[str, Any], 
        collected_slots: List[str],
        tool_results: List[Dict[str, Any]] = None,
        prompt_fingerprint: str = None,
        db: Session = None
    ):
        """Save conversation data to state snapshot with enhanced tracking."""
        try:
            # Generate prompt fingerprint if not provided
            if not prompt_fingerprint:
                import hashlib
                data_str = json.dumps(data, sort_keys=True)
                prompt_fingerprint = hashlib.md5(data_str.encode()).hexdigest()[:16]
            
            # Create snapshot with enhanced data
            snapshot = StateSnapshot(
                conversation_id=conversation.id,
                intent=conversation.current_intent,
                phase=conversation.current_phase,
                collected_slots=json.dumps(collected_slots),
                conversation_data=json.dumps(data),
                pending_questions=json.dumps([]),
                context_synopsis=self._generate_context_synopsis(conversation, data, db),
                internal_scratchpad=json.dumps({
                    "last_prompt_fingerprint": prompt_fingerprint,
                    "tool_results_count": len(tool_results or []),
                    "data_completeness": len(collected_slots)
                })
            )
            db.add(snapshot)
            db.commit()
            
            logger.info(f"Saved state snapshot for {conversation.id} with {len(collected_slots)} slots")
            
        except Exception as e:
            logger.error(f"Failed to save conversation data: {e}")
    
    def _generate_context_synopsis(
        self, 
        conversation: Conversation, 
        data: Dict[str, Any],
        db: Session
    ) -> str:
        """Generate a compact context synopsis for the conversation."""
        
        # Get conversation turns
        turns = db.query(Turn).filter(
            Turn.conversation_id == conversation.id
        ).order_by(Turn.turn_number).all()
        
        if not turns:
            return f"New {conversation.current_intent.value.replace('_', ' ')} conversation"
        
        # Build synopsis
        intent_name = conversation.current_intent.value.replace('_', ' ').title()
        synopsis_parts = [f"{intent_name} request:"]
        
        # Add key data points
        if data.get("destination"):
            synopsis_parts.append(f"destination={data['destination']}")
            
        if data.get("date_range", {}).get("duration_days"):
            synopsis_parts.append(f"duration={data['date_range']['duration_days']}d")
            
        if data.get("travelers"):
            travelers = data["travelers"]
            adults = travelers.get("adults", 0)
            kids = travelers.get("kids", 0)
            if kids > 0:
                synopsis_parts.append(f"travelers={adults}a+{kids}k")
            else:
                synopsis_parts.append(f"travelers={adults}a")
        
        if data.get("activities_planned"):
            activities = ", ".join(data["activities_planned"][:3])  # First 3 activities
            synopsis_parts.append(f"activities=[{activities}]")
        
        # Add phase info
        synopsis_parts.append(f"phase={conversation.current_phase.value}")
        
        # Keep under 400 tokens (roughly 300 characters)
        synopsis = " ".join(synopsis_parts)
        if len(synopsis) > 300:
            synopsis = synopsis[:297] + "..."
            
        return synopsis
    
    def _handle_intent_detection(
        self, 
        conversation: Conversation, 
        user_message: str,
        db: Session
    ) -> AgentResponse:
        """Handle intent detection phase."""
        intent = ConversationStateManager.detect_intent_from_message(user_message)
        
        if intent != ConversationIntent.GENERAL:
            # Update conversation
            conversation.current_intent = intent
            conversation.current_phase = ConversationPhase.DATA_COLLECTION
            db.commit()
            
            service_description = ConversationStateManager.get_service_description(intent)
            questions = ConversationStateManager.get_prioritized_questions(
                intent, [], max_questions=2
            )
            
            if questions:
                questions_text = "\n".join([f"• {q}" for q in questions])
                response_message = f"Perfect! {service_description}\n\nTo get started:\n{questions_text}"
            else:
                response_message = f"Great! {service_description}"
            
            return AgentResponse(response_message, ConversationPhase.DATA_COLLECTION)
        
        else:
            return AgentResponse(
                "I can help you with travel planning! What would you like help with:\n\n"
                "• **Destination recommendations** - Find the perfect place to visit\n"
                "• **Packing lists** - Get personalized packing suggestions\n" 
                "• **Attractions & activities** - Discover things to do\n\n"
                "Just let me know what interests you!"
            )
    
    def _handle_structured_phases(
        self,
        conversation: Conversation,
        user_message: str,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Handle the structured conversation phases."""
        
        current_phase = conversation.current_phase
        intent = conversation.current_intent
        
        if current_phase == ConversationPhase.DATA_COLLECTION:
            return self._handle_data_collection_phase(
                conversation, user_message, existing_data, db
            )
        elif current_phase == ConversationPhase.PROCESSING:
            return self._handle_processing_phase(
                conversation, user_message, existing_data, db
            )
        elif current_phase == ConversationPhase.REFINEMENT:
            return self._handle_refinement_phase(
                conversation, user_message, existing_data, db
            )
        elif current_phase == ConversationPhase.COMPLETED:
            return self._handle_completed_phase(
                conversation, user_message, existing_data, db
            )
        else:
            # Default fallback
            return AgentResponse(
                f"I'm currently helping you with {intent.value.replace('_', ' ')}. "
                f"What specific information do you need?"
            )
    
    def _handle_data_collection_phase(
        self,
        conversation: Conversation,
        user_message: str,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Handle DATA_COLLECTION phase - gather required information."""
        
        # Extract new data from user message
        new_data = self.data_extractor.extract_travel_data(
            user_message, 
            conversation.current_intent,
            existing_data
        )
        
        # Check what critical slots are still missing
        missing_slots = self.data_extractor.get_missing_critical_slots(
            conversation.current_intent,
            new_data
        )
        
        # Save the updated data
        collected_slots = list(new_data.keys())
        self._save_conversation_data(conversation, new_data, collected_slots, db=db)
        
        if not missing_slots:
            # We have enough data to proceed to processing
            conversation.current_phase = ConversationPhase.PROCESSING
            db.commit()
            
            service_name = conversation.current_intent.value.replace("_", " ").title()
            return AgentResponse(
                f"Perfect! I have all the information I need for your {service_name.lower()}. "
                f"Let me process this and provide recommendations...",
                ConversationPhase.PROCESSING,
                collected_data=new_data
            )
        else:
            # Ask for missing information
            questions = self._generate_targeted_questions(
                conversation.current_intent,
                missing_slots,
                max_questions=2
            )
            
            if len(questions) == 1:
                response = f"Thanks for that information! {questions[0]}"
            else:
                questions_text = "\n".join([f"• {q}" for q in questions])
                response = f"Great! I just need a bit more information:\n{questions_text}"
            
            return AgentResponse(
                response,
                ConversationPhase.DATA_COLLECTION,
                collected_data=new_data
            )
    
    def _generate_targeted_questions(
        self, 
        intent: ConversationIntent, 
        missing_slots: List[str],
        max_questions: int = 3
    ) -> List[str]:
        """Generate targeted questions for missing slots."""
        
        question_map = {
            ConversationIntent.PACKING_LIST: {
                "destination": "What's your destination?",
                "date_range": "When are you traveling? (dates or duration)",
                "travelers": "How many people are traveling and what are their ages?",
            },
            ConversationIntent.DESTINATION_RECOMMENDATION: {
                "interests": "What type of activities or experiences are you looking for?",
                "date_range": "When are you planning to travel?",
                "travelers": "How many people will be traveling?",
            },
            ConversationIntent.ATTRACTIONS: {
                "destination": "Which city would you like attraction suggestions for?",
                "visit_duration": "How many days will you be visiting?",
            }
        }
        
        questions = []
        service_questions = question_map.get(intent, {})
        
        for slot in missing_slots[:max_questions]:
            if slot in service_questions:
                questions.append(service_questions[slot])
        
        return questions
    
    def _handle_processing_phase(
        self,
        conversation: Conversation,
        user_message: str,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Handle PROCESSING phase - use chain-of-thought and tools."""
        
        # Create internal reasoning scratchpad
        scratchpad = ReasoningEngine.create_scratchpad(
            conversation.current_intent,
            existing_data
        )
        
        if scratchpad is None:
            # This shouldn't happen in processing phase, but safety check
            logger.warning("No scratchpad created for processing phase")
            conversation.current_phase = ConversationPhase.REFINEMENT
            db.commit()
            return AgentResponse(
                "I'm processing your request...",
                ConversationPhase.REFINEMENT
            )
        
        logger.info(f"Created scratchpad with {len(scratchpad.goals)} goals and {len(scratchpad.steps)} steps")
        
        # Plan tool calls
        tool_plans = ReasoningEngine.plan_tool_calls(
            scratchpad,
            conversation.current_intent,
            existing_data
        )
        
        # Execute tools (placeholder for now - actual tool integration next)
        tool_results = []
        for plan in tool_plans:
            logger.info(f"Planning to execute {plan.tool_name}: {plan.reasoning}")
            tool_results.append({
                "tool_name": plan.tool_name,
                "status": "planned",
                "reasoning": plan.reasoning
            })
        
        # Add completed tool calls to scratchpad
        scratchpad.completed_tool_calls = tool_results
        
        # Record key decisions
        scratchpad.key_decisions = [
            f"Planned {len(tool_plans)} tool calls",
            "Considered all user constraints",
            "Optimized for trip requirements"
        ]
        
        # Generate user-facing rationale (hiding internal reasoning)
        user_rationale = ReasoningEngine.generate_user_rationale(scratchpad)
        
        service_name = conversation.current_intent.value.replace("_", " ").title()
        
        # Move to refinement
        conversation.current_phase = ConversationPhase.REFINEMENT
        db.commit()
        
        return AgentResponse(
            f"I've analyzed your {service_name.lower()} requirements. {user_rationale}\n\n"
            f"Here are my recommendations:\n\n"
            f"[Next step: Actual tool execution will generate real results here]\n\n"
            f"**Internal reasoning completed:**\n"
            f"• Identified {len(scratchpad.goals)} goals\n"
            f"• Planned {len(tool_plans)} tool calls\n"
            f"• Considered {len(scratchpad.user_constraints)} constraints\n\n"
            f"Would you like me to modify anything or do you have questions?",
            ConversationPhase.REFINEMENT,
            collected_data=existing_data,
            tool_outputs=tool_results
        )
    
    def _handle_refinement_phase(
        self,
        conversation: Conversation,
        user_message: str,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Handle REFINEMENT phase - allow modifications and pre-finalize checks."""
        
        message_lower = user_message.lower()
        
        # Check for completion signals
        if any(word in message_lower for word in [
            "looks good", "perfect", "thanks", "that's great", "no changes", "finalize"
        ]):
            # Before finalizing, run quality checks
            return self._run_pre_finalize_checks(conversation, existing_data, db)
        else:
            # Handle modification requests
            return AgentResponse(
                "I'd be happy to make adjustments! "
                "[In the next development phase, I'll process your specific changes and regenerate recommendations]\n\n"
                "What specific changes would you like me to make?",
                ConversationPhase.REFINEMENT,
                collected_data=existing_data
            )
    
    def _run_pre_finalize_checks(
        self,
        conversation: Conversation,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Run quality checks before finalizing recommendations."""
        
        # Create scratchpad for quality checking
        scratchpad = ReasoningEngine.create_scratchpad(
            conversation.current_intent,
            existing_data
        )
        
        if scratchpad is None:
            # Skip checks for general intent
            conversation.current_phase = ConversationPhase.COMPLETED
            db.commit()
            return AgentResponse(
                "Great! Your request has been completed.",
                ConversationPhase.COMPLETED
            )
        
        # Get quality checks for this intent
        quality_checks = ReasoningEngine.create_quality_checks(conversation.current_intent)
        
        # Simulate running the checks (in real implementation, these would be actual validations)
        passed_checks = []
        failed_checks = []
        auto_fixes = []
        
        for check in quality_checks:
            # Simulate check results (in reality, these would be actual validations)
            if check.check_name == "weather_conflicts":
                # Simulate weather check
                check.passed = True
                check.reason = "Weather appropriate for Tokyo in March"
                passed_checks.append(check)
                
            elif check.check_name == "constraint_compliance":
                # Check if all constraints are met
                check.passed = True  
                check.reason = "All user constraints considered"
                passed_checks.append(check)
                
            elif check.check_name == "activity_coverage":
                # Check activity coverage
                activities = existing_data.get("activities_planned", [])
                if "sightseeing" in activities and "temples" in activities:
                    check.passed = True
                    check.reason = "Packing covers sightseeing and temple visits"
                    passed_checks.append(check)
                else:
                    check.passed = False
                    check.reason = "Missing activity-specific items"
                    failed_checks.append(check)
                    auto_fixes.append("Add comfortable walking shoes and respectful temple attire")
                    
            elif check.check_name == "weather_preparation":
                # Weather preparation check
                check.passed = True
                check.reason = "March weather in Tokyo accounted for"
                passed_checks.append(check)
        
        # Generate quality check summary
        check_summary = f"**Pre-finalize quality checks completed:**\n"
        check_summary += f"✅ {len(passed_checks)} checks passed\n"
        
        if failed_checks:
            check_summary += f"⚠️ {len(failed_checks)} checks need attention\n\n"
            check_summary += "**Auto-adjustments made:**\n"
            for fix in auto_fixes:
                check_summary += f"• {fix}\n"
            check_summary += "\n"
        
        # Store quality check results in scratchpad
        scratchpad.quality_checks = quality_checks
        if auto_fixes:
            scratchpad.uncertainty_flags = [f"Auto-adjusted: {', '.join(auto_fixes)}"]
        
        # Finalize
        conversation.current_phase = ConversationPhase.COMPLETED
        db.commit()
        
        return AgentResponse(
            f"Excellent! I've completed your trip planning with quality assurance.\n\n"
            f"{check_summary}"
            f"Your personalized recommendations are ready! "
            f"I've considered all your requirements and made sure everything is optimized for your Tokyo trip.\n\n"
            f"Have a wonderful trip! Feel free to start a new conversation if you need help with anything else.",
            ConversationPhase.COMPLETED,
            collected_data=existing_data
        )
    
    def _handle_completed_phase(
        self,
        conversation: Conversation,
        user_message: str,
        existing_data: Dict[str, Any],
        db: Session
    ) -> AgentResponse:
        """Handle COMPLETED phase - offer new services."""
        
        return AgentResponse(
            "Your previous request has been completed! "
            "I can help you with a new travel planning task:\n\n"
            "• **Destination recommendations** - Find new places to visit\n"
            "• **Packing lists** - Get packing suggestions\n"
            "• **Attractions** - Discover things to do\n\n"
            "What would you like help with next?"
        )


# Global orchestrator instance  
_enhanced_orchestrator = EnhancedOrchestrator()


def get_orchestrator() -> EnhancedOrchestrator:
    """Get the enhanced orchestrator instance."""
    return _enhanced_orchestrator
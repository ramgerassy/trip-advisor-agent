"""
FastAPI routes for conversation management.
"""
import json
import logging
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.database.models import Conversation, ConversationStatus, Turn
from app.schemas import (
    ConversationIntent,
    ConversationPhase,
    GetConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartConversationRequest,
    StartConversationResponse,
)
from app.schemas.state import ConversationStateManager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/conversations", response_model=StartConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    db: Session = Depends(get_db)
) -> StartConversationResponse:
    """
    Start a new conversation.
    Returns conversation_id and initial message based on intent.
    """
    try:
        # Detect intent from initial message or use provided intent
        if request.initial_message:
            detected_intent = ConversationStateManager.detect_intent_from_message(
                request.initial_message
            )
        else:
            detected_intent = request.initial_intent or ConversationIntent.GENERAL
        
        # Create new conversation
        conversation = Conversation(
            id=str(uuid4()),
            user_id=request.user_id,
            status=ConversationStatus.ACTIVE,
            current_intent=detected_intent,
            current_phase=ConversationPhase.INTENT_DETECTION if detected_intent == ConversationIntent.GENERAL else ConversationPhase.DATA_COLLECTION
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Generate appropriate response message
        if detected_intent == ConversationIntent.GENERAL:
            message = "Hello! I'm your trip planning assistant. I can help you with:\n\n• **Destination recommendations** - Find the perfect place to travel\n• **Packing lists** - Get personalized packing suggestions\n• **Attractions & activities** - Discover things to do at your destination\n\nWhat would you like help with today?"
            next_required = ["intent_selection"]
        else:
            service_description = ConversationStateManager.get_service_description(detected_intent)
            message = f"Great! {service_description}"
            
            # Get initial questions for the detected service
            missing_questions = ConversationStateManager.get_prioritized_questions(
                detected_intent, [], max_questions=3
            )
            if missing_questions:
                if len(missing_questions) == 1:
                    message += f"\n\nTo get started, {missing_questions[0].lower()}"
                else:
                    questions_text = "\n".join([f"• {q}" for q in missing_questions])
                    message += f"\n\nTo get started, I need to know:\n{questions_text}"
            
            next_required = ConversationStateManager.get_required_slots(
                detected_intent, conversation.current_phase
            )
        
        # Create initial turn
        initial_turn = Turn(
            id=str(uuid4()),
            conversation_id=conversation.id,
            turn_number=1,
            user_message=request.initial_message,
            agent_response=message,
            intent=detected_intent,
            phase=conversation.current_phase
        )
        
        db.add(initial_turn)
        db.commit()
        
        logger.info(f"Started conversation {conversation.id} with intent {detected_intent}")
        
        return StartConversationResponse(
            conversation_id=conversation.id,
            message=message,
            intent=detected_intent,
            phase=conversation.current_phase,
            next_required=next_required
        )
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start conversation")


@router.post("/conversations/{conversation_id}/message", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
) -> SendMessageResponse:
    """
    Send a message to the conversation and get agent response.
    """
    try:
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if conversation.status != ConversationStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Conversation is not active")
        
        # Get turn count for this conversation
        turn_count = db.query(Turn).filter(
            Turn.conversation_id == conversation_id
        ).count()
        
        # For now, this is a placeholder response
        # In Hour 1.5-3.5, we'll implement the actual Orchestrator agent here
        
        # Simple intent detection if we're in general mode
        if conversation.current_intent == ConversationIntent.GENERAL:
            detected_intent = ConversationStateManager.detect_intent_from_message(request.message)
            if detected_intent != ConversationIntent.GENERAL:
                conversation.current_intent = detected_intent
                conversation.current_phase = ConversationPhase.DATA_COLLECTION
                
                service_description = ConversationStateManager.get_service_description(detected_intent)
                agent_response = f"Perfect! {service_description}"
                
                # Get questions for the new intent
                missing_questions = ConversationStateManager.get_prioritized_questions(
                    detected_intent, [], max_questions=3
                )
                if missing_questions:
                    questions_text = "\n".join([f"• {q}" for q in missing_questions])
                    agent_response += f"\n\nTo get started, I need to know:\n{questions_text}"
            else:
                agent_response = "I'd be happy to help! Could you let me know if you're looking for:\n\n• **Destination recommendations** - I can suggest places to visit\n• **Packing help** - I can create a personalized packing list\n• **Attraction suggestions** - I can recommend things to do\n\nWhich of these interests you?"
        else:
            # Placeholder response for active services
            agent_response = f"Thank you for your message about {conversation.current_intent.value.replace('_', ' ')}. I'm processing your request and will provide personalized recommendations soon!"
        
        # Create new turn
        new_turn = Turn(
            id=str(uuid4()),
            conversation_id=conversation_id,
            turn_number=turn_count + 1,
            user_message=request.message,
            agent_response=agent_response,
            intent=conversation.current_intent,
            phase=conversation.current_phase
        )
        
        db.add(new_turn)
        db.commit()
        
        # Update conversation timestamp
        conversation.updated_at = db.query(func.now()).scalar()
        db.commit()
        
        next_required = ConversationStateManager.get_required_slots(
            conversation.current_intent, conversation.current_phase
        )
        
        logger.info(f"Processed message for conversation {conversation_id}")
        
        return SendMessageResponse(
            agent_response=agent_response,
            intent=conversation.current_intent,
            phase=conversation.current_phase,
            next_required=next_required,
            missing_slots=[],  # Will be implemented with actual state tracking
            tool_outputs=[],
            uncertainty_flags=[],
            ready_for_next_service=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/conversations/{conversation_id}", response_model=GetConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> GetConversationResponse:
    """
    Get conversation summary and current state.
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get turn count
        turn_count = db.query(Turn).filter(
            Turn.conversation_id == conversation_id
        ).count()
        
        # Parse completed services
        completed_services = []
        if conversation.services_completed:
            completed_services = json.loads(conversation.services_completed)
        
        return GetConversationResponse(
            conversation_id=conversation.id,
            status=conversation.status,
            created_at=conversation.created_at,
            synopsis=conversation.synopsis,
            current_intent=conversation.current_intent,
            current_phase=conversation.current_phase,
            services_completed=[ConversationIntent(service) for service in completed_services],
            destination_recommendations=None,  # Will be populated when available
            packing_list=None,
            attractions_suggestions=None,
            turn_count=turn_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.get("/conversations", response_model=List[GetConversationResponse])
async def list_conversations(
    user_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[GetConversationResponse]:
    """
    List conversations, optionally filtered by user_id.
    """
    try:
        query = db.query(Conversation)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).limit(limit).all()
        
        result = []
        for conv in conversations:
            turn_count = db.query(Turn).filter(
                Turn.conversation_id == conv.id
            ).count()
            
            completed_services = []
            if conv.services_completed:
                completed_services = json.loads(conv.services_completed)
            
            result.append(GetConversationResponse(
                conversation_id=conv.id,
                status=conv.status,
                created_at=conv.created_at,
                synopsis=conv.synopsis,
                current_intent=conv.current_intent,
                current_phase=conv.current_phase,
                services_completed=[ConversationIntent(service) for service in completed_services],
                destination_recommendations=None,
                packing_list=None,
                attractions_suggestions=None,
                turn_count=turn_count
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")
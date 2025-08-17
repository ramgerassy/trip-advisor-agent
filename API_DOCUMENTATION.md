# Trip Planner Agent API Documentation

Welcome to the Trip Planner Agent API! This intelligent conversational API helps users plan their trips through three main services: destination recommendations, packing lists, and attraction suggestions.

## Table of Contents

1. [Overview](#overview)
2. [Base URL & Setup](#base-url--setup)
3. [Authentication](#authentication)
4. [Core Endpoints](#core-endpoints)
5. [Data Models](#data-models)
6. [Conversation Flow](#conversation-flow)
7. [Error Handling](#error-handling)
8. [Examples & Use Cases](#examples--use-cases)

## Overview

The Trip Planner Agent API uses a conversational approach with:
- **Intent Detection**: Automatically determines what the user wants (destination recommendations, packing lists, or attractions)
- **Data Collection**: Gathers required information through natural conversation
- **Processing**: Generates intelligent recommendations using LLM-powered tools
- **Refinement**: Allows users to modify and improve results

### Supported Services

1. **Destination Recommendations**: Find perfect travel destinations based on preferences, budget, and travel style
2. **Packing Lists**: Generate personalized packing suggestions for specific destinations and activities
3. **Attraction Suggestions**: Discover activities and attractions for a specific destination

## Base URL & Setup

```bash
# Default local development
BASE_URL="http://localhost:8000"

# Set up environment
export TRIP_API_BASE="http://localhost:8000"
```

## Authentication

Currently, the API doesn't require authentication, but you can optionally include a `user_id` for conversation tracking.

## Core Endpoints

### 1. Health Check

**GET /** - Basic health check

```bash
curl -X GET "${TRIP_API_BASE}/" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "message": "Trip Planner Agent API",
  "version": "1.0.0", 
  "status": "healthy",
  "environment": "development"
}
```

**GET /health** - Detailed health check

```bash
curl -X GET "${TRIP_API_BASE}/health" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. Start Conversation

**POST /api/v1/conversations** - Create a new conversation

#### Option A: Start with general greeting

```bash
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
```

#### Option B: Start with specific intent

```bash
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "initial_intent": "destination_recommendation"
  }'
```

#### Option C: Start with initial message (auto-detects intent)

```bash
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "initial_message": "I need help choosing a destination for my honeymoon"
  }'
```

**Response:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Great! I'll help you find the perfect destination based on your preferences, budget, and travel style.\n\nTo get started, I need to know:\n• What type of trip are you looking for? (adventure, relaxation, cultural, etc.)\n• When are you planning to travel? (specific dates or just duration)\n• Do you have any specific requirements? (climate, budget, activities)",
  "intent": "destination_recommendation",
  "phase": "data_collection",
  "next_required": ["user_preferences", "date_range", "destination_criteria"]
}
```

### 3. Send Message

**POST /api/v1/conversations/{conversation_id}/message** - Send a message to continue the conversation

```bash
# Save conversation ID from previous response
CONVERSATION_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We want a romantic destination for our honeymoon in June. We love beaches and fine dining. Budget is luxury."
  }'
```

**Response:**
```json
{
  "agent_response": "Perfect! A romantic luxury honeymoon in June with beaches and fine dining sounds wonderful. Let me find some amazing destinations for you.\n\n🏝️ **Maldives** - Overwater bungalows, world-class spas, and pristine beaches\n🏖️ **Santorini, Greece** - Stunning sunsets, luxury resorts, and excellent cuisine\n🌺 **Maui, Hawaii** - Beautiful beaches, fine dining, and romantic atmosphere\n\nWould you like more details about any of these destinations, or shall I suggest a few more options?",
  "intent": "destination_recommendation",
  "phase": "refinement",
  "next_required": [],
  "missing_slots": [],
  "tool_outputs": [],
  "uncertainty_flags": [],
  "ready_for_next_service": false
}
```

### 4. Get Conversation

**GET /api/v1/conversations/{conversation_id}** - Get conversation details and current state

```bash
curl -X GET "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "synopsis": "User seeking romantic luxury honeymoon destination for June with beaches and fine dining",
  "current_intent": "destination_recommendation",
  "current_phase": "refinement",
  "services_completed": [],
  "destination_recommendations": null,
  "packing_list": null,
  "attractions_suggestions": null,
  "turn_count": 3
}
```

### 5. Resume Conversation

**POST /api/v1/conversations/{conversation_id}/resume** - Resume an existing conversation

```bash
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/resume" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "agent_response": "Welcome back! We were discussing romantic luxury destinations for your June honeymoon. I had suggested the Maldives, Santorini, and Maui. Would you like more details about any of these, or shall I suggest additional options?",
  "intent": "destination_recommendation",
  "phase": "refinement",
  "next_required": [],
  "missing_slots": [],
  "tool_outputs": [],
  "uncertainty_flags": [],
  "ready_for_next_service": false
}
```

### 6. Get Conversation Context

**GET /api/v1/conversations/{conversation_id}/context** - Get conversation context for debugging

```bash
curl -X GET "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/context" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "intent": "destination_recommendation",
  "phase": "refinement",
  "synopsis": "User seeking romantic luxury honeymoon destination for June with beaches and fine dining",
  "turn_count": 3,
  "resumable": true
}
```

## Data Models

### Key Enums

#### ConversationIntent
- `destination_recommendation` - Find travel destinations
- `packing_list` - Generate packing suggestions  
- `attractions` - Discover activities and attractions
- `general` - General conversation (no specific intent yet)

#### ConversationPhase
- `intent_detection` - Determining what user wants
- `data_collection` - Gathering required information
- `processing` - Generating recommendations
- `refinement` - Allowing user to modify results
- `completed` - Service delivered successfully

#### ConversationStatus
- `active` - Conversation in progress
- `completed` - Conversation finished
- `abandoned` - Conversation inactive

### Request Models

#### StartConversationRequest
```json
{
  "user_id": "string (optional)",
  "initial_intent": "destination_recommendation|packing_list|attractions|general (optional)",
  "initial_message": "string (optional)"
}
```

#### SendMessageRequest
```json
{
  "message": "string (required, min_length=1)"
}
```

## Conversation Flow

### 1. Destination Recommendation Flow

```bash
# Step 1: Start conversation
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "initial_message": "I need help choosing a destination for my vacation"
  }'

# Step 2: Provide preferences
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want somewhere warm and relaxing for 2 weeks in July. Budget is mid-range and I love beaches and local culture."
  }'

# Step 3: Get recommendations and refine
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about Thailand. What are the best islands for a first-time visitor?"
  }'
```

### 2. Packing List Flow

```bash
# Step 1: Start with packing intent
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "initial_message": "I need help creating a packing list for my trip"
  }'

# Step 2: Provide trip details
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I'm going to Japan in March for 10 days. It will be 2 adults, and we plan to do city sightseeing and some hiking."
  }'

# Step 3: Get personalized packing list
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about camera gear? And do I need special hiking equipment?"
  }'
```

### 3. Attractions Flow

```bash
# Step 1: Start with attractions intent
curl -X POST "${TRIP_API_BASE}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123", 
    "initial_message": "What are the best attractions in Paris?"
  }'

# Step 2: Provide preferences
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I'm interested in museums and historical sites. I'll be there for 3 days and love art and culture."
  }'

# Step 3: Get detailed itinerary
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you suggest a day-by-day itinerary with the best museums and when to visit them?"
  }'
```

## Error Handling

### HTTP Status Codes

- **200 OK** - Request successful
- **400 Bad Request** - Invalid request data or conversation state
- **404 Not Found** - Conversation not found
- **500 Internal Server Error** - Server error

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### Common Errors

```bash
# 404 - Conversation not found
curl -X GET "${TRIP_API_BASE}/api/v1/conversations/invalid-id"
# Response: {"detail": "Conversation not found"}

# 400 - Empty message
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'
# Response: {"detail": "Message cannot be empty"}

# 400 - Inactive conversation
curl -X POST "${TRIP_API_BASE}/api/v1/conversations/completed-conversation-id/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
# Response: {"detail": "Conversation is not active"}
```

## Examples & Use Cases

### Complete Destination Recommendation Example

```bash
#!/bin/bash

# Set up
BASE_URL="http://localhost:8000"

echo "🌍 Starting destination recommendation..."

# Start conversation
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "initial_message": "I need help choosing a destination for my anniversary trip"
  }')

CONVERSATION_ID=$(echo $RESPONSE | jq -r '.conversation_id')
echo "Conversation ID: $CONVERSATION_ID"
echo "Agent: $(echo $RESPONSE | jq -r '.message')"
echo ""

# Provide trip details
echo "👤 User: We want somewhere romantic for 5 days in September. We love good food and beautiful scenery. Budget is luxury."
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We want somewhere romantic for 5 days in September. We love good food and beautiful scenery. Budget is luxury."
  }')

echo "🤖 Agent: $(echo $RESPONSE | jq -r '.agent_response')"
echo ""

# Ask for more details
echo "👤 User: Tell me more about Tuscany. What makes it special for couples?"
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about Tuscany. What makes it special for couples?"
  }')

echo "🤖 Agent: $(echo $RESPONSE | jq -r '.agent_response')"

# Get conversation summary
echo ""
echo "📊 Conversation Summary:"
curl -s -X GET "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}" \
  -H "Content-Type: application/json" | jq '{
    status: .status,
    intent: .current_intent,
    phase: .current_phase,
    turn_count: .turn_count,
    synopsis: .synopsis
  }'
```

### Multi-Service Conversation Example

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🎯 Multi-service trip planning..."

# Start with destination
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "multi-user",
    "initial_message": "Help me plan a trip to Japan"
  }')

CONVERSATION_ID=$(echo $RESPONSE | jq -r '.conversation_id')

# Get destination recommendations
curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to visit Japan in spring for cherry blossoms. 10 days, cultural experiences, moderate budget."
  }' | jq -r '.agent_response'

# Switch to packing
echo ""
echo "🎒 Switching to packing list..."
curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Great! Now I need help with packing for this Japan trip."
  }' | jq -r '.agent_response'

# Switch to attractions
echo ""
echo "🎌 Switching to attractions..."
curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONVERSATION_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Perfect! Now what are the best attractions in Tokyo and Kyoto?"
  }' | jq -r '.agent_response'
```

### Testing All Endpoints Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🧪 Testing all API endpoints..."

# Health checks
echo "1. Testing health endpoints..."
curl -s "${BASE_URL}/" | jq '.status'
curl -s "${BASE_URL}/health" | jq '.status'

# Start conversation
echo -e "\n2. Starting new conversation..."
CONV_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "initial_message": "I need travel help"}')

CONV_ID=$(echo $CONV_RESPONSE | jq -r '.conversation_id')
echo "Created conversation: $CONV_ID"

# Send message
echo -e "\n3. Sending message..."
curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONV_ID}/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to visit Paris for a weekend"}' | jq '.phase'

# Get conversation
echo -e "\n4. Getting conversation details..."
curl -s -X GET "${BASE_URL}/api/v1/conversations/${CONV_ID}" | jq '{
  id: .conversation_id,
  status: .status,
  intent: .current_intent,
  phase: .current_phase,
  turns: .turn_count
}'

# Get context
echo -e "\n5. Getting conversation context..."
curl -s -X GET "${BASE_URL}/api/v1/conversations/${CONV_ID}/context" | jq '{
  intent: .intent,
  phase: .phase,
  resumable: .resumable
}'

# Resume conversation
echo -e "\n6. Resuming conversation..."
curl -s -X POST "${BASE_URL}/api/v1/conversations/${CONV_ID}/resume" \
  -H "Content-Type: application/json" | jq '.intent'

echo -e "\n✅ All endpoints tested successfully!"
```

## Advanced Features

### Intent Auto-Detection

The API automatically detects user intent from natural language:

```bash
# These will auto-detect different intents:

# Destination intent
curl -X POST "${BASE_URL}/api/v1/conversations" \
  -d '{"initial_message": "Where should I go for vacation?"}'

# Packing intent  
curl -X POST "${BASE_URL}/api/v1/conversations" \
  -d '{"initial_message": "What should I pack for my trip?"}'

# Attractions intent
curl -X POST "${BASE_URL}/api/v1/conversations" \
  -d '{"initial_message": "What are the best things to do in London?"}'
```

### LLM-Powered Data Extraction

The system uses intelligent LLM extraction with regex fallback:

```bash
# Complex natural language is understood
curl -X POST "${BASE_URL}/api/v1/conversations/${CONV_ID}/message" \
  -d '{
    "message": "Looking for outdoor activities and nature spots near Barcelona within 50km for a family of 4 visiting in summer"
  }'

# Extracts: destination=Barcelona, travelers=4, activities=outdoor/nature, season=summer
```

### Conversation State Management

The API maintains sophisticated conversation state across turns:

```bash
# Check current state
curl -X GET "${BASE_URL}/api/v1/conversations/${CONV_ID}/context"

# Resume maintains all context
curl -X POST "${BASE_URL}/api/v1/conversations/${CONV_ID}/resume"
```

---

## Getting Started

1. **Start the API server**:
   ```bash
   cd trip-advisor-agent
   uv run uvicorn app.server.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test the health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Start your first conversation**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/conversations" \
     -H "Content-Type: application/json" \
     -d '{"initial_message": "Help me plan a trip!"}'
   ```

4. **Continue the conversation using the returned `conversation_id`**

Happy trip planning! 🌍✈️🎒
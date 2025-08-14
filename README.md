Trip Planner Agent
An orchestrated AI agent system for trip planning with structured conversation flow, weather integration, and intelligent packing recommendations.
Architecture
The system consists of:

Orchestrator Agent: Manages conversation flow through structured phases using LangChain
Validator Agent: Ensures policy compliance and schema validation
Tools Layer: Weather, city info, and packing recommendation tools
Memory System: SQLite-based conversation persistence and resumption
State Machine: Guided conversation flow: intake → clarify → draft → refine → finalize

Features

🧠 Multi-step reasoning with hidden chain-of-thought processing
📱 Structured conversation with clear phases and progress tracking
🌤️ Weather integration with real-time forecasts and travel considerations
🎒 Smart packing recommendations based on weather, activities, and constraints
💾 Conversation memory with ability to resume sessions
🔒 Policy validation for safety and scope compliance
🛠️ Tool caching with TTL for efficient API usage

Tech Stack

FastAPI - High-performance Python web framework
LangChain - AI/LLM orchestration and tool integration
SQLAlchemy - Database ORM with SQLite
Pydantic - Data validation and serialization
Ollama - Local LLM hosting (Llama 3.1 8B)

Quick Start
Prerequisites

Prerequisites

Python 3.11+
uv
Ollama with Llama 3.1 8B model

Installation
# Clone the repository
git clone <repository-url>
cd trip-planner-agent

# Install dependencies with uv
uv sync

# Or install individual packages
uv add fastapi uvicorn[standard] langchain langchain-ollama sqlalchemy pydantic python-dotenv

# Or with pip (if not using uv)
pip install -r requirements.txt

Configuration
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY or ANTHROPIC_API_KEY
# Optional: GEODB_API_KEY for enhanced city info

Database Setup
# Run migrations to create tables
uv run python -m app.database.migrate

# Or with python directly
python -m app.database.migrate

Running the Server
# Development mode with auto-reload
uv run uvicorn app.server.main:app --reload --host 0.0.0.0 --port 8000

# Or with uvicorn directly
uvicorn app.server.main:app --reload --host 0.0.0.0 --port 8000

The API will be available at http://localhost:8000
Interactive docs: http://localhost:8000/docs
API Usage
Start a Conversation

curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "optional-user-id"}'

Send a Message
curl -X POST "http://localhost:8000/api/v1/conversations/{conversation_id}/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to plan a trip to Rome in April"}'

Get Conversation Status
curl "http://localhost:8000/api/v1/conversations/{conversation_id}"

Project Structure
app/
├── agents/          # AI agents (Orchestrator, Validator)
├── tools/           # External tool integrations (Weather, City Info, Packing)
├── memory/          # Conversation persistence and state management
├── server/          # FastAPI application and routes
├── schemas/         # Pydantic data models
├── policies/        # Safety and scope validation rules
├── database/        # SQLAlchemy models and migrations
└── core/           # Configuration and shared utilities

License
MIT License - see LICENSE file for details
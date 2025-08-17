# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv
uv sync

# Create .env file from template (if .env.example exists)
cp .env.example .env
```

### Database Operations
```bash
# Run migrations to create/update database tables
uv run python -m app.database.migrate
```

### Server Operations
```bash
# Run development server with auto-reload
uv run uvicorn app.server.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
```

### Testing
```bash
# Run individual test files
uv run python test_agent.py
uv run python test_city_info.py
uv run python test_data_extraction.py
uv run python test_geocoding.py
uv run python test_llm.py
uv run python test_memory.py
uv run python test_packing.py
uv run python test_reasoning.py
uv run python test_tool_integration.py
uv run python test_validator.py
uv run python test_weather.py

# Run with pytest if available
uv run pytest test_*.py
```

### Code Quality
```bash
# Format code with black
uv run black .

# Sort imports with isort
uv run isort .

# Lint with flake8
uv run flake8 .

# Type checking with mypy
uv run mypy .
```

## Architecture Overview

This is a **multi-agent trip planning system** built with FastAPI, LangChain, and SQLAlchemy that provides structured conversation flow for travel planning services.

### Core Components

**Orchestrator Agent** (`app/agents/orchestrator.py`)
- Manages conversation flow through phases: intent detection → data collection → processing → refinement → completion
- Coordinates tool execution and response formatting
- Handles conversation resumption and state management

**State Machine** (`app/schemas/state.py`)
- Defines conversation phases and valid transitions
- Maps required data slots for each service (destination recommendations, packing lists, attractions)
- Provides prioritized questions for data collection

**Database Models** (`app/database/models.py`)
- **Conversation**: Main conversation tracking with current intent/phase
- **Turn**: Individual message exchanges
- **StateSnapshot**: Conversation state for resumption
- **ToolResult**: Tool execution results with caching

**Tools Layer** (`app/tools/`)
- Weather API integration for climate data
- City information retrieval 
- Packing list generation with weather considerations
- Modular tool architecture with caching

### Service Types

The system supports three main services:
1. **Destination Recommendations** - Find travel destinations based on preferences
2. **Packing Lists** - Generate weather-aware packing suggestions  
3. **Attractions** - Discover activities and sightseeing options

### Conversation Flow

1. **Intent Detection**: Determine what service the user wants
2. **Data Collection**: Gather required information (destination, dates, travelers, etc.)
3. **Processing**: Execute tools (weather, city info, packing) to generate recommendations
4. **Refinement**: Allow user to modify or approve results
5. **Completion**: Finalize and offer new services

### Key Files

- `app/server/main.py` - FastAPI application entry point
- `app/core/config.py` - Application settings and environment variables
- `app/core/llm_client.py` - LLM integration (Ollama/OpenAI/Anthropic)
- `app/agents/validator.py` - Input validation and safety policies
- `app/agents/data_extractor.py` - Extract structured data from user messages
- `app/schemas/internal.py` - Internal reasoning and quality check structures

### Technology Stack

- **FastAPI** - High-performance web framework
- **LangChain** - AI/LLM orchestration 
- **SQLAlchemy** - Database ORM with SQLite
- **Pydantic** - Data validation and serialization
- **uv** - Fast Python package installer and resolver

### Configuration

Environment variables are managed through `app/core/config.py`:
- LLM providers (Ollama, OpenAI, Anthropic)
- API keys for external services
- Database connection settings
- Cache TTL and rate limiting

The system defaults to local Ollama with Llama 3.1 8B but supports cloud providers as fallbacks.
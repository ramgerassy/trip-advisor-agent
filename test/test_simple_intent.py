                                                                                                                         
from app.agents.orchestrator import get_orchestrator
from app.schemas import ConversationIntent
from app.schemas.internal import ReasoningEngine


# Test minimal attractions execution
data = {'destination': 'Barcelona', 'attraction_criteria': 'beaches, museums, food'}
orchestrator = get_orchestrator()

# Test the ReasoningEngine creation
try:
    reasoning_engine = ReasoningEngine()
    print('✅ ReasoningEngine created successfully')

    # Test the attractions tool execution
    tool_results = orchestrator._execute_attractions_tools(data, reasoning_engine)
    print(f'✅ Tool results: {tool_results}')

    # Test the formatting
    response = orchestrator._format_attractions_results(tool_results, data)
    print(f'✅ Formatted response: {response[:200]}...')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"""
Test script to verify Ollama LLM connection.
"""
from app.core.llm_client import test_llm_connection, get_llm

def main():
    print("🧪 Testing Ollama LLM connection...")
    
    if test_llm_connection():
        print("✅ LLM connection successful!")
        
        # Try a simple travel-related question
        try:
            llm = get_llm()
            response = llm.invoke("What are 3 things to consider when packing for a trip?")
            print(f"\n📝 Sample response:\n{response}")
        except Exception as e:
            print(f"❌ Error getting sample response: {e}")
    else:
        print("❌ LLM connection failed!")
        print("Make sure Ollama is running and llama3.1:8b model is available")

if __name__ == "__main__":
    main()
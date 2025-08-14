"""
Test memory and resume functionality.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_memory_and_resume():
    print("💾 Testing Memory and Resume Functionality...")
    
    # Step 1: Start a conversation
    print("\n1️⃣ Starting new conversation...")
    response = requests.post(f"{BASE_URL}/conversations", json={
        "initial_message": "I need help packing for a business trip to London"
    })
    
    if response.status_code == 200:
        data = response.json()
        conversation_id = data["conversation_id"]
        print(f"✅ Started conversation: {conversation_id}")
        print(f"📝 Initial message: {data['message'][:100]}...")
    else:
        print(f"❌ Failed to start conversation: {response.status_code}")
        return
    
    # Step 2: Add some data
    print("\n2️⃣ Adding trip details...")
    response = requests.post(f"{BASE_URL}/conversations/{conversation_id}/message", json={
        "message": "I'm going to London for 3 days next week with my colleague. We'll be staying at a hotel."
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Added details, current phase: {data['phase']}")
        print(f"📝 Response: {data['agent_response'][:100]}...")
    else:
        print(f"❌ Failed to add details: {response.status_code}")
        return
    
    # Step 3: Get conversation context
    print("\n3️⃣ Checking conversation context...")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/context")
    
    if response.status_code == 200:
        context = response.json()
        print(f"✅ Context retrieved:")
        print(f"   Intent: {context['intent']}")
        print(f"   Phase: {context['phase']}")
        print(f"   Turn count: {context['turn_count']}")
        print(f"   Synopsis: {context['synopsis']}")
        print(f"   Resumable: {context['resumable']}")
    else:
        print(f"❌ Failed to get context: {response.status_code}")
        return
    
    # Step 4: Test resume
    print("\n4️⃣ Testing resume functionality...")
    response = requests.post(f"{BASE_URL}/conversations/{conversation_id}/resume")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully resumed conversation")
        print(f"📝 Resume message: {data['agent_response']}")
        print(f"🔄 Current phase: {data['phase']}")
    else:
        print(f"❌ Failed to resume: {response.status_code}")
        print(f"Error: {response.text}")
    
    # Step 5: Continue conversation after resume
    print("\n5️⃣ Continuing conversation after resume...")
    response = requests.post(f"{BASE_URL}/conversations/{conversation_id}/message", json={
        "message": "Yes, please proceed with the recommendations"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Continued successfully, phase: {data['phase']}")
        print(f"📝 Response: {data['agent_response'][:150]}...")
    else:
        print(f"❌ Failed to continue: {response.status_code}")
    
    print(f"\n🎯 Test completed for conversation: {conversation_id}")

if __name__ == "__main__":
    test_memory_and_resume()
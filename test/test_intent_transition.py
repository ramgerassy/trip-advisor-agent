#!/usr/bin/env python3
"""
Test script to verify intent transition functionality
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_intent_transition():
    """Test the exact scenario from the user's problem."""
    print("🧪 Testing Intent Transition Functionality")
    print("=" * 50)
    
    # Step 1: Start with packing list request
    print("\n1️⃣ Starting packing conversation...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations", json={
        "initial_message": "Help me pack for Barcelona for 4 days with my family"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to start conversation: {response.status_code}")
        return False
    
    data = response.json()
    conversation_id = data.get('conversation_id')
    print(f"✅ Conversation started: {conversation_id}")
    print(f"Intent: {data.get('intent')}")
    print(f"Phase: {data.get('phase')}")
    
    # Step 2: Provide family details
    print("\n2️⃣ Providing family details...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
        "message": "So as i said, we will be traveling to Barcelona. it will be a 4 days trip, our family is composed of my wife(33) me(32) and our child(2)."
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send message: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ Family details processed")
    print(f"Intent: {data.get('intent')}")
    print(f"Phase: {data.get('phase')}")
    
    # Step 3: Get packing recommendations  
    print("\n3️⃣ Getting packing recommendations...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
        "message": "Yes, please generate the packing recommendations"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to get packing recommendations: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ Packing recommendations generated")
    print(f"Intent: {data.get('intent')}")
    print(f"Phase: {data.get('phase')}")
    
    # Step 4: THE CRITICAL TEST - Request attractions (intent transition)
    print("\n4️⃣ 🎯 CRITICAL TEST: Requesting attractions (intent transition)...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
        "message": "no, its perfect! but, i would love to get some recommendations about attractions in Barcelona. we love beaches, museums and street food."
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to request attractions: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ Attractions request processed")
    print(f"Intent: {data.get('intent')}")
    print(f"Phase: {data.get('phase')}")
    
    # Check the response for quality
    response_text = data.get('agent_response', '')
    print(f"\nResponse preview: {response_text[:200]}...")
    
    # Verify the intent transition worked correctly
    if data.get('intent') == 'attractions':
        print("\n✅ SUCCESS: Intent correctly transitioned to attractions!")
        
        # Check for Barcelona context (not Tokyo!)
        if 'barcelona' in response_text.lower() and 'tokyo' not in response_text.lower():
            print("✅ SUCCESS: Response correctly mentions Barcelona (no Tokyo contamination)")
            
            # Check for family context
            if any(word in response_text.lower() for word in ['family', 'child', 'kid', '2-year']):
                print("✅ SUCCESS: Family context preserved from packing conversation")
            else:
                print("⚠️ WARNING: Family context not preserved")
            
            # Check for mentioned interests
            if any(word in response_text.lower() for word in ['beach', 'museum', 'food']):
                print("✅ SUCCESS: User interests (beaches, museums, food) recognized")
            else:
                print("⚠️ WARNING: User interests not clearly addressed")
                
            return True
        else:
            print("❌ FAILURE: Response mentions wrong destination or has context contamination")
            print(f"Full response: {response_text}")
            return False
    else:
        print(f"❌ FAILURE: Intent did not transition correctly. Still: {data.get('intent')}")
        print(f"Full response: {response_text}")
        return False

def test_mid_conversation_intent_change():
    """Test abrupt intent change mid-conversation."""
    print("\n\n🧪 Testing Mid-Conversation Intent Change")
    print("=" * 50)
    
    # Start destination conversation
    print("\n1️⃣ Starting destination conversation...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations", json={
        "initial_message": "I need help choosing a destination for my vacation"
    })
    
    data = response.json()
    conversation_id = data.get('conversation_id')
    print(f"✅ Started destination conversation: {data.get('intent')}")
    
    # Suddenly switch to packing
    print("\n2️⃣ Suddenly switching to packing...")
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
        "message": "Actually, I already know where I'm going. I need help packing for Japan."
    })
    
    data = response.json()
    print(f"✅ Intent change processed")
    print(f"New intent: {data.get('intent')}")
    print(f"Response: {data.get('agent_response')[:150]}...")
    
    return data.get('intent') == 'packing_list'

def main():
    """Run all intent transition tests."""
    print(f"🎯 Intent Transition Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is reachable")
        else:
            print("⚠️ API returned non-200 status")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        print("Please ensure API is running: uv run uvicorn app.server.main:app --reload")
        return 1
    
    # Run tests
    test1_success = test_intent_transition()
    test2_success = test_mid_conversation_intent_change()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Natural Transition Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Mid-Conversation Change Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All intent transition tests passed!")
        print("The Barcelona → Attractions bug should now be fixed!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
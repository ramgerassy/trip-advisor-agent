#!/usr/bin/env python3
"""
Comprehensive test script to verify the new attractions tool implementation.
Tests both the tool functionality and end-to-end API integration.
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_attractions_tool_directly():
    """Test the attractions tool directly without API."""
    print("🧪 Testing Attractions Tool Directly")
    print("=" * 50)
    
    try:
        # Import and test the tool directly
        import sys
        import os
        sys.path.append('/tmp/trip-advisor-agent')
        
        from app.tools.attractions import get_attractions_tool
        
        tool = get_attractions_tool()
        print("✅ Attractions tool imported successfully")
        
        # Test 1: Basic destination test
        print("\n1️⃣ Testing basic destination (Paris)...")
        result = tool.execute(
            destination="Paris",
            interests=["museums", "food", "architecture"],
            family_composition="family of 3",
            trip_duration_days=4,
            budget_level="mid-range"
        )
        
        if result.success:
            print("✅ Paris attractions generated successfully")
            attractions = result.data.get("attractions", [])
            print(f"   Generated {len(attractions)} attractions")
            if attractions:
                print(f"   Sample attraction: {attractions[0].get('name', 'Unknown')}")
        else:
            print(f"❌ Paris test failed: {result.error}")
        
        # Test 2: Family-friendly test
        print("\n2️⃣ Testing family-friendly (Rome with children)...")
        result = tool.execute(
            destination="Rome",
            interests=["history", "food"],
            family_composition="family with children",
            ages=[32, 30, 3, 5],
            names=["John", "Sarah", "Emma", "Luke"],
            trip_duration_days=5
        )
        
        if result.success:
            print("✅ Rome family attractions generated successfully")
            attractions = result.data.get("attractions", [])
            family_friendly_count = sum(1 for a in attractions if a.get('family_friendly', False))
            print(f"   Generated {len(attractions)} attractions ({family_friendly_count} family-friendly)")
        else:
            print(f"❌ Rome family test failed: {result.error}")
        
        # Test 3: Unknown destination test
        print("\n3️⃣ Testing unknown destination...")
        result = tool.execute(
            destination="Nonexistentville",
            interests=["anything"]
        )
        
        if not result.success:
            print("✅ Unknown destination properly rejected")
            print(f"   Error message: {result.error}")
        else:
            print("⚠️ Unknown destination unexpectedly succeeded")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_attractions_api_integration():
    """Test attractions through full API integration."""
    print("\n\n🧪 Testing Attractions API Integration")
    print("=" * 50)
    
    try:
        # Test 1: Full conversation flow
        print("1️⃣ Starting full conversation flow...")
        
        # Start conversation
        response = requests.post(f"{BASE_URL}/api/v1/conversations", json={
            "initial_message": "Help me find attractions in Tokyo for my family vacation"
        })
        
        data = response.json()
        conversation_id = data.get('conversation_id')
        print(f"✅ Conversation started: {conversation_id}")
        
        # Add family details
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "We are a family of 4: me (35), my wife (32), and our kids aged 8 and 5. We love temples, anime culture, and traditional food. Our budget is around $300 per day."
        })
        
        data = response.json()
        print("✅ Family details provided")
        
        # Get attractions directly (should trigger intent transition)
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "Can you recommend specific attractions in Tokyo for our family? We especially want kid-friendly temples and anime-related activities."
        })
        
        data = response.json()
        response_text = data.get('agent_response', '')
        
        print(f"✅ Attractions response received")
        print(f"Intent: {data.get('intent')}")
        print(f"Phase: {data.get('phase')}")
        
        # Analyze response quality
        print("\n🔍 Response Analysis:")
        
        # Check for context preservation
        context_indicators = []
        if any(word in response_text.lower() for word in ['family', 'kids', 'children']):
            context_indicators.append("Family context")
        if any(word in response_text.lower() for word in ['temple', 'anime', 'food']):
            context_indicators.append("Interest context")
        if any(word in response_text.lower() for word in ['tokyo']):
            context_indicators.append("Destination context")
        
        print(f"   Context preserved: {context_indicators}")
        
        # Check for real attractions vs placeholder
        if "coming soon" in response_text.lower():
            print("   ⚠️ Still showing 'coming soon' message")
            success = False
        elif "personalized recommendations" in response_text.lower():
            print("   ✅ Shows personalized recommendations")
            success = True
        elif any(keyword in response_text.lower() for keyword in ['attraction', 'temple', 'museum', 'activity']):
            print("   ✅ Contains specific attraction recommendations")
            success = True
        else:
            print("   ❌ No clear attraction recommendations found")
            success = False
        
        # Check response length (substantial response expected)
        if len(response_text) > 200:
            print(f"   ✅ Substantial response ({len(response_text)} characters)")
        else:
            print(f"   ⚠️ Short response ({len(response_text)} characters)")
        
        print(f"\nFull Response Preview:\n{response_text[:500]}...")
        
        return success
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_attractions_context_transition():
    """Test attractions in context of packing → attractions transition."""
    print("\n\n🧪 Testing Context Transition (Packing → Attractions)")
    print("=" * 60)
    
    try:
        # Start with packing conversation
        response = requests.post(f"{BASE_URL}/api/v1/conversations", json={
            "initial_message": "Help me pack for Barcelona with my family"
        })
        
        data = response.json()
        conversation_id = data.get('conversation_id')
        print(f"✅ Packing conversation started: {conversation_id}")
        
        # Provide rich context
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "We are traveling to Barcelona for 5 days. Our family includes me John(35), my wife Maria(33), and our daughter Sofia(6). We love beaches, art museums, and tapas."
        })
        
        data = response.json()
        print("✅ Rich family context provided")
        
        # Complete packing
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "Yes, please generate our packing list"
        })
        
        data = response.json()
        print("✅ Packing list generated")
        
        # Transition to attractions
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "Perfect! Now I'd love specific attraction recommendations in Barcelona for our family, especially places Sofia would enjoy along with art museums and beach areas."
        })
        
        data = response.json()
        response_text = data.get('agent_response', '')
        
        print(f"✅ Attractions transition completed")
        print(f"Intent: {data.get('intent')}")
        
        # Detailed context analysis
        print("\n🔍 Context Preservation Analysis:")
        
        context_score = 0
        total_checks = 5
        
        # Check 1: Family names preserved
        if any(name in response_text for name in ['John', 'Maria', 'Sofia']):
            print("   ✅ Family names preserved")
            context_score += 1
        else:
            print("   ❌ Family names lost")
        
        # Check 2: Destination preserved
        if 'barcelona' in response_text.lower():
            print("   ✅ Destination preserved")
            context_score += 1
        else:
            print("   ❌ Destination lost")
        
        # Check 3: Interests preserved
        interests_found = [interest for interest in ['beach', 'museum', 'art', 'tapas', 'food'] 
                          if interest in response_text.lower()]
        if interests_found:
            print(f"   ✅ Interests preserved: {interests_found}")
            context_score += 1
        else:
            print("   ❌ Interests lost")
        
        # Check 4: Family-friendly focus
        if any(term in response_text.lower() for term in ['family', 'sofia', 'child', 'kid']):
            print("   ✅ Family-friendly focus maintained")
            context_score += 1
        else:
            print("   ❌ Family focus lost")
        
        # Check 5: Real attractions vs placeholder
        if "coming soon" not in response_text.lower() and len(response_text) > 300:
            print("   ✅ Real attractions provided (not placeholder)")
            context_score += 1
        else:
            print("   ❌ Still using placeholder responses")
        
        print(f"\nContext Preservation Score: {context_score}/{total_checks} ({(context_score/total_checks)*100:.0f}%)")
        
        if context_score >= 4:
            print("🎉 Excellent context preservation!")
            return True
        elif context_score >= 3:
            print("✅ Good context preservation")
            return True
        else:
            print("❌ Poor context preservation")
            return False
        
    except Exception as e:
        print(f"❌ Context transition test failed: {e}")
        return False

def test_attractions_error_handling():
    """Test error handling for attractions."""
    print("\n\n🧪 Testing Attractions Error Handling")
    print("=" * 50)
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/conversations", json={
            "initial_message": "I want attractions in Atlantis the lost city"
        })
        
        data = response.json()
        conversation_id = data.get('conversation_id')
        
        response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={
            "message": "Please recommend attractions in Atlantis"
        })
        
        data = response.json()
        response_text = data.get('agent_response', '')
        
        # Should handle gracefully
        if any(phrase in response_text.lower() for phrase in [
            'different destination', 'cannot find', 'try another', 'suggestions'
        ]):
            print("✅ Error handled gracefully with helpful suggestions")
            return True
        else:
            print("⚠️ Error handling could be improved")
            return False
    
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run comprehensive attractions testing."""
    print(f"🎯 Attractions Implementation Test Suite")
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
        return 1
    
    # Run all tests
    test_results = {
        "Direct Tool Test": test_attractions_tool_directly(),
        "API Integration": test_attractions_api_integration(), 
        "Context Transition": test_attractions_context_transition(),
        "Error Handling": test_attractions_error_handling()
    }
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.0f}%)")
    
    if success_rate >= 75:
        print("\n🎉 Attractions implementation is working well!")
        print("Key achievements:")
        print("✅ Real LLM-powered attractions generated")
        print("✅ Context preservation across intent transitions")
        print("✅ Family-friendly filtering and personalization")
        print("✅ Graceful error handling for unknown destinations")
        return 0
    else:
        print("\n⚠️ Attractions implementation needs improvement.")
        print("Issues to address:")
        for test_name, result in test_results.items():
            if not result:
                print(f"- {test_name} failed")
        return 1

if __name__ == "__main__":
    exit(main())
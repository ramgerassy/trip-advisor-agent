#!/usr/bin/env python3                                                                                                                                                          
"""                                                                                                                                                                             
Test script to verify context preservation during intent transitions                                                                                                            
"""                                                                                                                                                                             
import requests                                                                                                                                                                 
import json                                                                                                                                                                     
from datetime import datetime                                                                                                                                                   
                                                                                                                                                                                
BASE_URL = "http://localhost:8000"                                                                                                                                              
                                                                                                                                                                                
def test_context_preservation():                                                                                                                                                
    """Test detailed context preservation across intent transitions."""                                                                                                         
    print("🧪 Testing Context Preservation During Intent Transitions")                                                                                                          
    print("=" * 60)                                                                                                                                                             
                                                                                                                                                                                
    # Step 1: Start with detailed packing conversation                                                                                                                          
    print("\n1️⃣ Starting detailed packing conversation...")                                                                                                                    
    response = requests.post(f"{BASE_URL}/api/v1/conversations", json={                                                                                                         
        "initial_message": "Help me pack for Barcelona for 4 days with my family"                                                                                               
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    conversation_id = data.get('conversation_id')                                                                                                                               
    print(f"✅ Conversation started: {conversation_id}")                                                                                                                         
                                                                                                                                                                                
    # Step 2: Provide rich family and context details                                                                                                                           
    print("\n2️⃣ Providing rich family and context details...")                                                                                                                 
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "So as i said, we will be traveling to Barcelona. it will be a 4 days trip, our family is composed of my wife Sarah(33) me John(32) and our child Emma(2).We love cultural activities, beach time, and trying local cuisine. Our budget is mid-range, around €200 per day for the family."                                                
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    print(f"✅ Rich family details processed")                                                                                                                                   
    print(f"Response preview: {data.get('agent_response', '')[:150]}...")                                                                                                       
                                                                                                                                                                                
    # Step 3: Get packing recommendations                                                                                                                                       
    print("\n3️⃣ Getting packing recommendations...")                                                                                                                           
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "Yes, please generate the packing recommendations for our Barcelona family trip"                                                                             
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    print(f"✅ Packing recommendations generated")                                                                                                                               
                                                                                                                                                                                
    # Step 4: CRITICAL TEST - Request attractions with specific interests                                                                                                       
    print("\n4️⃣ 🎯 CRITICAL TEST: Requesting attractions with specific interests...")                                                                                          
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "Perfect! Now I would love to get some recommendations about attractions in Barcelona. As I mentioned, we love beaches, museums, and street food, and we have our 2-year-old Emma with us. Family-friendly places would be great!"                                                                                                       
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    response_text = data.get('agent_response', '')                                                                                                                              
    print(f"✅ Attractions request processed")                                                                                                                                   
    print(f"Intent: {data.get('intent')}")                                                                                                                                      
    print(f"Phase: {data.get('phase')}")                                                                                                                                        
    print(f"\nFull Response:\n{response_text}")                                                                                                                                 
                                                                                                                                                                                
    # Detailed context analysis                                                                                                                                                 
    print("\n" + "=" * 60)                                                                                                                                                      
    print("🔍 CONTEXT PRESERVATION ANALYSIS")                                                                                                                                   
    print("=" * 60)                                                                                                                                                             
                                                                                                                                                                                
    # Test 1: Family composition preservation                                                                                                                                   
    family_context_preserved = False                                                                                                                                            
    family_indicators = [                                                                                                                                                       
        "family", "emma", "2-year", "child", "toddler", "kid",                                                                                                                  
        "wife", "sarah", "john", "parents", "couple with child"                                                                                                                 
    ]                                                                                                                                                                           
    found_family_context = [indicator for indicator in family_indicators if indicator.lower() in response_text.lower()]                                                         
    if found_family_context:                                                                                                                                                    
        family_context_preserved = True                                                                                                                                         
        print(f"✅ FAMILY CONTEXT: Found indicators: {found_family_context}")                                                                                                    
    else:                                                                                                                                                                       
        print(f"❌ FAMILY CONTEXT: No family indicators found")                                                                                                                  
                                                                                                                                                                                
    # Test 2: Specific interests preservation                                                                                                                                   
    interests_preserved = False                                                                                                                                                 
    interest_indicators = [                                                                                                                                                     
        "beach", "museum", "cultural", "cuisine", "food", "street food",                                                                                                        
        "local food", "family-friendly", "kid-friendly", "toddler-friendly"                                                                                                     
    ]                                                                                                                                                                           
    found_interests = [interest for interest in interest_indicators if interest.lower() in response_text.lower()]                                                               
    if len(found_interests) >= 2:  # At least 2 interests mentioned                                                                                                             
        interests_preserved = True                                                                                                                                              
        print(f"✅ INTERESTS: Found indicators: {found_interests}")                                                                                                              
    else:                                                                                                                                                                       
        print(f"❌ INTERESTS: Limited interest indicators: {found_interests}")                                                                                                   
                                                                                                                                                                                
    # Test 3: Budget context preservation                                                                                                                                       
    budget_preserved = False                                                                                                                                                    
    budget_indicators = ["budget", "€200", "mid-range", "affordable", "cost", "price"]                                                                                          
    found_budget = [indicator for indicator in budget_indicators if indicator.lower() in response_text.lower()]                                                                 
    if found_budget:                                                                                                                                                            
        budget_preserved = True                                                                                                                                                 
        print(f"✅ BUDGET CONTEXT: Found indicators: {found_budget}")                                                                                                            
    else:                                                                                                                                                                       
        print(f"⚠️ BUDGET CONTEXT: No budget indicators found")                                                                                                                 
                                                                                                                                                                                
    # Test 4: Names preservation (most specific)                                                                                                                                
    names_preserved = False                                                                                                                                                     
    name_indicators = ["emma", "sarah", "john"]                                                                                                                                 
    found_names = [name for name in name_indicators if name.lower() in response_text.lower()]                                                                                   
    if found_names:                                                                                                                                                             
        names_preserved = True                                                                                                                                                  
        print(f"✅ PERSONAL NAMES: Found: {found_names}")                                                                                                                        
    else:                                                                                                                                                                       
        print(f"❌ PERSONAL NAMES: No personal names found")                                                                                                                     
                                                                                                                                                                                
    # Test 5: Trip duration context                                                                                                                                             
    duration_preserved = False                                                                                                                                                  
    duration_indicators = ["4 days", "four days", "4-day", "short trip"]                                                                                                        
    found_duration = [indicator for indicator in duration_indicators if indicator.lower() in response_text.lower()]                                                             
    if found_duration:                                                                                                                                                          
        duration_preserved = True                                                                                                                                               
        print(f"✅ TRIP DURATION: Found: {found_duration}")                                                                                                                      
    else:                                                                                                                                                                       
        print(f"⚠️ TRIP DURATION: No duration indicators found")                                                                                                                
                                                                                                                                                                                
    # Overall assessment                                                                                                                                                        
    print("\n" + "=" * 60)                                                                                                                                                      
    print("📊 CONTEXT PRESERVATION SUMMARY")                                                                                                                                    
    print("=" * 60)                                                                                                                                                             
                                                                                                                                                                                
    context_scores = {                                                                                                                                                          
        "Family Context": family_context_preserved,                                                                                                                             
        "Interest Preferences": interests_preserved,                                                                                                                            
        "Budget Information": budget_preserved,                                                                                                                                 
        "Personal Names": names_preserved,                                                                                                                                      
        "Trip Duration": duration_preserved                                                                                                                                     
    }                                                                                                                                                                           
                                                                                                                                                                                
    passed_tests = sum(context_scores.values())                                                                                                                                 
    total_tests = len(context_scores)                                                                                                                                           
                                                                                                                                                                                
    for context_type, preserved in context_scores.items():                                                                                                                      
        status = "✅ PRESERVED" if preserved else "❌ LOST"                                                                                                                      

        print(f"{context_type}: {status}")                                                                                                                                      
                                                                                                                                                                                
    print(f"\nOverall Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")                                                                             
                                                                                                                                                                                
    if passed_tests >= 3:                                                                                                                                                       
        print("✅ GOOD: Most context preserved")                                                                                                                                 
        return True                                                                                                                                                             
    elif passed_tests >= 2:                                                                                                                                                     
        print("⚠️ FAIR: Some context preserved, needs improvement")                                                                                                             
        return False                                                                                                                                                            
    else:                                                                                                                                                                       
        print("❌ POOR: Major context loss detected")                                                                                                                            
        return False                                                                                                                                                            
                                                                                                                                                                                
def test_data_extraction_during_transition():                                                                                                                                   
    """Test what data is actually extracted and shared during transition."""                                                                                                    
    print("\n\n🧪 Testing Data Extraction During Transition")                                                                                                                   
    print("=" * 60)                                                                                                                                                             
                                                                                                                                                                                
    # Start fresh conversation                                                                                                                                                  
    response = requests.post(f"{BASE_URL}/api/v1/conversations", json={                                                                                                         
        "initial_message": "Help me pack for Rome for 5 days. We're a family of 4: myself, my partner, and our twin boys aged 3."                                               
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    conversation_id = data.get('conversation_id')                                                                                                                               
                                                                                                                                                                                
    # Add more context                                                                                                                                                          
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "We enjoy outdoor activities, historical sites, and authentic Italian food. Budget is around €150-250 per day."                                              
    })                                                                                                                                                                          
                                                                                                                                                                                
    # Complete packing phase                                                                                                                                                    
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "Please generate our packing list for Rome"                                                                                                                  
    })                                                                                                                                                                          
                                                                                                                                                                                
    # Transition to attractions                                                                                                                                                 
    response = requests.post(f"{BASE_URL}/api/v1/conversations/{conversation_id}/message", json={                                                                               
        "message": "Great packing list! Now can you recommend family-friendly attractions in Rome for our twin boys?"                                                           
    })                                                                                                                                                                          
                                                                                                                                                                                
    data = response.json()                                                                                                                                                      
    response_text = data.get('agent_response', '')                                                                                                                              
                                                                                                                                                                                
    print(f"Transition Response:\n{response_text}")                                                                                                                             
                                                                                                                                                                                
    # Check for shared data indicators                                                                                                                                          
    shared_data_found = []                                                                                                                                                      
    if "twin" in response_text.lower() or "boys" in response_text.lower():                                                                                                      
        shared_data_found.append("Children details")                                                                                                                            
    if "family" in response_text.lower():                                                                                                                                       
        shared_data_found.append("Family context")                                                                                                                              
    if "historical" in response_text.lower() or "outdoor" in response_text.lower():                                                                                             
        shared_data_found.append("Activity preferences")                                                                                                                        
    if "budget" in response_text.lower() or "€" in response_text:                                                                                                               
        shared_data_found.append("Budget context")                                                                                                                              
                                                                                                                                                                                
    print(f"\nShared Data Found: {shared_data_found}")                                                                                                                          
                                                                                                                                                                                
    return len(shared_data_found) >= 2                                                                                                                                          
                                                                                                                                                                                
def main():                                                                                                                                                                     
    """Run context preservation tests."""                                                                                                                                       
    print(f"🎯 Context Preservation Test Suite")                                                                                                                                
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
                                                                                                                                                                                
    # Run tests                                                                                                                                                                 
    test1_success = test_context_preservation()                                                                                                                                 
    test2_success = test_data_extraction_during_transition()                                                                                                                    
                                                                                                                                                                                
    # Final summary                                                                                                                                                             
    print("\n" + "=" * 60)                                                                                                                                                      
    print("📊 FINAL TEST SUMMARY")                                                                                                                                              
    print("=" * 60)                                                                                                                                                             
    print(f"Context Preservation Test: {'✅ PASS' if test1_success else '❌ FAIL'}")                                                                                             

    print(f"Data Extraction Test: {'✅ PASS' if test2_success else '❌ FAIL'}")                                                                                                  

                                                                                                                                                                                
    if test1_success and test2_success:                                                                                                                                         
        print("\n🎉 All context preservation tests passed!")                                                                                                                    
        return 0                                                                                                                                                                
    else:                                                                                                                                                                       
        print("\n⚠️ Context preservation needs improvement.")                                                                                                                   
        print("\nIssues to address:")                                                                                                                                           
        if not test1_success:                                                                                                                                                   
            print("- Family details, interests, and personal context not preserved")                                                                                            
        if not test2_success:                                                                                                                                                   
            print("- Data extraction during transitions insufficient")                                                                                                          
        return 1                                                                                                                                                                
                                                                                                                                                                                
if __name__ == "__main__":                                                                                                                                                      
    exit(main())
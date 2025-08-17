"""
Test the data extraction functionality.
"""
from app.agents.data_extractor import get_data_extractor
from app.schemas import ConversationIntent

def test_data_extraction():
    extractor = get_data_extractor()
    
    print("🔍 Testing Data Extraction...")
    
    # Test 1: Packing list extraction
    print("\n🎒 Test 1: Packing list data extraction")
    message1 = "I'm going to Paris for 5 days with my wife. We'll be staying at a hotel and plan to do sightseeing and visit museums."
    
    result1 = extractor.extract_travel_data(
        message1, 
        ConversationIntent.PACKING_LIST
    )
    
    print(f"📝 Message: {message1}")
    print(f"📊 Extracted data: {result1}")
    
    missing1 = extractor.get_missing_critical_slots(
        ConversationIntent.PACKING_LIST, 
        result1
    )
    print(f"❓ Missing critical slots: {missing1}")
    
    # Test 2: Destination recommendation extraction
    print("\n🗺️ Test 2: Destination recommendation extraction")
    message2 = "I want to go somewhere warm for my honeymoon in June. We love beaches and romantic settings. Budget is mid-range."
    
    result2 = extractor.extract_travel_data(
        message2,
        ConversationIntent.DESTINATION_RECOMMENDATION
    )
    
    print(f"📝 Message: {message2}")
    print(f"📊 Extracted data: {result2}")
    
    missing2 = extractor.get_missing_critical_slots(
        ConversationIntent.DESTINATION_RECOMMENDATION,
        result2
    )
    print(f"❓ Missing critical slots: {missing2}")
    
    # Test 3: Incremental data building
    print("\n🔄 Test 3: Incremental data building")
    existing_data = {"destination": "Tokyo", "travelers": {"adults": 1}}
    message3 = "I'll be there for 7 days in March"
    
    result3 = extractor.extract_travel_data(
        message3,
        ConversationIntent.PACKING_LIST,
        existing_data
    )
    
    print(f"📝 Existing: {existing_data}")
    print(f"📝 New message: {message3}")
    print(f"📊 Combined data: {result3}")

if __name__ == "__main__":
    test_data_extraction()
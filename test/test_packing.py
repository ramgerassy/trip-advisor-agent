"""
Test the packing tool functionality.
"""
from app.tools.packing import get_packing_tool

def test_packing():
    packing_tool = get_packing_tool()
    
    print("🎒 Testing Packing Tool...")
    
    # Test case 1: Hot beach vacation
    print("\n🏖️ Test Case 1: Hot beach vacation (7 days)")
    result1 = packing_tool.execute(
        trip_length_days=7,
        weather_data={
            "avg_high": 32,
            "avg_low": 25,
            "max_precip_prob": 10
        },
        activities=["beach", "swimming", "sightseeing"],
        travelers={"adults": 2, "kids": 0},
        accommodation_type="hotel",
        has_laundry=True
    )
    
    if result1.success:
        print("✅ Packing list generated successfully!")
        print(f"📊 Total items: {result1.data['total_items']}")
        print(f"🌡️ Climate: {result1.data['trip_summary']['climate']}")
        print(f"☔ Rain risk: {result1.data['trip_summary']['rain_risk']}")
        print(f"📝 Weather notes: {result1.data['weather_considerations']}")
        
        # Show clothing category
        print("\n👕 Clothing recommendations:")
        for item in result1.data['categories']['clothing'][:5]:  # First 5 items
            print(f"   • {item['name']}: {item['qty']} ({item['reason']})")
        
        # Show footwear
        print("\n👟 Footwear recommendations:")
        for item in result1.data['categories']['footwear']:
            print(f"   • {item['name']}: {item['qty']} ({item['reason']})")
    else:
        print(f"❌ Failed: {result1.error}")
    
    # Test case 2: Cold winter trip
    print("\n🏔️ Test Case 2: Cold winter trip (3 days)")
    result2 = packing_tool.execute(
        trip_length_days=3,
        weather_data={
            "avg_high": -2,
            "avg_low": -8,
            "max_precip_prob": 70
        },
        activities=["hiking", "sightseeing"],
        travelers={"adults": 1, "kids": 1},
        accommodation_type="hostel",
        has_laundry=False
    )
    
    if result2.success:
        print("✅ Winter packing list generated!")
        print(f"📊 Total items: {result2.data['total_items']}")
        print(f"🌡️ Climate: {result2.data['trip_summary']['climate']}")
        print(f"📝 Weather notes: {result2.data['weather_considerations']}")
        
        # Show some winter-specific items
        all_items = []
        for category in result2.data['categories'].values():
            all_items.extend(category)
        
        winter_items = [item for item in all_items if any(word in item['name'].lower() 
                       for word in ['warm', 'thermal', 'gloves', 'hat', 'boot'])]
        
        print("\n🧥 Winter-specific items:")
        for item in winter_items:
            print(f"   • {item['name']}: {item['qty']} ({item['reason']})")
    else:
        print(f"❌ Failed: {result2.error}")
    
    # Test case 3: Local camping trip (your example!)
    print("\n🏕️ Test Case 3: Local camping trip (2 days)")
    result3 = packing_tool.execute(
        trip_length_days=2,
        weather_data={
            "avg_high": 22,
            "avg_low": 12,
            "max_precip_prob": 20
        },
        activities=["camping", "hiking"],
        travelers={"adults": 2, "kids": 2},
        accommodation_type="camping",
        has_laundry=False,
        is_international=False,        # Domestic trip
        requires_flight=False,         # Driving there
        requires_accommodation_booking=False  # No hotel booking needed
    )
    
    if result3.success:
        print("✅ Local camping list generated!")
        print(f"📊 Total items: {result3.data['total_items']}")
        
        # Show documents for local trip
        print("\n📄 Documents for local camping:")
        for item in result3.data['categories']['documents']:
            print(f"   • {item['name']}: {item['qty']} ({item['reason']})")
    else:
        print(f"❌ Failed: {result3.error}")
    
    # Test case 4: Invalid input
    print("\n🚫 Test Case 4: Invalid input")
    result4 = packing_tool.execute(
        trip_length_days=-5,  # Invalid
        weather_data={},
        activities=[],
        travelers={"adults": 1}
    )
    
    print(f"🔍 Invalid input handled: {'✅' if not result4.success else '❌'}")
    if not result4.success:
        print(f"   Error: {result4.error}")

if __name__ == "__main__":
    test_packing()
"""
Test tool integration directly.
"""
from datetime import date, timedelta
from app.tools.weather import get_weather_tool
from app.tools.city_info import get_city_info_tool  
from app.tools.packing import get_packing_tool

def test_tools_directly():
    print("🔧 Testing Tool Integration Directly...")
    
    # Test 1: Weather tool
    print("\n🌤️ Testing Weather Tool...")
    try:
        weather_tool = get_weather_tool()
        
        # Use dates one week from now
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=4)
        
        result = weather_tool.execute(
            city="Tokyo",
            start_date=start.isoformat(),
            end_date=end.isoformat()
        )
        
        if result.success:
            print(f"✅ Weather: {result.data['summary']}")
            print(f"   Temp: {result.data['avg_low']:.1f}°C - {result.data['avg_high']:.1f}°C")
        else:
            print(f"❌ Weather failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Weather tool error: {e}")
    
    # Test 2: City Info tool
    print("\n🏙️ Testing City Info Tool...")
    try:
        city_tool = get_city_info_tool()
        result = city_tool.execute(city="Tokyo")
        
        if result.success:
            print(f"✅ City info: {result.data['overview'][:100]}...")
        else:
            print(f"❌ City info failed: {result.error}")
            
    except Exception as e:
        print(f"❌ City info tool error: {e}")
    
    # Test 3: Packing tool
    print("\n🎒 Testing Packing Tool...")
    try:
        packing_tool = get_packing_tool()
        
        weather_data = {
            "avg_high": 22, "avg_low": 12, "max_precip_prob": 20
        }
        
        result = packing_tool.execute(
            trip_length_days=5,
            weather_data=weather_data,
            activities=["sightseeing", "temples"],
            travelers={"adults": 2, "kids": 0},
            accommodation_type="hotel",
            has_laundry=False
        )
        
        if result.success:
            print(f"✅ Packing: {result.data['total_items']} items generated")
            # Show a few items
            clothing = result.data['categories'].get('clothing', [])
            if clothing:
                print(f"   Sample: {clothing[0]['name']} x{clothing[0]['qty']}")
        else:
            print(f"❌ Packing failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Packing tool error: {e}")

if __name__ == "__main__":
    test_tools_directly()
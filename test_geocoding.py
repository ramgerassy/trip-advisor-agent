"""
Test geocoding functionality (API + LLM fallback).
"""
from app.tools.weather import get_weather_tool

def test_geocoding():
    weather_tool = get_weather_tool()
    
    print("🗺️ Testing Geocoding (API + LLM Fallback)...")
    
    # Test cities
    test_cities = [
        "Paris",           # Should work with API
        "Tokyo",           # Should work with API
        "NYC",             # API might not recognize, LLM should
        "NonExistentCity12345",  # Both should fail
    ]
    
    for city in test_cities:
        print(f"\n📍 Testing: {city}")
        lat, lon, name = weather_tool._get_coordinates(city)
        
        if lat is not None and lon is not None:
            print(f"   ✅ Success: {name}")
            print(f"   📊 Coordinates: {lat:.4f}, {lon:.4f}")
            
            # Basic validation
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                print(f"   ✅ Coordinates valid")
            else:
                print(f"   ❌ Invalid coordinates!")
        else:
            print(f"   ❌ Failed: {name}")
    
    # Test LLM directly
    print(f"\n🤖 Testing LLM geocoding directly...")
    lat, lon, name = weather_tool._get_coordinates_from_llm("London")
    if lat is not None:
        print(f"   ✅ LLM found London: {name} at {lat:.4f}, {lon:.4f}")
    else:
        print(f"   ❌ LLM failed: {name}")

if __name__ == "__main__":
    test_geocoding()
"""
Test the weather tool functionality.
"""
from datetime import date, timedelta
from app.tools.weather import get_weather_tool

def test_weather():
    weather_tool = get_weather_tool()
    
    # Test dates (tomorrow for 3 days)
    tomorrow = date.today() + timedelta(days=1)
    end_date = tomorrow + timedelta(days=2)
    
    start_date_str = tomorrow.isoformat()
    end_date_str = end_date.isoformat()
    
    print("🌤️ Testing Weather Tool...")
    print(f"Getting weather for Paris from {start_date_str} to {end_date_str}")
    
    # Test 1: Valid request
    result = weather_tool.execute(
        city="Paris",
        start_date=start_date_str,
        end_date=end_date_str
    )
    
    if result.success:
        print("✅ Weather API call successful!")
        print(f"📍 Location: {result.data['location']}")
        print(f"📊 Summary: {result.data['summary']}")
        print(f"🌡️ Avg High: {result.data['avg_high']}°C")
        print(f"🌡️ Avg Low: {result.data['avg_low']}°C")
        print(f"🌧️ Max Rain Chance: {result.data['max_precip_prob']}%")
        print(f"💾 Cached: {result.cached}")
        
        print("\n📅 Daily forecast:")
        for day in result.data['daily']:
            print(f"  {day['date']}: {day['tmin']}°C - {day['tmax']}°C, "
                  f"{day['precip_prob']}% rain, {day['conditions']}")
        
        # Test 2: Cache (same request should be cached)
        print(f"\n🔄 Testing cache...")
        result2 = weather_tool.execute(
            city="Paris",
            start_date=start_date_str,
            end_date=end_date_str
        )
        print(f"💾 Second call cached: {result2.cached}")
    else:
        print(f"❌ Weather API call failed: {result.error}")
    
    # Test 3: Invalid city
    print(f"\n🔍 Testing invalid city...")
    result3 = weather_tool.execute(
        city="NonExistentCity12345",
        start_date=start_date_str,
        end_date=end_date_str
    )
    print(f"🚫 Invalid city result: {'✅ Failed as expected' if not result3.success else '❌ Should have failed'}")
    if not result3.success:
        print(f"   Error: {result3.error}")

if __name__ == "__main__":
    test_weather()
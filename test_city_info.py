"""
Test the city info tool functionality.
"""
from app.tools.city_info import get_city_info_tool

def test_city_info():
    city_tool = get_city_info_tool()
    
    print("🏙️ Testing City Info Tool...")
    
    # Test cities
    test_cities = [
        "Paris",           # Should work with Wikipedia API
        "Rome",            # Should work with Wikipedia API
        "NYC",             # Might need LLM fallback
        "NonExistentCity", # Both should fail but provide fallback
    ]
    
    for city in test_cities:
        print(f"\n📍 Testing: {city}")
        result = city_tool.execute(city=city)
        
        if result.success:
            print(f"   ✅ Success ({result.confidence} confidence)")
            print(f"   📄 Source: {result.data.get('source', 'unknown')}")
            print(f"   📝 Overview: {result.data['overview'][:100]}...")
            
            if result.data.get('highlights'):
                print(f"   🎯 Highlights: {', '.join(result.data['highlights'][:3])}")
            
            if result.data.get('best_months'):
                print(f"   📅 Best months: {', '.join(result.data['best_months'])}")
            
            if result.data.get('caution'):
                print(f"   ⚠️ Caution: {', '.join(result.data['caution'])}")
                
            print(f"   💾 Cached: {result.cached}")
        else:
            print(f"   ❌ Failed: {result.error}")
            # Even failures should provide fallback data
            if result.data and result.data.get('overview'):
                print(f"   📝 Fallback: {result.data['overview'][:100]}...")
    
    # Test LLM directly
    print(f"\n🤖 Testing LLM city info directly...")
    success, data = city_tool._get_city_info_from_llm("Barcelona")
    if success:
        print(f"   ✅ LLM provided info for Barcelona")
        print(f"   📝 Overview: {data.get('overview', '')[:100]}...")
        if data.get('highlights'):
            print(f"   🎯 Highlights: {', '.join(data['highlights'])}")
    else:
        print(f"   ❌ LLM failed: {data.get('error', 'unknown error')}")
    
    # Test caching
    print(f"\n🔄 Testing cache...")
    result2 = city_tool.execute(city="Paris")
    print(f"💾 Second Paris call cached: {result2.cached}")

if __name__ == "__main__":
    test_city_info()
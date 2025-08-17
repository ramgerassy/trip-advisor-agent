#!/usr/bin/env python3
"""
Master script to run all API test scenarios
"""
import subprocess
import sys
import time
from datetime import datetime

def run_scenario(script_name, description):
    """Run a specific scenario script."""
    print(f"\n{'='*60}")
    print(f"🚀 Starting {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Last 500 chars
        else:
            print(f"❌ {description} failed")
            print("Error:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"💥 {description} crashed: {e}")
        return False

def main():
    """Run all test scenarios."""
    print("🎯 Trip Planner API - Complete Test Suite")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if API is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("⚠️ API server returned non-200 status")
    except Exception as e:
        print(f"❌ Cannot reach API server: {e}")
        print("\nPlease start the API server first:")
        print("  uv run uvicorn app.server.main:app --reload --host 0.0.0.0 --port 8000")
        return 1
    
    scenarios = [
        ("scenario_1_destination_planning.py", "Scenario 1: Destination Planning"),
        ("scenario_2_packing_list.py", "Scenario 2: Packing List Generation"),
        ("scenario_3_attraction_recommendations.py", "Scenario 3: Attraction Recommendations"),
        ("scenario_4_problematic_requests.py", "Scenario 4: Problematic Requests (Security Testing)"),
        ("scenario_5_multi_service.py", "Scenario 5: Multi-Service Journey")
    ]
    
    results = []
    start_time = time.time()
    
    for script, description in scenarios:
        success = run_scenario(script, description)
        results.append((description, success))
        time.sleep(2)  # Brief pause between scenarios
    
    end_time = time.time()
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
    
    print(f"\n📈 Results: {successful}/{total} scenarios passed")
    print(f"⏱️ Total time: {end_time - start_time:.1f} seconds")
    
    if successful == total:
        print("\n🎉 All scenarios completed successfully!")
        print("\nGenerated documentation files:")
        print("  - scenario_1_destination_planning_results.md")
        print("  - scenario_2_packing_list_results.md") 
        print("  - scenario_3_attraction_recommendations_results.md")
        print("  - scenario_4_problematic_requests_results.md")
        print("  - scenario_5_multi_service_results.md")
    else:
        print(f"\n⚠️ {total - successful} scenario(s) failed")
    
    return 0 if successful == total else 1

if __name__ == "__main__":
    exit(main())
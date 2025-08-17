#!/usr/bin/env python3
"""
Trip Planner Agent Test Suite
Tests all conversation flows using httpx
"""
import asyncio
import json
from typing import Dict, Any, Optional
import httpx
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """Test result container."""
    test_name: str
    success: bool
    conversation_id: Optional[str] = None
    error: Optional[str] = None
    responses: list = None
    
    def __post_init__(self):
        if self.responses is None:
            self.responses = []


class TripPlannerTester:
    """Test suite for Trip Planner Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def start_conversation(self, initial_message: str) -> Dict[str, Any]:
        """Start a new conversation."""
        response = await self.client.post(
            f"{self.base_url}/conversations",
            json={"initial_message": initial_message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    async def send_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Send a message to an existing conversation."""
        response = await self.client.post(
            f"{self.base_url}/conversations/{conversation_id}/message",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    async def resume_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Resume a conversation."""
        response = await self.client.post(
            f"{self.base_url}/conversations/{conversation_id}/resume",
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context."""
        response = await self.client.get(
            f"{self.base_url}/conversations/{conversation_id}/context"
        )
        response.raise_for_status()
        return response.json()
    
    def log_response(self, step: str, response: Dict[str, Any]):
        """Log a response for debugging."""
        print(f"\n🔄 {step}")
        print("-" * 50)
        if "agent_response" in response:
            print(f"Agent: {response['agent_response'][:200]}{'...' if len(response['agent_response']) > 200 else ''}")
        elif "message" in response:
            print(f"Agent: {response['message'][:200]}{'...' if len(response['message']) > 200 else ''}")
        print(f"Intent: {response.get('intent', 'N/A')}")
        print(f"Phase: {response.get('phase', 'N/A')}")
    
    async def test_packing_list_flow(self) -> TestResult:
        """Test complete packing list flow."""
        test_name = "Packing List Flow"
        print(f"\n🧳 Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            
            # Start conversation
            response = await self.start_conversation(
                "I need a packing list for Delhi for 3 days"
            )
            conversation_id = response["conversation_id"]
            responses.append(response)
            self.log_response("Started packing conversation", response)
            
            # Add travel details
            response = await self.send_message(
                conversation_id,
                "I will be traveling alone for a business event, staying at a hotel"
            )
            responses.append(response)
            self.log_response("Added travel details", response)
            
            # Add specific dates and destination
            response = await self.send_message(
                conversation_id,
                "I will be in Delhi, India from August 17th for 3 days"
            )
            responses.append(response)
            self.log_response("Added dates and destination", response)
            
            # Request packing recommendations
            response = await self.send_message(
                conversation_id,
                "Please generate the packing recommendations"
            )
            responses.append(response)
            self.log_response("Generated packing list", response)
            
            # Check if we got a proper packing list
            has_packing_items = "items" in response.get("agent_response", "").lower()
            
            return TestResult(
                test_name=test_name,
                success=has_packing_items,
                conversation_id=conversation_id,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def test_destination_recommendation_flow(self) -> TestResult:
        """Test destination recommendation flow."""
        test_name = "Destination Recommendations"
        print(f"\n🌍 Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            
            # Start conversation
            response = await self.start_conversation(
                "I need help choosing a destination for my honeymoon"
            )
            conversation_id = response["conversation_id"]
            responses.append(response)
            self.log_response("Started destination conversation", response)
            
            # Add preferences
            response = await self.send_message(
                conversation_id,
                "We want a romantic, warm destination with beautiful sunsets and luxury resorts. Budget is no limit for 10 days in June."
            )
            responses.append(response)
            self.log_response("Added preferences", response)
            
            # Add traveler details
            response = await self.send_message(
                conversation_id,
                "We are 2 adults who love spa treatments, fine dining, and private beach access."
            )
            responses.append(response)
            self.log_response("Added traveler details", response)
            
            # Request recommendations
            response = await self.send_message(
                conversation_id,
                "Please recommend some destinations for us"
            )
            responses.append(response)
            self.log_response("Requested recommendations", response)
            
            # Check if we got to processing phase
            reached_processing = any(r.get("phase") == "processing" for r in responses)
            
            return TestResult(
                test_name=test_name,
                success=reached_processing,
                conversation_id=conversation_id,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def test_attractions_flow(self) -> TestResult:
        """Test attractions and activities flow."""
        test_name = "Attractions & Activities"
        print(f"\n🎯 Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            
            # Start conversation
            response = await self.start_conversation(
                "What are the best things to do in Tokyo?"
            )
            conversation_id = response["conversation_id"]
            responses.append(response)
            self.log_response("Started attractions conversation", response)
            
            # Add visit details
            response = await self.send_message(
                conversation_id,
                "I will be visiting for 4 days. I love museums, traditional culture, and trying local food."
            )
            responses.append(response)
            self.log_response("Added visit details", response)
            
            # Request itinerary
            response = await self.send_message(
                conversation_id,
                "Can you suggest a daily itinerary with must-see attractions?"
            )
            responses.append(response)
            self.log_response("Requested itinerary", response)
            
            # Check if we got city info
            has_city_info = "tokyo" in response.get("agent_response", "").lower()
            
            return TestResult(
                test_name=test_name,
                success=has_city_info,
                conversation_id=conversation_id,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def test_multi_service_flow(self) -> TestResult:
        """Test switching between multiple services."""
        test_name = "Multi-Service Flow"
        print(f"\n🔄 Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            
            # Start with general request
            response = await self.start_conversation(
                "I need help planning a complete trip - destination, activities, and packing"
            )
            conversation_id = response["conversation_id"]
            responses.append(response)
            self.log_response("Started multi-service conversation", response)
            
            # Provide requirements
            response = await self.send_message(
                conversation_id,
                "I want a 6-day European city break in April. I love art, history, and good food. Budget is mid-range for 2 people."
            )
            responses.append(response)
            self.log_response("Added requirements", response)
            
            # Switch to attractions after choosing destination
            response = await self.send_message(
                conversation_id,
                "Let's plan activities for Paris. What are the best art museums and historical sites?"
            )
            responses.append(response)
            self.log_response("Switched to attractions", response)
            
            # Finally ask for packing
            response = await self.send_message(
                conversation_id,
                "Now I need a packing list for Paris in April for 6 days with museum visits"
            )
            responses.append(response)
            self.log_response("Requested packing list", response)
            
            # Check if system handled service switching
            intents_used = set(r.get("intent") for r in responses if r.get("intent"))
            multi_service = len(intents_used) > 1
            
            return TestResult(
                test_name=test_name,
                success=multi_service,
                conversation_id=conversation_id,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def test_conversation_resume(self) -> TestResult:
        """Test conversation resume functionality."""
        test_name = "Conversation Resume"
        print(f"\n💾 Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            
            # Start conversation
            response = await self.start_conversation(
                "I need a packing list for Barcelona"
            )
            conversation_id = response["conversation_id"]
            responses.append(response)
            self.log_response("Started conversation", response)
            
            # Add some info
            response = await self.send_message(
                conversation_id,
                "I will be there for 4 days with my family"
            )
            responses.append(response)
            self.log_response("Added travel info", response)
            
            # Test resume
            response = await self.resume_conversation(conversation_id)
            responses.append(response)
            self.log_response("Resumed conversation", response)
            
            # Test context retrieval
            context = await self.get_conversation_context(conversation_id)
            print(f"\n📊 Conversation Context:")
            print(f"  Intent: {context.get('intent', 'N/A')}")
            print(f"  Phase: {context.get('phase', 'N/A')}")
            print(f"  Turn Count: {context.get('turn_count', 'N/A')}")
            print(f"  Synopsis: {context.get('synopsis', 'N/A')}")
            
            # Check if resume worked
            resume_success = "barcelona" in response.get("agent_response", "").lower()
            
            return TestResult(
                test_name=test_name,
                success=resume_success,
                conversation_id=conversation_id,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def test_edge_cases(self) -> TestResult:
        """Test edge cases and error handling."""
        test_name = "Edge Cases"
        print(f"\n⚠️ Testing: {test_name}")
        print("=" * 60)
        
        try:
            responses = []
            edge_case_results = []
            
            # Test 1: Unclear destination
            print("\n🔸 Testing unclear destination...")
            try:
                response = await self.start_conversation(
                    "What should I do in Randomcityname?"
                )
                responses.append(response)
                edge_case_results.append("unclear_destination_handled")
                print("✅ Unclear destination handled gracefully")
            except Exception as e:
                print(f"❌ Unclear destination failed: {e}")
            
            # Test 2: Invalid duration
            print("\n🔸 Testing invalid duration...")
            try:
                response = await self.start_conversation(
                    "I need a packing list for Tokyo for 0 days"
                )
                conv_id = response["conversation_id"]
                response2 = await self.send_message(conv_id, "Generate packing list")
                responses.extend([response, response2])
                edge_case_results.append("invalid_duration_handled")
                print("✅ Invalid duration handled gracefully")
            except Exception as e:
                print(f"❌ Invalid duration failed: {e}")
            
            # Test 3: Vague request
            print("\n🔸 Testing vague request...")
            try:
                response = await self.start_conversation(
                    "I want to travel somewhere"
                )
                responses.append(response)
                edge_case_results.append("vague_request_handled")
                print("✅ Vague request handled gracefully")
            except Exception as e:
                print(f"❌ Vague request failed: {e}")
            
            # Test 4: Invalid conversation ID
            print("\n🔸 Testing invalid conversation ID...")
            try:
                await self.send_message("invalid-id", "Hello")
                print("❌ Should have failed with invalid ID")
            except Exception:
                edge_case_results.append("invalid_id_rejected")
                print("✅ Invalid conversation ID properly rejected")
            
            success = len(edge_case_results) >= 3  # At least 3 edge cases handled
            
            return TestResult(
                test_name=test_name,
                success=success,
                responses=responses
            )
            
        except Exception as e:
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Trip Planner Agent Test Suite")
        print("=" * 80)
        print(f"Testing API at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # List of all tests
        tests = [
            self.test_packing_list_flow,
            self.test_destination_recommendation_flow,
            self.test_attractions_flow,
            self.test_multi_service_flow,
            self.test_conversation_resume,
            self.test_edge_cases
        ]
        
        # Run all tests
        for test_func in tests:
            try:
                result = await test_func()
                self.results.append(result)
            except Exception as e:
                self.results.append(TestResult(
                    test_name=test_func.__name__,
                    success=False,
                    error=str(e)
                ))
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("\n\n📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            if result.error:
                print(f"    Error: {result.error}")
            if result.conversation_id:
                print(f"    Conversation ID: {result.conversation_id}")
        
        print(f"\n📈 Overall Results: {passed}/{total} tests passed")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Your Trip Planner Agent is working correctly.")
        else:
            print(f"\n⚠️ {total-passed} test(s) failed. Check the logs above for details.")
        
        # Print conversation IDs for manual testing
        print("\n🔗 Conversation IDs for manual testing:")
        for result in self.results:
            if result.conversation_id:
                print(f"  {result.test_name}: {result.conversation_id}")


async def main():
    """Main test runner."""
    # You can change this URL if your server is running elsewhere
    tester = TripPlannerTester("http://localhost:8000/api/v1")
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
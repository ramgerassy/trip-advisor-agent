#!/usr/bin/env python3
"""
Enhanced test for attraction recommendation functionality with comprehensive logging.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.agents.orchestrator import get_orchestrator
from app.agents.data_extractor import get_data_extractor
from app.schemas import ConversationIntent, ConversationPhase, ConversationStatus
from app.schemas.state import ConversationStateManager
from app.database.models import Conversation, create_new_conversation
from app.database.connection import get_db_session

# Setup logging
def setup_test_logging():
    """Setup comprehensive logging for tests."""
    os.makedirs("logs", exist_ok=True)
    
    # Create timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Setup file handler
    log_file = f"logs/test_attraction_recommendation_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Keep console output
        ]
    )
    
    return log_file

# Setup logging for this test run
test_log_file = setup_test_logging()
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result container."""
    test_name: str
    success: bool
    error: Optional[str] = None
    conversation_data: Optional[Dict[str, Any]] = None
    agent_responses: Optional[list] = None
    detailed_log: Optional[str] = None
    
    def __post_init__(self):
        if self.agent_responses is None:
            self.agent_responses = []


class AttractionRecommendationTester:
    """Enhanced test suite for attraction recommendation functionality."""
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.data_extractor = get_data_extractor()
        self.results = []
        logger.info("=== Starting Attraction Recommendation Test Suite ===")
    
    def log_test_step(self, step: str, details: Any = None, level="INFO"):
        """Log a test step with details."""
        log_msg = f"🔄 {step}"
        print(f"\n{log_msg}")
        print("-" * 50)
        
        if level == "INFO":
            logger.info(log_msg)
        elif level == "ERROR":
            logger.error(log_msg)
        elif level == "WARNING":
            logger.warning(log_msg)
        
        if details:
            detail_str = str(details)
            if isinstance(details, str):
                detail_str = details[:200] + ('...' if len(details) > 200 else '')
                print(f"Details: {detail_str}")
            else:
                print(f"Details: {details}")
                detail_str = str(details)
            
            logger.info(f"Details: {detail_str}")
    
    def test_intent_detection(self) -> TestResult:
        """Test attraction recommendation intent detection."""
        test_name = "Attraction Intent Detection"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n🎯 Testing: {test_name}")
        print("=" * 60)
        
        try:
            test_messages = [
                "What are the best attractions in Paris?",
                "Show me things to do in Tokyo",
                "I need recommendations for activities in Rome",
                "What can I visit in Barcelona?",
                "Looking for museums in London",
                "Best sightseeing spots in Amsterdam",
                # Negative cases
                "I need help choosing a destination for my vacation",  # Should not trigger attractions intent
                "I need a packing list for Paris"  # Should not trigger attractions intent
            ]
            
            correct_detections = 0
            total_tests = len(test_messages)
            
            for i, message in enumerate(test_messages):
                logger.debug(f"Testing message {i+1}: {message}")
                intent = ConversationStateManager.detect_intent_from_message(message)
                expected_attraction = i < 6  # First 6 should be attraction intent
                
                if expected_attraction:
                    if intent == ConversationIntent.ATTRACTIONS:
                        correct_detections += 1
                        self.log_test_step(f"✅ Correctly detected attraction intent", message)
                        logger.info(f"PASS: Correctly detected attraction intent for: {message}")
                    else:
                        self.log_test_step(f"❌ Failed to detect attraction intent", f"{message} -> {intent}", "ERROR")
                        logger.error(f"FAIL: Expected attraction intent but got {intent} for: {message}")
                else:
                    if intent != ConversationIntent.ATTRACTIONS:
                        correct_detections += 1
                        self.log_test_step(f"✅ Correctly rejected attraction intent", f"{message} -> {intent}")
                        logger.info(f"PASS: Correctly rejected attraction intent for: {message}")
                    else:
                        self.log_test_step(f"❌ Incorrectly detected attraction intent", message, "ERROR")
                        logger.error(f"FAIL: Expected non-attraction intent but got attraction for: {message}")
            
            accuracy = correct_detections / total_tests
            success = accuracy >= 0.8  # 80% accuracy threshold
            
            logger.info(f"Intent detection test completed: {correct_detections}/{total_tests} correct, accuracy: {accuracy:.2%}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                conversation_data={"accuracy": accuracy, "correct": correct_detections, "total": total_tests},
                detailed_log=f"Accuracy: {accuracy:.2%}, Correct: {correct_detections}/{total_tests}"
            )
            
        except Exception as e:
            logger.exception(f"Intent detection test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_data_extraction(self) -> TestResult:
        """Test data extraction for attraction recommendations."""
        test_name = "Attraction Data Extraction"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n📊 Testing: {test_name}")
        print("=" * 60)
        
        try:
            test_cases = [
                {
                    "message": "What are the best museums and galleries in Paris? I'll be there for 3 days.",
                    "expected_fields": ["destination", "date_range"]
                },
                {
                    "message": "Show me family-friendly attractions in Tokyo for 2 adults and 2 kids visiting for a week.",
                    "expected_fields": ["destination", "travelers", "date_range"]
                },
                {
                    "message": "I'm interested in historical sites and cultural experiences in Rome.",
                    "expected_fields": ["destination", "activities_planned"]
                },
                {
                    "message": "Looking for outdoor activities and nature spots near Barcelona within 50km.",
                    "expected_fields": ["destination", "activities_planned"]
                }
            ]
            
            successful_extractions = 0
            
            for i, test_case in enumerate(test_cases):
                logger.debug(f"Testing extraction case {i+1}: {test_case['message']}")
                self.log_test_step(f"Test Case {i+1}", test_case["message"])
                
                extracted_data = self.data_extractor.extract_travel_data(
                    test_case["message"],
                    ConversationIntent.ATTRACTIONS
                )
                
                logger.debug(f"Extracted data: {extracted_data}")
                
                # Check if expected fields are present
                fields_found = 0
                for field in test_case["expected_fields"]:
                    if field in extracted_data and extracted_data[field]:
                        fields_found += 1
                        print(f"   ✅ Found {field}: {extracted_data[field]}")
                        logger.info(f"Found field {field}: {extracted_data[field]}")
                    else:
                        print(f"   ❌ Missing {field}")
                        logger.warning(f"Missing expected field: {field}")
                
                success_threshold = len(test_case["expected_fields"]) * 0.7  # 70% of expected fields
                if fields_found >= success_threshold:
                    successful_extractions += 1
                    print(f"   ✅ Extraction successful ({fields_found}/{len(test_case['expected_fields'])} fields)")
                    logger.info(f"Extraction successful for case {i+1}")
                else:
                    print(f"   ❌ Extraction failed ({fields_found}/{len(test_case['expected_fields'])} fields)")
                    logger.error(f"Extraction failed for case {i+1}")
                
                print(f"   📋 Full extracted data: {extracted_data}")
                logger.debug(f"Full extracted data for case {i+1}: {extracted_data}")
            
            success_rate = successful_extractions / len(test_cases)
            success = success_rate >= 0.7  # 70% success rate
            
            logger.info(f"Data extraction test completed: {successful_extractions}/{len(test_cases)} successful, rate: {success_rate:.2%}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                conversation_data={"success_rate": success_rate, "successful": successful_extractions, "total": len(test_cases)},
                detailed_log=f"Success rate: {success_rate:.2%}, Successful: {successful_extractions}/{len(test_cases)}"
            )
            
        except Exception as e:
            logger.exception(f"Data extraction test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_missing_slots_detection(self) -> TestResult:
        """Test detection of missing critical slots for attractions."""
        test_name = "Missing Slots Detection"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n❓ Testing: {test_name}")
        print("=" * 60)
        
        try:
            test_cases = [
                {
                    "data": {"destination": "Paris"},
                    "expected_missing": []  # destination is the only critical slot
                },
                {
                    "data": {"destination": "Tokyo", "date_range": {"duration_days": 5}},
                    "expected_missing": []  # destination is present
                },
                {
                    "data": {"travelers": {"adults": 2, "kids": 1}, "date_range": {"duration_days": 3}},
                    "expected_missing": ["destination"]  # Missing destination
                },
                {
                    "data": {},
                    "expected_missing": ["destination"]  # Missing destination
                }
            ]
            
            correct_detections = 0
            
            for i, test_case in enumerate(test_cases):
                logger.debug(f"Testing missing slots case {i+1}: {test_case['data']}")
                self.log_test_step(f"Test Case {i+1}", test_case["data"])
                
                missing_slots = self.data_extractor.get_missing_critical_slots(
                    ConversationIntent.ATTRACTIONS,
                    test_case["data"]
                )
                
                logger.debug(f"Missing slots detected: {missing_slots}")
                
                # Check if detection is correct
                expected_missing = set(test_case["expected_missing"])
                actual_missing = set(missing_slots)
                
                if expected_missing == actual_missing:
                    correct_detections += 1
                    print(f"   ✅ Correctly identified missing slots: {missing_slots}")
                    logger.info(f"Correct missing slots detection for case {i+1}")
                else:
                    print(f"   ❌ Incorrect missing slots detection")
                    print(f"      Expected: {expected_missing}")
                    print(f"      Actual: {actual_missing}")
                    logger.error(f"Incorrect missing slots for case {i+1}: expected {expected_missing}, got {actual_missing}")
            
            success_rate = correct_detections / len(test_cases)
            success = success_rate >= 0.8  # 80% accuracy
            
            logger.info(f"Missing slots test completed: {correct_detections}/{len(test_cases)} correct, rate: {success_rate:.2%}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                conversation_data={"success_rate": success_rate, "correct": correct_detections, "total": len(test_cases)},
                detailed_log=f"Success rate: {success_rate:.2%}, Correct: {correct_detections}/{len(test_cases)}"
            )
            
        except Exception as e:
            logger.exception(f"Missing slots test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_state_transitions(self) -> TestResult:
        """Test conversation state transitions for attraction recommendations."""
        test_name = "State Transitions"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n🔄 Testing: {test_name}")
        print("=" * 60)
        
        try:
            # Test valid transitions
            valid_transitions = [
                (ConversationPhase.INTENT_DETECTION, ConversationPhase.DATA_COLLECTION),
                (ConversationPhase.DATA_COLLECTION, ConversationPhase.PROCESSING),
                (ConversationPhase.PROCESSING, ConversationPhase.REFINEMENT),
                (ConversationPhase.REFINEMENT, ConversationPhase.COMPLETED),
                (ConversationPhase.COMPLETED, ConversationPhase.INTENT_DETECTION)
            ]
            
            correct_transitions = 0
            
            for from_phase, to_phase in valid_transitions:
                can_transition = ConversationStateManager.can_transition(from_phase, to_phase)
                if can_transition:
                    correct_transitions += 1
                    print(f"   ✅ {from_phase.value} -> {to_phase.value}: Valid")
                    logger.info(f"Valid transition: {from_phase.value} -> {to_phase.value}")
                else:
                    print(f"   ❌ {from_phase.value} -> {to_phase.value}: Should be valid but rejected")
                    logger.error(f"Invalid transition rejected: {from_phase.value} -> {to_phase.value}")
            
            # Test invalid transitions
            invalid_transitions = [
                (ConversationPhase.INTENT_DETECTION, ConversationPhase.PROCESSING),
                (ConversationPhase.DATA_COLLECTION, ConversationPhase.COMPLETED),
                (ConversationPhase.PROCESSING, ConversationPhase.INTENT_DETECTION)
            ]
            
            for from_phase, to_phase in invalid_transitions:
                can_transition = ConversationStateManager.can_transition(from_phase, to_phase)
                if not can_transition:
                    correct_transitions += 1
                    print(f"   ✅ {from_phase.value} -> {to_phase.value}: Correctly rejected")
                    logger.info(f"Invalid transition correctly rejected: {from_phase.value} -> {to_phase.value}")
                else:
                    print(f"   ❌ {from_phase.value} -> {to_phase.value}: Should be invalid but allowed")
                    logger.error(f"Invalid transition allowed: {from_phase.value} -> {to_phase.value}")
            
            total_tests = len(valid_transitions) + len(invalid_transitions)
            success_rate = correct_transitions / total_tests
            success = success_rate >= 0.9  # 90% accuracy for state transitions
            
            logger.info(f"State transitions test completed: {correct_transitions}/{total_tests} correct, rate: {success_rate:.2%}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                conversation_data={"success_rate": success_rate, "correct": correct_transitions, "total": total_tests},
                detailed_log=f"Success rate: {success_rate:.2%}, Correct: {correct_transitions}/{total_tests}"
            )
            
        except Exception as e:
            logger.exception(f"State transitions test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_question_generation(self) -> TestResult:
        """Test generation of targeted questions for missing data."""
        test_name = "Question Generation"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n❓ Testing: {test_name}")
        print("=" * 60)
        
        try:
            test_cases = [
                {
                    "collected_slots": [],
                    "expected_question_count": 2  # Should ask for destination and other info
                },
                {
                    "collected_slots": ["destination"],
                    "expected_question_count": 1  # Should ask for additional info
                },
                {
                    "collected_slots": ["destination", "date_range"],
                    "expected_question_count": 1  # Should ask for preferences
                },
                {
                    "collected_slots": ["destination", "date_range", "activities_planned"],
                    "expected_question_count": 0  # Has minimum required data
                }
            ]
            
            correct_question_counts = 0
            
            for i, test_case in enumerate(test_cases):
                logger.debug(f"Testing question generation case {i+1}: {test_case['collected_slots']}")
                self.log_test_step(f"Test Case {i+1}", f"Collected slots: {test_case['collected_slots']}")
                
                questions = ConversationStateManager.get_prioritized_questions(
                    ConversationIntent.ATTRACTIONS,
                    test_case["collected_slots"],
                    max_questions=3
                )
                
                actual_count = len(questions)
                expected_count = test_case["expected_question_count"]
                
                print(f"   📝 Generated {actual_count} questions (expected ~{expected_count})")
                logger.info(f"Generated {actual_count} questions for case {i+1}")
                for j, question in enumerate(questions):
                    print(f"      {j+1}. {question}")
                    logger.debug(f"Question {j+1}: {question}")
                
                # Allow some flexibility in question count
                if expected_count == 0:
                    count_correct = actual_count <= 1
                else:
                    count_correct = abs(actual_count - expected_count) <= 1
                
                if count_correct:
                    correct_question_counts += 1
                    print(f"   ✅ Question count appropriate")
                    logger.info(f"Question count appropriate for case {i+1}")
                else:
                    print(f"   ❌ Question count inappropriate")
                    logger.warning(f"Question count inappropriate for case {i+1}")
            
            success_rate = correct_question_counts / len(test_cases)
            success = success_rate >= 0.75  # 75% success rate
            
            logger.info(f"Question generation test completed: {correct_question_counts}/{len(test_cases)} correct, rate: {success_rate:.2%}")
            
            return TestResult(
                test_name=test_name,
                success=success,
                conversation_data={"success_rate": success_rate, "correct": correct_question_counts, "total": len(test_cases)},
                detailed_log=f"Success rate: {success_rate:.2%}, Correct: {correct_question_counts}/{len(test_cases)}"
            )
            
        except Exception as e:
            logger.exception(f"Question generation test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_city_info_integration(self) -> TestResult:
        """Test city info tool integration for attractions context."""
        test_name = "City Info Integration"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n🏙️ Testing: {test_name}")
        print("=" * 60)
        
        try:
            # Create a test conversation
            with get_db_session() as db:
                conversation = create_new_conversation()
                conversation.current_intent = ConversationIntent.ATTRACTIONS
                conversation.current_phase = ConversationPhase.PROCESSING
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                logger.debug(f"Created test conversation: {conversation.id}")
                
                test_destinations = ["Paris", "Tokyo", "London"]
                successful_integrations = 0
                
                for destination in test_destinations:
                    self.log_test_step(f"Testing City Info for {destination}")
                    
                    # Simulate having destination data
                    test_data = {"destination": destination}
                    
                    # Test the attractions tools execution
                    try:
                        tool_results = self.orchestrator._execute_attractions_tools(test_data, None)
                        
                        # Check if city_info tool was called
                        city_info_result = next((r for r in tool_results if r.get("tool_name") == "city_info"), None)
                        
                        if city_info_result:
                            if city_info_result.get("success"):
                                successful_integrations += 1
                                print(f"   ✅ City info successfully retrieved for {destination}")
                                logger.info(f"City info successful for {destination}")
                                
                                # Check data structure
                                data = city_info_result.get("data", {})
                                if data.get("overview") and data.get("highlights"):
                                    print(f"      📊 Data quality: Good (has overview and highlights)")
                                else:
                                    print(f"      ⚠️ Data quality: Partial")
                            else:
                                print(f"   ❌ City info failed for {destination}: {city_info_result.get('error')}")
                                logger.error(f"City info failed for {destination}")
                        else:
                            print(f"   ❌ City info tool not called for {destination}")
                            logger.error(f"City info tool not called for {destination}")
                            
                    except Exception as e:
                        print(f"   ❌ Exception during tool execution: {e}")
                        logger.error(f"Tool execution exception for {destination}: {e}")
                
                # Clean up
                db.delete(conversation)
                db.commit()
                
                success_rate = successful_integrations / len(test_destinations)
                success = success_rate >= 0.7  # 70% success rate
                
                logger.info(f"City info integration test completed: {successful_integrations}/{len(test_destinations)} successful, rate: {success_rate:.2%}")
                
                return TestResult(
                    test_name=test_name,
                    success=success,
                    conversation_data={"success_rate": success_rate, "successful": successful_integrations, "total": len(test_destinations)},
                    detailed_log=f"Success rate: {success_rate:.2%}, Successful: {successful_integrations}/{len(test_destinations)}"
                )
                
        except Exception as e:
            logger.exception(f"City info integration test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    def test_conversation_flow(self) -> TestResult:
        """Test complete attraction recommendation conversation flow."""
        test_name = "Complete Conversation Flow"
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"{'='*60}")
        
        print(f"\n💬 Testing: {test_name}")
        print("=" * 60)
        
        try:
            # Create a test conversation
            with get_db_session() as db:
                conversation = create_new_conversation()
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                logger.debug(f"Created test conversation: {conversation.id}")
                
                responses = []
                
                # Step 1: Initial attraction request
                self.log_test_step("Step 1: Initial attraction request")
                response1 = self.orchestrator.process_user_message(
                    conversation.id,
                    "What are the best attractions in Paris?",
                    db
                )
                responses.append(response1)
                logger.debug(f"Step 1 response: {response1}")
                
                # Should transition to DATA_COLLECTION or PROCESSING (since destination is provided)
                db.refresh(conversation)
                if conversation.current_intent == ConversationIntent.ATTRACTIONS:
                    print("   ✅ Intent correctly set to ATTRACTIONS")
                    logger.info("Intent correctly set to ATTRACTIONS")
                else:
                    print(f"   ❌ Wrong intent: {conversation.current_intent}")
                    logger.error(f"Wrong intent: {conversation.current_intent}")
                
                expected_phases = [ConversationPhase.DATA_COLLECTION, ConversationPhase.PROCESSING]
                if conversation.current_phase in expected_phases:
                    print(f"   ✅ Phase correctly set to {conversation.current_phase}")
                    logger.info(f"Phase correctly set to {conversation.current_phase}")
                else:
                    print(f"   ❌ Wrong phase: {conversation.current_phase}")
                    logger.error(f"Wrong phase: {conversation.current_phase}")
                
                # Step 2: Provide additional preferences (if needed)
                self.log_test_step("Step 2: Provide additional preferences")
                response2 = self.orchestrator.process_user_message(
                    conversation.id,
                    "I'm interested in museums and historical sites, visiting for 3 days.",
                    db
                )
                responses.append(response2)
                logger.debug(f"Step 2 response: {response2}")
                
                # Check final state
                db.refresh(conversation)
                
                success = (
                    conversation.current_intent == ConversationIntent.ATTRACTIONS and
                    conversation.current_phase in [ConversationPhase.PROCESSING, ConversationPhase.REFINEMENT, ConversationPhase.COMPLETED] and
                    len(responses) == 2
                )
                
                logger.info(f"Final conversation state: intent={conversation.current_intent.value}, phase={conversation.current_phase.value}")
                
                # Clean up
                db.delete(conversation)
                db.commit()
                
                return TestResult(
                    test_name=test_name,
                    success=success,
                    conversation_data={
                        "final_intent": conversation.current_intent.value,
                        "final_phase": conversation.current_phase.value,
                        "responses_count": len(responses)
                    },
                    agent_responses=[r.message for r in responses],
                    detailed_log=f"Final phase: {conversation.current_phase.value}, Intent: {conversation.current_intent.value}"
                )
                
        except Exception as e:
            logger.exception(f"Conversation flow test failed with exception: {e}")
            return TestResult(
                test_name=test_name,
                success=False,
                error=str(e)
            )
    
    async def run_all_tests(self):
        """Run all attraction recommendation tests."""
        start_time = datetime.now()
        logger.info("🎯 Starting Attraction Recommendation Test Suite")
        print("🎯 Starting Attraction Recommendation Test Suite")
        print("=" * 80)
        
        # List of all tests
        tests = [
            self.test_intent_detection,
            self.test_data_extraction,
            self.test_missing_slots_detection,
            self.test_state_transitions,
            self.test_question_generation,
            self.test_city_info_integration,
            self.test_conversation_flow
        ]
        
        # Run all tests
        for test_func in tests:
            try:
                result = test_func()
                self.results.append(result)
                logger.info(f"Test {test_func.__name__} completed: {'PASS' if result.success else 'FAIL'}")
            except Exception as e:
                logger.exception(f"Test {test_func.__name__} crashed: {e}")
                self.results.append(TestResult(
                    test_name=test_func.__name__,
                    success=False,
                    error=str(e)
                ))
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Test suite completed in {duration.total_seconds():.2f} seconds")
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("\n\n📊 ATTRACTION RECOMMENDATION TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r.success)
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            if result.error:
                print(f"    Error: {result.error}")
                logger.error(f"Test {result.test_name} error: {result.error}")
            if result.conversation_data:
                print(f"    Data: {result.conversation_data}")
            if result.detailed_log:
                print(f"    Details: {result.detailed_log}")
        
        print(f"\n📈 Overall Results: {passed}/{total} tests passed")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"\n📁 Detailed logs saved to: {test_log_file}")
        
        logger.info(f"FINAL SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All attraction recommendation tests passed!")
            logger.info("🎉 All tests passed!")
        else:
            print(f"\n⚠️ {total-passed} test(s) failed. Check the logs for details.")
            logger.warning(f"⚠️ {total-passed} test(s) failed")


def main():
    """Main test runner."""
    print(f"📁 Test logs will be saved to: logs/")
    
    tester = AttractionRecommendationTester()
    
    # Run synchronously since these are mostly unit tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(tester.run_all_tests())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
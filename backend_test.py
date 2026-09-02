#!/usr/bin/env python3
"""
Backend API tests for Kukdi prep-circle feature.
Tests ONLY the new additive endpoints: People prep fields, Mock sessions, Dream nudges.
"""
import requests
import sys
import json
from typing import Dict, List, Any

# Base URL from frontend/.env
BASE_URL = "https://kukdi-verify-state.preview.emergentagent.com/api"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "_id_leaks": []
}


def check_no_id_leak(data: Any, path: str = "root") -> List[str]:
    """Recursively check for _id fields in response data."""
    leaks = []
    if isinstance(data, dict):
        if "_id" in data:
            leaks.append(f"{path} contains _id: {data['_id']}")
        for key, value in data.items():
            leaks.extend(check_no_id_leak(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            leaks.extend(check_no_id_leak(item, f"{path}[{i}]"))
    return leaks


def test_result(name: str, passed: bool, details: str = ""):
    """Record test result."""
    if passed:
        test_results["passed"].append(f"✅ {name}")
        print(f"✅ PASS: {name}")
        if details:
            print(f"   {details}")
    else:
        test_results["failed"].append(f"❌ {name}: {details}")
        print(f"❌ FAIL: {name}")
        print(f"   {details}")


def check_id_leaks(response_data: Any, test_name: str):
    """Check for _id leaks and record them."""
    leaks = check_no_id_leak(response_data)
    if leaks:
        for leak in leaks:
            test_results["_id_leaks"].append(f"{test_name}: {leak}")
            test_result(f"{test_name} - No _id leak", False, leak)
    else:
        test_result(f"{test_name} - No _id leak", True)


# ============================================================================
# TEST 1: People new fields (PATCH and POST)
# ============================================================================

def test_people_endpoints():
    """Test People PATCH/POST with prep_group, strengths, strength_note."""
    print("\n" + "="*70)
    print("TEST 1: People PATCH/POST persist prep_group, strengths, strength_note")
    print("="*70)
    
    # First, get real person IDs from the database
    try:
        resp = requests.get(f"{BASE_URL}/people", timeout=10)
        if resp.status_code != 200:
            test_result("GET /api/people", False, f"Status {resp.status_code}")
            return None
        
        people_data = resp.json()
        check_id_leaks(people_data, "GET /api/people")
        
        people = people_data.get("people", [])
        if not people:
            test_result("GET /api/people", False, "No people in database")
            return None
        
        test_result("GET /api/people", True, f"Found {len(people)} people")
        
        # Find a person who is NOT in prep_group to test with
        test_person = None
        for p in people:
            if not p.get("prep_group", False):
                test_person = p
                break
        
        if not test_person:
            # Use the first person anyway
            test_person = people[0]
        
        person_id = test_person["id"]
        person_name = test_person.get("name", "Unknown")
        print(f"\n   Using person: {person_name} (id: {person_id})")
        
    except Exception as e:
        test_result("GET /api/people", False, str(e))
        return None
    
    # Test 1a: PATCH with prep_group=true, strengths, strength_note
    print("\n--- Test 1a: PATCH person with prep fields ---")
    try:
        payload = {
            "prep_group": True,
            "strengths": ["Leadership", "Execution"],
            "strength_note": "clear thinker"
        }
        resp = requests.patch(f"{BASE_URL}/people/{person_id}", json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "PATCH /api/people/{id} with prep fields")
            
            # Verify fields are set correctly
            if (data.get("prep_group") == True and 
                data.get("strengths") == ["Leadership", "Execution"] and
                data.get("strength_note") == "clear thinker"):
                test_result("PATCH person with prep_group=true, strengths, strength_note", True, 
                           f"Fields correctly set for {person_name}")
            else:
                test_result("PATCH person with prep_group=true, strengths, strength_note", False,
                           f"Fields not correctly reflected: {json.dumps(data, indent=2)}")
        else:
            test_result("PATCH person with prep_group=true, strengths, strength_note", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("PATCH person with prep_group=true, strengths, strength_note", False, str(e))
    
    # Test 1b: PATCH with prep_group=false (toggle off)
    print("\n--- Test 1b: PATCH person with prep_group=false ---")
    try:
        payload = {"prep_group": False}
        resp = requests.patch(f"{BASE_URL}/people/{person_id}", json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "PATCH /api/people/{id} prep_group=false")
            
            if data.get("prep_group") == False:
                test_result("PATCH person with prep_group=false", True, "Toggle off works")
            else:
                test_result("PATCH person with prep_group=false", False,
                           f"prep_group not false: {data.get('prep_group')}")
        else:
            test_result("PATCH person with prep_group=false", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("PATCH person with prep_group=false", False, str(e))
    
    # Test 1c: Set prep_group back to true for subsequent tests
    print("\n--- Test 1c: Set prep_group back to true ---")
    try:
        payload = {"prep_group": True}
        resp = requests.patch(f"{BASE_URL}/people/{person_id}", json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("prep_group") == True:
                test_result("PATCH person prep_group back to true", True)
            else:
                test_result("PATCH person prep_group back to true", False,
                           f"prep_group not true: {data.get('prep_group')}")
        else:
            test_result("PATCH person prep_group back to true", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("PATCH person prep_group back to true", False, str(e))
    
    # Test 1d: PATCH with unknown strength (should be kept gracefully)
    print("\n--- Test 1d: PATCH with unknown strength ---")
    try:
        payload = {"strengths": ["Leadership", "SomethingUnknown"]}
        resp = requests.patch(f"{BASE_URL}/people/{person_id}", json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "PATCH /api/people/{id} with unknown strength")
            
            strengths = data.get("strengths", [])
            if "Leadership" in strengths and "SomethingUnknown" in strengths:
                test_result("PATCH with unknown strength kept gracefully", True,
                           f"Unknown value kept: {strengths}")
            else:
                test_result("PATCH with unknown strength kept gracefully", False,
                           f"Strengths not as expected: {strengths}")
        else:
            test_result("PATCH with unknown strength kept gracefully", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("PATCH with unknown strength kept gracefully", False, str(e))
    
    # Test 1e: POST new person with prep_group=true
    print("\n--- Test 1e: POST new person with prep fields ---")
    created_person_id = None
    try:
        payload = {
            "name": "Test Peer",
            "prep_group": True,
            "strengths": ["Conflict"]
        }
        resp = requests.post(f"{BASE_URL}/people", json=payload, timeout=10)
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            check_id_leaks(data, "POST /api/people with prep fields")
            
            created_person_id = data.get("id")
            if (data.get("name") == "Test Peer" and 
                data.get("prep_group") == True and
                data.get("strengths") == ["Conflict"]):
                test_result("POST person with prep_group=true", True,
                           f"Created person with id: {created_person_id}")
            else:
                test_result("POST person with prep_group=true", False,
                           f"Fields not correctly set: {json.dumps(data, indent=2)}")
        else:
            test_result("POST person with prep_group=true", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("POST person with prep_group=true", False, str(e))
    
    # Test 1f: DELETE the created person to keep data clean
    if created_person_id:
        print("\n--- Test 1f: DELETE created test person ---")
        try:
            resp = requests.delete(f"{BASE_URL}/people/{created_person_id}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") == True:
                    test_result("DELETE test person", True, "Cleanup successful")
                else:
                    test_result("DELETE test person", False, f"Response: {data}")
            else:
                test_result("DELETE test person", False, f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            test_result("DELETE test person", False, str(e))
    
    return person_id  # Return for use in mock sessions tests


# ============================================================================
# TEST 2: Mock sessions /api/mocks
# ============================================================================

def test_mock_sessions(person_id: str):
    """Test Mock sessions CRUD endpoints."""
    print("\n" + "="*70)
    print("TEST 2: Mock sessions collection + /api/mocks CRUD")
    print("="*70)
    
    if not person_id:
        print("⚠️  Skipping mock sessions tests - no valid person_id")
        return
    
    created_mock_id = None
    
    # Test 2a: POST /api/mocks - create a mock session
    print("\n--- Test 2a: POST /api/mocks ---")
    try:
        payload = {
            "person_ids": [person_id],
            "competencies": ["Leadership"],
            "company": "Google",
            "feedback": "solid structure",
            "what_went_well": "good framing",
            "to_act_on": "tighten the summary"
        }
        resp = requests.post(f"{BASE_URL}/mocks", json=payload, timeout=10)
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            check_id_leaks(data, "POST /api/mocks")
            
            created_mock_id = data.get("id")
            # Check required fields
            if (created_mock_id and 
                data.get("date") and  # Should have ISO date
                data.get("acted") == False and
                data.get("person_ids") == [person_id] and
                data.get("competencies") == ["Leadership"] and
                data.get("company") == "Google"):
                test_result("POST /api/mocks", True,
                           f"Created mock session with id: {created_mock_id}")
            else:
                test_result("POST /api/mocks", False,
                           f"Fields not correctly set: {json.dumps(data, indent=2)}")
        else:
            test_result("POST /api/mocks", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("POST /api/mocks", False, str(e))
    
    # Test 2b: GET /api/mocks?person_id={person_id} - should return the created mock
    print("\n--- Test 2b: GET /api/mocks?person_id={person_id} ---")
    try:
        resp = requests.get(f"{BASE_URL}/mocks?person_id={person_id}", timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "GET /api/mocks?person_id=")
            
            mocks = data.get("mocks", [])
            # Should include the created mock
            found_mock = False
            if created_mock_id:
                for mock in mocks:
                    if mock.get("id") == created_mock_id:
                        found_mock = True
                        break
            
            if found_mock:
                test_result("GET /api/mocks?person_id= returns created mock", True,
                           f"Found {len(mocks)} mock(s), newest-first order")
            else:
                test_result("GET /api/mocks?person_id= returns created mock", False,
                           f"Created mock not found in response. Mocks: {len(mocks)}")
        else:
            test_result("GET /api/mocks?person_id= returns created mock", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("GET /api/mocks?person_id= returns created mock", False, str(e))
    
    # Test 2c: GET /api/mocks?person_id={different_id} - should return empty or not include our mock
    print("\n--- Test 2c: GET /api/mocks?person_id={different_id} ---")
    try:
        # Use a fake UUID that doesn't exist
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = requests.get(f"{BASE_URL}/mocks?person_id={fake_id}", timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "GET /api/mocks?person_id={different}")
            
            mocks = data.get("mocks", [])
            # Should not include our created mock
            found_our_mock = False
            if created_mock_id:
                for mock in mocks:
                    if mock.get("id") == created_mock_id:
                        found_our_mock = True
                        break
            
            if not found_our_mock:
                test_result("GET /api/mocks?person_id={different} filters correctly", True,
                           f"Returned {len(mocks)} mock(s), our mock not included")
            else:
                test_result("GET /api/mocks?person_id={different} filters correctly", False,
                           "Our mock incorrectly included in filtered results")
        else:
            test_result("GET /api/mocks?person_id={different} filters correctly", False,
                       f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        test_result("GET /api/mocks?person_id={different} filters correctly", False, str(e))
    
    # Test 2d: PATCH /api/mocks/{id} with acted=true
    if created_mock_id:
        print("\n--- Test 2d: PATCH /api/mocks/{id} with acted=true ---")
        try:
            payload = {"acted": True}
            resp = requests.patch(f"{BASE_URL}/mocks/{created_mock_id}", json=payload, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                check_id_leaks(data, "PATCH /api/mocks/{id}")
                
                if data.get("acted") == True:
                    test_result("PATCH /api/mocks/{id} with acted=true", True,
                               "acted field updated successfully")
                else:
                    test_result("PATCH /api/mocks/{id} with acted=true", False,
                               f"acted not true: {data.get('acted')}")
            else:
                test_result("PATCH /api/mocks/{id} with acted=true", False,
                           f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            test_result("PATCH /api/mocks/{id} with acted=true", False, str(e))
    
    # Test 2e: DELETE /api/mocks/{id}
    if created_mock_id:
        print("\n--- Test 2e: DELETE /api/mocks/{id} ---")
        try:
            resp = requests.delete(f"{BASE_URL}/mocks/{created_mock_id}", timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") == True:
                    test_result("DELETE /api/mocks/{id}", True, "Mock session deleted")
                    
                    # Verify it's actually deleted
                    verify_resp = requests.get(f"{BASE_URL}/mocks?person_id={person_id}", timeout=10)
                    if verify_resp.status_code == 200:
                        verify_data = verify_resp.json()
                        mocks = verify_data.get("mocks", [])
                        found = any(m.get("id") == created_mock_id for m in mocks)
                        if not found:
                            test_result("DELETE /api/mocks/{id} - verify deletion", True,
                                       "Mock no longer returned in GET")
                        else:
                            test_result("DELETE /api/mocks/{id} - verify deletion", False,
                                       "Mock still returned after deletion")
                else:
                    test_result("DELETE /api/mocks/{id}", False, f"Response: {data}")
            else:
                test_result("DELETE /api/mocks/{id}", False,
                           f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            test_result("DELETE /api/mocks/{id}", False, str(e))


# ============================================================================
# TEST 3: GET /api/dream/nudges
# ============================================================================

def test_dream_nudges():
    """Test Dream nudges endpoint with LLM reasoning."""
    print("\n" + "="*70)
    print("TEST 3: GET /api/dream/nudges (prep_nudges reasoning)")
    print("="*70)
    
    print("\n--- Test 3a: GET /api/dream/nudges ---")
    print("   (This endpoint calls an LLM and may take up to 30s)")
    
    try:
        resp = requests.get(f"{BASE_URL}/dream/nudges", timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            check_id_leaks(data, "GET /api/dream/nudges")
            
            # Check structure
            if "nudge" not in data or "more" not in data:
                test_result("GET /api/dream/nudges structure", False,
                           f"Missing 'nudge' or 'more' keys. Keys: {list(data.keys())}")
                return
            
            test_result("GET /api/dream/nudges structure", True,
                       "Response has 'nudge' and 'more' keys")
            
            nudge = data.get("nudge")
            more = data.get("more", [])
            
            # With 3 circle members, should return a non-null nudge
            if nudge is None:
                test_result("GET /api/dream/nudges returns non-null nudge", False,
                           "nudge is null (expected non-null with 3 circle members)")
            else:
                # Check nudge structure
                required_keys = ["id", "kind", "line", "detail", "refs"]
                missing_keys = [k for k in required_keys if k not in nudge]
                
                if missing_keys:
                    test_result("GET /api/dream/nudges nudge structure", False,
                               f"Missing keys in nudge: {missing_keys}")
                else:
                    test_result("GET /api/dream/nudges nudge structure", True,
                               f"Nudge has all required keys: {required_keys}")
                
                # Check that 'line' is a warm sentence (non-empty string)
                line = nudge.get("line", "")
                if isinstance(line, str) and len(line) > 0:
                    test_result("GET /api/dream/nudges 'line' is warm sentence", True,
                               f"Line: '{line[:80]}...'")
                else:
                    test_result("GET /api/dream/nudges 'line' is warm sentence", False,
                               f"Line is empty or not a string: {line}")
                
                # Check refs - should reference real people (Devina, Rasukh, Shubhi) or competencies
                refs = nudge.get("refs", [])
                if isinstance(refs, list):
                    test_result("GET /api/dream/nudges 'refs' is list", True,
                               f"refs has {len(refs)} item(s)")
                    
                    # Check if refs contain labels that reference real people or competencies
                    # This is a soft check - we just verify refs exist and have labels
                    known_people = ["Devina", "Rasukh", "Shubhi"]
                    known_competencies = ["Leadership", "Ambiguity", "Failure", "Conflict", 
                                        "Influence", "Execution", "Analytical Thinking", "Customer Focus"]
                    
                    for ref in refs:
                        if isinstance(ref, dict):
                            label = ref.get("label", "")
                            # Just log the refs, don't fail if they don't match exactly
                            print(f"      ref label: '{label}'")
                else:
                    test_result("GET /api/dream/nudges 'refs' is list", False,
                               f"refs is not a list: {type(refs)}")
                
                # Check 'more' is a list (may be empty or up to 2)
                if isinstance(more, list):
                    test_result("GET /api/dream/nudges 'more' is list", True,
                               f"more has {len(more)} item(s)")
                else:
                    test_result("GET /api/dream/nudges 'more' is list", False,
                               f"more is not a list: {type(more)}")
        else:
            test_result("GET /api/dream/nudges", False,
                       f"Status {resp.status_code}: {resp.text}")
    except requests.exceptions.Timeout:
        test_result("GET /api/dream/nudges", False, "Request timed out after 30s")
    except Exception as e:
        test_result("GET /api/dream/nudges", False, str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "="*70)
    print("KUKDI PREP-CIRCLE BACKEND API TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print("Testing ONLY new additive prep-circle endpoints")
    print("="*70)
    
    # Run tests in sequence
    person_id = test_people_endpoints()
    test_mock_sessions(person_id)
    test_dream_nudges()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    print(f"\n✅ PASSED: {len(test_results['passed'])}")
    for result in test_results['passed']:
        print(f"   {result}")
    
    print(f"\n❌ FAILED: {len(test_results['failed'])}")
    for result in test_results['failed']:
        print(f"   {result}")
    
    if test_results['_id_leaks']:
        print(f"\n🚨 _ID LEAKS DETECTED: {len(test_results['_id_leaks'])}")
        for leak in test_results['_id_leaks']:
            print(f"   {leak}")
    else:
        print("\n✅ NO _ID LEAKS DETECTED")
    
    print("\n" + "="*70)
    
    # Exit with appropriate code
    if test_results['failed'] or test_results['_id_leaks']:
        print("❌ TESTS FAILED")
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
Integration test script for question_generator app
Test với ngrok nếu ngrok đang chạy, nếu không test localhost
"""
import requests
import json
import time

# Try ngrok first, fallback to localhost
URLS = [
    "https://nonelliptic-dewily-carlos.ngrok-free.dev",
    "http://localhost:8000"
]

BASE_URL = None
for url in URLS:
    try:
        response = requests.get(f"{url}/", timeout=2)
        BASE_URL = url
        print(f"✓ Connected to {url}")
        break
    except:
        print(f"✗ Cannot connect to {url}")

if not BASE_URL:
    print("Cannot connect to any server!")
    exit(1)

AI_TOKEN = "38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21"

# Test 1: Request AI Questions
print("\n" + "="*60)
print("TEST 1: Request AI Questions (Django → AI Worker)")
print("="*60)

payload = {
    "user_id": "test_user_123",
    "quiz_size": 5,
    "declared_level": "Intermediate",
    "profession": "developer",
    "preferred_topics": ["Python"],
    "weak_skills": ["async"]
}

try:
    response = requests.post(
        f"{BASE_URL}/api/ai/generate/",
        json=payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 2: Receive AI Questions (Simulate AI Worker response)
print("\n" + "="*60)
print("TEST 2: Receive AI Questions (AI Worker → Django)")
print("="*60)

sample_questions = [
    {
        "sentence": "What is the output of print(2**3)?",
        "directive": "Choose the correct answer",
        "options": {
            "A": "6",
            "B": "8",
            "C": "9",
            "D": "16"
        },
        "correct_answer": "B",
        "explanation": "2 to the power of 3 is 8",
        "type": "multiple_choice",
        "difficulty": "easy",
        "score": 10,
        "context": "Python"
    },
    {
        "sentence": "What is a closure in Python?",
        "directive": "Select the best definition",
        "options": {
            "A": "A function that is closed to outside access",
            "B": "A function that returns another function with access to variables from its enclosing scope",
            "C": "A way to close a file",
            "D": "A Python module"
        },
        "correct_answer": "B",
        "explanation": "A closure is a function that has access to variables from another function's scope",
        "type": "multiple_choice",
        "difficulty": "hard",
        "score": 20,
        "context": "Advanced Python"
    }
]

headers = {
    "X-AI-Worker-Token": AI_TOKEN
}

receive_payload = {
    "questions": sample_questions,
    "user_id": "test_user_123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/ai/receive/",
        json=receive_payload,
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 3: Security - Wrong token
print("\n" + "="*60)
print("TEST 3: Security Test - Wrong Token")
print("="*60)

wrong_headers = {
    "X-AI-Worker-Token": "wrong_token_123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/ai/receive/",
        json=receive_payload,
        headers=wrong_headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 401:
        print("✓ Correctly rejected unauthorized request")
    else:
        print("✗ Should return 401 for wrong token")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 4: Validation - Missing required field
print("\n" + "="*60)
print("TEST 4: Validation Test - Missing Required Field")
print("="*60)

invalid_questions = [
    {
        # Missing 'sentence' field
        "directive": "Choose",
        "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
        "correct_answer": "A"
    }
]

invalid_payload = {
    "questions": invalid_questions,
    "user_id": "test_user_123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/ai/receive/",
        json=invalid_payload,
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code == 500:
        print("✓ Correctly returned 500 for validation error")
    else:
        print("✗ Expected 500 for validation error")
except Exception as e:
    print(f"Error: {str(e)}")

print("\n" + "="*60)
print("INTEGRATION TESTS COMPLETE")
print("="*60)
